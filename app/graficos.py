"""Gráficos Plotly do dashboard, todos na paleta do Boto Café.

Cada função recebe dados já filtrados e devolve uma `go.Figure`.
"""
import pandas as pd
import plotly.graph_objects as go

from src.rfm import ORDEM_SEGMENTOS

CAFE, ROSA, VERDE, CREME, OURO = "#3E2723", "#E8A0B4", "#2E5E4E", "#F5EDE0", "#C8963E"

# Uma cor por segmento: verdes/dourado = saudáveis, rosas = atenção, marrons = esfriando.
COR_SEGMENTO = {
    "Campeões": OURO, "Clientes Fiéis": VERDE, "Potenciais Fiéis": "#5E9C84",
    "Novos": "#9FCBB8", "Promissores": "#F2D3DC", "Precisam de Atenção": "#E8C27A",
    "Prestes a Dar Churn": ROSA, "Hibernando": "#8D6E63", "Perdidos": "#BCAAA4",
}


def _layout(fig: go.Figure, titulo: str, altura: int = 340) -> go.Figure:
    """Estilo comum: fundo transparente, fonte da marca, margens enxutas."""
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=CAFE), x=0),
        height=altura, margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CAFE), legend=dict(orientation="h", y=-0.2),
    )
    return fig


def receita_mensal(it: pd.DataFrame) -> go.Figure:
    """Barras de receita por mês."""
    m = it.groupby(it["data_pedido"].dt.to_period("M").astype(str))["receita"].sum()
    fig = go.Figure(go.Bar(x=m.index, y=m.values, marker_color=CAFE,
                           hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>"))
    fig.update_yaxes(tickprefix="R$ ", gridcolor="#E9DFD0")
    return _layout(fig, "Receita por mês")


def distribuicao_segmentos(cli: pd.DataFrame) -> go.Figure:
    """Nº de clientes por segmento (barras horizontais, melhor segmento no topo)."""
    c = cli["segmento"].value_counts().reindex(ORDEM_SEGMENTOS).dropna()
    fig = go.Figure(go.Bar(
        y=c.index, x=c.values, orientation="h",
        marker_color=[COR_SEGMENTO[s] for s in c.index], text=c.values.astype(int),
        textposition="outside", hovertemplate="%{y}: %{x} clientes<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(visible=False)
    return _layout(fig, "Clientes por segmento")


def receita_por_segmento(cli: pd.DataFrame, it: pd.DataFrame) -> go.Figure:
    """Participação de cada segmento na receita do período."""
    seg = cli["segmento"].astype(str)
    r = it.assign(segmento=it["cliente_id"].map(seg)).groupby("segmento")["receita"].sum()
    r = (r / r.sum() * 100).reindex(ORDEM_SEGMENTOS).dropna()
    fig = go.Figure(go.Bar(
        y=r.index, x=r.values, orientation="h",
        marker_color=[COR_SEGMENTO[s] for s in r.index],
        text=[f"{v:.1f}%" for v in r.values], textposition="outside",
        hovertemplate="%{y}: %{x:.1f}% da receita<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(visible=False)
    return _layout(fig, "% da receita por segmento")


def heatmap_rf(cli: pd.DataFrame) -> go.Figure:
    """Mapa R × F: cor = nº de clientes; o hover mostra o gasto médio da célula."""
    cont = cli.pivot_table(index="R", columns="F", values="monetario", aggfunc="size",
                           fill_value=0).reindex(index=range(5, 0, -1), columns=range(1, 6), fill_value=0)
    medio = cli.pivot_table(index="R", columns="F", values="monetario", aggfunc="mean"
                            ).reindex(index=range(5, 0, -1), columns=range(1, 6))
    fig = go.Figure(go.Heatmap(
        z=cont.values, x=[f"F{c}" for c in cont.columns], y=[f"R{r}" for r in cont.index],
        text=cont.values, texttemplate="%{text}", customdata=medio.values,
        colorscale=[[0, CREME], [1, VERDE]], colorbar=dict(title="Clientes"),
        hovertemplate="%{y} · %{x}<br>%{z} clientes<br>gasto médio R$ %{customdata:,.0f}<extra></extra>"))
    fig.update_xaxes(title="Frequência (5 = compra mais vezes)")
    fig.update_yaxes(title="Recência (5 = comprou há pouco)")
    return _layout(fig, "Mapa RFM: recência × frequência", altura=380)


def ranking_vip(topo: pd.DataFrame) -> go.Figure:
    """Barras horizontais com os maiores clientes (`topo` já ordenado, maior primeiro)."""
    fig = go.Figure(go.Bar(
        y=topo["nome"], x=topo["receita"], orientation="h",
        marker_color=[COR_SEGMENTO[str(s)] for s in topo["segmento"]],
        hovertemplate="%{y}<br>R$ %{x:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickprefix="R$ ", gridcolor="#E9DFD0")
    return _layout(fig, "Maiores clientes no período", altura=max(300, 24 * len(topo) + 80))


def lucro_por_segmento(sim: pd.DataFrame) -> go.Figure:
    """Custo × margem incremental por segmento, vindo do simulador de cupons."""
    fig = go.Figure([
        go.Bar(name="Custo da ação", x=sim.index, y=sim["custo_total"], marker_color=ROSA),
        go.Bar(name="Margem incremental", x=sim.index, y=sim["margem_incremental"], marker_color=VERDE),
    ])
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickprefix="R$ ", gridcolor="#E9DFD0")
    return _layout(fig, "Custo × retorno por segmento", altura=360)
