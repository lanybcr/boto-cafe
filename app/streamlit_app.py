"""Dashboard Boto Café — rode com:  streamlit run app/streamlit_app.py"""
import sys
from dataclasses import replace
from pathlib import Path

# Permite importar `src` e `app` rodando a partir de qualquer pasta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from app import dados as D, graficos as G
from src import cupons as C
from src.rfm import ORDEM_SEGMENTOS, REGRAS_SEGMENTOS

st.set_page_config(page_title="Boto Café · RFM", page_icon="☕", layout="wide")

# Estilo: cartões de KPI e títulos na paleta da marca
st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
div[data-testid="stMetric"] {background:#F5EDE0; border-left:5px solid #C8963E;
    padding:14px 18px; border-radius:10px;}
div[data-testid="stMetricLabel"] p {color:#6D4C41; font-weight:600;}
div[data-testid="stMetricValue"] {font-size:1.7rem;}
h1, h2, h3 {color:#3E2723;}
.stTabs [data-baseweb="tab"] {font-weight:600;}
</style>
""", unsafe_allow_html=True)

d = D.carregar()
brl = lambda v: f"R$ {v:,.0f}".replace(",", ".")

# ───────────── Filtros (barra lateral) ─────────────
with st.sidebar:
    st.markdown("## ☕ Boto Café")
    st.caption("Dados fictícios · análise RFM")
    dmin, dmax = d.itens["data_pedido"].min().date(), d.itens["data_pedido"].max().date()
    periodo = st.date_input("Período", (dmin, dmax), min_value=dmin, max_value=dmax)
    # Filtro vazio = "todos" (evita uma barra lateral lotada de etiquetas)
    todos_estados = sorted(d.rfm["estado"].unique())
    estados = st.multiselect("Estado", todos_estados, placeholder="Todos") or todos_estados
    segmentos = st.multiselect("Segmento", ORDEM_SEGMENTOS, placeholder="Todos") or ORDEM_SEGMENTOS
    todas_cat = sorted(d.itens["categoria"].unique())
    categorias = st.multiselect("Categoria", todas_cat, placeholder="Todas") or todas_cat
    st.divider()
    st.caption("Deixe um filtro vazio para incluir tudo. O segmento RFM é calculado sobre todo o "
               "histórico; o período e a categoria filtram receita, pedidos e ticket.")

if len(periodo) != 2:  # o usuário ainda está escolhendo a data final
    st.info("Escolha a data inicial e a final do período.")
    st.stop()

cli, it = D.filtrar(d, periodo, estados, segmentos, categorias)
if cli.empty:
    st.warning("Nenhum cliente com esses filtros. Amplie o período ou a seleção na barra lateral.")
    st.stop()

# ───────────── Cabeçalho + KPIs ─────────────
st.title("Boto Café · Clientes e campanhas")
k = D.indicadores(cli, it)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Receita", brl(k["receita"]))
c2.metric("Clientes", f"{k['clientes']:,}".replace(",", "."))
c3.metric("Ticket médio", f"R$ {k['ticket']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c4.metric("Clientes em risco", f"{k['pct_risco']:.1%}",
          help="Share de clientes nos segmentos: " + ", ".join(D.SEGMENTOS_EM_RISCO))

tab_geral, tab_rfm, tab_vip, tab_risco, tab_sim = st.tabs(
    ["Visão geral", "Mapa RFM", "Clientes VIP", "Em risco", "Simulador de cupons"])

# ───────────── Visão geral ─────────────
with tab_geral:
    st.plotly_chart(G.receita_mensal(it), width="stretch")
    a, b = st.columns(2)
    a.plotly_chart(G.distribuicao_segmentos(cli), width="stretch")
    b.plotly_chart(G.receita_por_segmento(cli, it), width="stretch")

# ───────────── Mapa RFM ─────────────
with tab_rfm:
    a, b = st.columns([3, 2])
    a.plotly_chart(G.heatmap_rf(cli), width="stretch")
    with b:
        st.markdown("**Como ler:** quanto mais verde, mais clientes na célula. "
                    "Canto de cima à direita = compra muito e recentemente; "
                    "embaixo à esquerda = comprava pouco e sumiu.")
        with st.expander("Regras dos segmentos"):
            st.dataframe(REGRAS_SEGMENTOS.set_index("segmento"), width="stretch")

# ───────────── VIPs ─────────────
with tab_vip:
    n = st.slider("Quantos clientes mostrar", 5, 50, 15)
    rec = it.groupby("cliente_id")["receita"].sum().rename("receita")
    vip = (cli.join(rec).sort_values("receita", ascending=False).head(n)
           .reset_index()[["cliente_id", "nome", "estado", "segmento", "frequencia", "recencia", "receita"]])
    a, b = st.columns([2, 3])
    a.plotly_chart(G.ranking_vip(vip), width="stretch")
    b.dataframe(
        vip.rename(columns={"cliente_id": "id", "frequencia": "pedidos (total)", "recencia": "dias sem comprar"}),
        hide_index=True, width="stretch",
        column_config={"receita": st.column_config.NumberColumn("receita no período", format="R$ %.0f")})

# ───────────── Em risco ─────────────
with tab_risco:
    risco = cli[cli["segmento"].isin(D.SEGMENTOS_EM_RISCO)].copy()
    risco["cupom_sugerido"] = risco["segmento"].astype(str).map(lambda s: C.PREMISSAS[s].cupom)
    risco = (risco.reset_index().sort_values("monetario", ascending=False)
             [["cliente_id", "nome", "email", "estado", "segmento", "recencia", "frequencia",
               "monetario", "cupom_sugerido"]]
             .rename(columns={"cliente_id": "cliente", "recencia": "dias_sem_comprar",
                              "frequencia": "pedidos", "monetario": "gasto_total"}))
    st.markdown(f"**{len(risco)} clientes em risco** · {brl(risco['gasto_total'].sum())} já gastos por eles. "
                "Ordenados por valor: comece pelos de cima.")
    st.dataframe(risco, hide_index=True, width="stretch",
                 column_config={"gasto_total": st.column_config.NumberColumn(format="R$ %.0f")})
    st.download_button("Baixar CSV (abre com acentos no Excel)",
                       risco.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                       "clientes_em_risco.csv", "text/csv")

# ───────────── Simulador de cupons ─────────────
with tab_sim:
    st.markdown("Mude as hipóteses e veja se a ação compensa. "
                "Lucro = pedidos × ticket × (**incremental** × margem − desconto) − brindes − contato.")
    with st.expander("Premissas globais", expanded=False):
        g1, g2 = st.columns(2)
        margem = g1.slider("Margem bruta", 0.10, 0.80, float(round(d.margem, 3)), 0.01, format="%.2f",
                           help="Padrão: margem real calculada do custo dos produtos.")
        contato = g2.slider("Custo por contato (R$)", 0.0, 2.0, C.CUSTO_CONTATO, 0.05)

    segs_disp = [s for s in ORDEM_SEGMENTOS if s in set(cli["segmento"].astype(str))]
    seg = st.selectbox("Segmento a ajustar", segs_disp,
                       index=segs_disp.index("Prestes a Dar Churn") if "Prestes a Dar Churn" in segs_disp else 0)
    p0 = C.PREMISSAS[seg]
    st.caption(f"{p0.acao} · cupom `{p0.cupom}`")
    s1, s2, s3, s4 = st.columns(4)
    desc = s1.slider("Desconto", 0.0, 0.40, p0.desconto, 0.01, format="%.2f", key=f"d_{seg}")
    resp = s2.slider("Taxa de resposta", 0.0, 1.0, p0.taxa_resposta, 0.01, format="%.2f", key=f"r_{seg}")
    inc = s3.slider("% incremental", 0.0, 1.0, p0.incremental, 0.01, format="%.2f", key=f"i_{seg}",
                    help="Fatia dos pedidos que só acontecem por causa do cupom.")
    brinde = s4.slider("Brinde (R$/resposta)", 0.0, 30.0, p0.brinde_custo, 1.0, key=f"b_{seg}")

    prem = {**C.PREMISSAS, seg: replace(p0, desconto=desc, taxa_resposta=resp, incremental=inc,
                                        brinde_custo=brinde)}
    sim = C.simular(cli, margem, prem, contato)
    r = sim.loc[seg]
    equilibrio = inc * margem

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Lucro do segmento", brl(r["lucro_liquido"]))
    m2.metric("ROI", f"{r['roi']:.2f}" if pd.notna(r["roi"]) else "—",
              help="Lucro líquido por R$ 1 investido na ação.")
    m3.metric("Clientes que respondem", f"{r['respondem']:.0f}")
    m4.metric("Lucro da campanha toda", brl(sim["lucro_liquido"].sum()))
    if desc > equilibrio:
        st.error(f"Desconto de {desc:.0%} acima do ponto de equilíbrio ({equilibrio:.0%} = incremental × margem): "
                 "cada pedido com cupom dá prejuízo.")
    else:
        st.success(f"Desconto abaixo do ponto de equilíbrio ({equilibrio:.0%}): folga de {equilibrio - desc:.0%}.")
    st.plotly_chart(G.lucro_por_segmento(sim), width="stretch")
    st.caption("Hipóteses, não medições: troque por resultados de teste A/B. A simulação cobre uma campanha só, "
               "e os dados são fictícios.")
