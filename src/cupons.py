"""Estratégia de cupons do Boto Café: ação por segmento, simulação custo × retorno
e exportação das listas de campanha.

Todas as premissas ficam em `PREMISSAS` (um dicionário editável). A lógica de
cálculo não tem número "escondido": mude a premissa e rode de novo.

A conta central, por segmento, é:

    lucro líquido = pedidos_resgatados × ticket × (incremental × margem − desconto)
                    − brindes − custo de contato

- `incremental`: fatia dos pedidos que SÓ aconteceram por causa da ação. Quem
  já compraria de qualquer jeito (ex.: Campeões) leva o desconto "de graça",
  e isso é custo puro (canibalização).
- `margem`: margem bruta real, calculada do custo dos produtos.
"""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import config as cfg
from .rfm import ORDEM_SEGMENTOS

DIR_CAMPANHAS = cfg.DIR_DADOS / "campanhas"

# Custo de acionar um cliente (e-mail/WhatsApp), em R$ por contato. Hipótese.
CUSTO_CONTATO = 0.30


@dataclass(frozen=True)
class Premissa:
    """Ação e hipóteses de um segmento (tudo editável)."""
    acao: str                    # o que fazer, em uma frase
    cupom: str                   # código sugerido ('—' quando não há cupom)
    desconto: float              # % de desconto do cupom (0.20 = 20%)
    brinde_custo: float          # custo (R$) do brinde por cliente que responde
    taxa_resposta: float         # % dos contatados que compram por causa da ação
    pedidos_por_resposta: float  # pedidos feitos por quem responde
    incremental: float           # % desses pedidos que NÃO ocorreriam sem a ação
    objetivo: str                # por que esta ação para este grupo


# Códigos novos de propósito: não reutilizam os cupons históricos da loja.
PREMISSAS: dict[str, Premissa] = {
    "Campeões": Premissa(
        "Recompensa sem desconto: brinde exclusivo + acesso antecipado a lançamentos",
        "—", 0.0, 12.0, 0.60, 1.0, 0.15,
        "Proteger quem sustenta a receita sem ensiná-los a esperar desconto."),
    "Clientes Fiéis": Premissa(
        "Cupom leve de agradecimento na próxima compra",
        "FIEL5", 0.05, 0.0, 0.35, 1.0, 0.25,
        "Manter o hábito; boa parte compraria de qualquer forma, então desconto baixo."),
    "Potenciais Fiéis": Premissa(
        "Cupom para a 3ª/4ª compra, acelerando o hábito",
        "VOLTA10", 0.10, 0.0, 0.30, 1.0, 0.50,
        "Estão a um passo de virar fiéis: vale empurrar."),
    "Novos": Premissa(
        "Cupom de segunda compra, enviado ~15 dias após a primeira",
        "SEGUNDA10", 0.10, 0.0, 0.25, 1.0, 0.60,
        "A 2ª compra é o grande divisor entre cliente e curioso."),
    "Promissores": Premissa(
        "Cupom de reativação leve com sugestão de produto",
        "PROMESSA10", 0.10, 0.0, 0.20, 1.0, 0.60,
        "Compraram pouco e há pouco tempo: ainda dá para engajar."),
    "Precisam de Atenção": Premissa(
        "Lembrete personalizado com cupom moderado",
        "ATENCAO10", 0.10, 0.0, 0.20, 1.0, 0.60,
        "Meio-termo que pode escorregar para o churn se ninguém olhar."),
    "Prestes a Dar Churn": Premissa(
        "Campanha 'saudade': cupom forte, contato pessoal (WhatsApp) para os de maior valor",
        "SAUDADE20", 0.20, 0.0, 0.20, 1.5, 0.85,
        "Já foram bons clientes e concentram o maior valor em risco."),
    "Hibernando": Premissa(
        "Cupom de retorno com prazo curto",
        "SAUDADE15", 0.15, 0.0, 0.10, 1.2, 0.90,
        "Sumindo, mas com histórico: tentativa de custo controlado."),
    "Perdidos": Premissa(
        "Último chamado por e-mail (custo baixo); sem investimento em desconto alto",
        "ULTIMO15", 0.15, 0.0, 0.03, 1.0, 0.95,
        "Chance baixa: testar barato e, se não responderem, tirar da lista."),
}


def calcular_margem(base: dict) -> float:
    """Margem bruta global = (receita a preço de lista − custo) / receita a preço de lista,
    usando só itens de pedidos válidos. O custo vem da tabela de produtos."""
    validos = base["pedidos"].loc[base["pedidos"]["valido"], "id"]
    it = base["itens_pedido"][base["itens_pedido"]["pedido_id"].isin(validos)]
    it = it.merge(base["produtos"][["id", "custo"]], left_on="produto_id", right_on="id")
    receita = (it["quantidade"] * it["preco_unitario"]).sum()
    custo = (it["quantidade"] * it["custo"]).sum()
    return float((receita - custo) / receita)


def simular(rfm: pd.DataFrame, margem: float,
            premissas: dict[str, Premissa] | None = None,
            custo_contato: float = CUSTO_CONTATO) -> pd.DataFrame:
    """Simula custo × retorno por segmento. Devolve uma linha por segmento."""
    premissas = premissas or PREMISSAS
    base = rfm.groupby("segmento", observed=True).agg(
        clientes=("monetario", "size"), ticket=("ticket_medio", "mean"))
    linhas = []
    for seg in [s for s in ORDEM_SEGMENTOS if s in base.index]:
        p, n, t = premissas[seg], base.at[seg, "clientes"], base.at[seg, "ticket"]
        respondem = n * p.taxa_resposta
        pedidos = respondem * p.pedidos_por_resposta
        # Custos: desconto vale para TODOS os pedidos com cupom (incl. não incrementais)
        c_desc = pedidos * t * p.desconto
        c_brinde = respondem * p.brinde_custo
        c_contato = n * custo_contato
        custo = c_desc + c_brinde + c_contato
        margem_inc = pedidos * p.incremental * t * margem
        linhas.append({
            "segmento": seg, "clientes": n, "ticket": t, "cupom": p.cupom,
            "desconto": p.desconto, "respondem": respondem,
            "receita_incremental": pedidos * p.incremental * t * (1 - p.desconto),
            "custo_desconto": c_desc, "custo_brinde": c_brinde, "custo_contato": c_contato,
            "custo_total": custo, "margem_incremental": margem_inc,
            "lucro_liquido": margem_inc - custo,
            "roi": (margem_inc - custo) / custo if custo else float("nan"),
        })
    return pd.DataFrame(linhas).set_index("segmento")


def desconto_ponto_equilibrio(p: Premissa, margem: float) -> float:
    """Desconto máximo que ainda não dá prejuízo na ação (ignorando contato/brinde):
    incremental × margem = desconto."""
    return p.incremental * margem


def _motivo(linha: pd.Series, p: Premissa) -> str:
    """Texto curto e personalizado explicando por que o cliente está na lista."""
    return (f"{linha['segmento']}: {int(linha['frequencia'])} pedido(s), "
            f"R$ {linha['monetario']:,.0f} gastos, última compra há {int(linha['recencia'])} dias. "
            f"{p.objetivo}")


def montar_campanha(rfm: pd.DataFrame, premissas: dict[str, Premissa] | None = None) -> pd.DataFrame:
    """Lista final de contato: uma linha por cliente, ordenada por prioridade de valor."""
    premissas = premissas or PREMISSAS
    df = rfm.reset_index()
    df["cupom_sugerido"] = df["segmento"].astype(str).map(lambda s: premissas[s].cupom)
    df["desconto_pct"] = df["segmento"].astype(str).map(lambda s: round(premissas[s].desconto * 100))
    df["acao"] = df["segmento"].astype(str).map(lambda s: premissas[s].acao)
    df["motivo"] = [_motivo(l, premissas[str(l["segmento"])]) for _, l in df.iterrows()]
    df["monetario"] = df["monetario"].round(2)
    cols = ["cliente_id", "nome", "email", "estado", "segmento", "cupom_sugerido",
            "desconto_pct", "acao", "motivo", "recencia", "frequencia", "monetario"]
    return (df[cols].rename(columns={"cliente_id": "cliente", "recencia": "dias_sem_comprar",
                                     "frequencia": "pedidos", "monetario": "gasto_total"})
            .sort_values(["segmento", "gasto_total"], ascending=[True, False]))


def exportar_campanhas(camp: pd.DataFrame, pasta: Path = DIR_CAMPANHAS) -> list[Path]:
    """Grava um CSV por segmento (para cada time/ferramenta) + um consolidado.
    Usa utf-8-sig para o Excel abrir os acentos corretamente."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for seg, g in camp.groupby("segmento", observed=True):
        nome = str(seg).lower().replace(" ", "_").replace("õ", "o").replace("ã", "a") \
            .replace("é", "e").replace("ç", "c").replace("í", "i")
        c = pasta / f"campanha_{nome}.csv"
        g.sort_values("gasto_total", ascending=False).to_csv(c, index=False, encoding="utf-8-sig")
        caminhos.append(c)
    todos = pasta / "campanha_completa.csv"
    camp.to_csv(todos, index=False, encoding="utf-8-sig")
    return caminhos + [todos]
