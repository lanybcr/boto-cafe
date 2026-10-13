"""Camada de dados do dashboard: carrega, monta a tabela de itens e aplica os filtros.

Decisão de design (importante para interpretar os números):
- O SEGMENTO RFM é uma "foto" do cliente calculada sobre todo o histórico.
  Ele não muda quando você filtra o período.
- Receita, pedidos e ticket médio respondem aos filtros de período e categoria.
- Para o filtro de categoria fazer sentido, a receita é calculada por ITEM, com o
  desconto do pedido rateado entre os itens. Assim, sem filtro de categoria, a soma
  bate exatamente com o `valor_total` dos pedidos.
"""
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from src import cupons, rfm as R

# Segmentos tratados como "em risco" (KPI e tabela de resgate).
SEGMENTOS_EM_RISCO = ["Precisam de Atenção", "Prestes a Dar Churn", "Hibernando"]


@dataclass
class Dados:
    """Tudo o que o dashboard precisa, já carregado."""
    rfm: pd.DataFrame      # um cliente por linha (R, F, M, segmento...)
    itens: pd.DataFrame    # um item de pedido válido por linha, com receita rateada
    margem: float          # margem bruta real (do custo dos produtos)
    data_ref: pd.Timestamp


@st.cache_data(show_spinner="Carregando a base do Boto Café...")
def carregar() -> Dados:
    """Roda o pipeline RFM e monta a tabela de itens (cacheada pelo Streamlit)."""
    rfm, base, data_ref = R.construir_rfm()
    ped = base["pedidos"].loc[base["pedidos"]["valido"],
                              ["id", "cliente_id", "data_pedido", "valor_total"]]
    it = base["itens_pedido"].merge(ped, left_on="pedido_id", right_on="id", suffixes=("", "_ped"))
    it = it.merge(base["produtos"][["id", "nome", "categoria"]].rename(
        columns={"id": "produto_id", "nome": "produto"}), on="produto_id")
    it["subtotal_item"] = it["quantidade"] * it["preco_unitario"]
    subtotal_pedido = it.groupby("pedido_id")["subtotal_item"].transform("sum")
    # receita do item = fatia do valor pago (já com desconto) proporcional ao item
    it["receita"] = it["subtotal_item"] / subtotal_pedido * it["valor_total"]
    itens = it[["pedido_id", "cliente_id", "data_pedido", "produto", "categoria", "receita"]]
    return Dados(rfm, itens, cupons.calcular_margem(base), data_ref)


def filtrar(d: Dados, periodo: tuple, estados: list[str], segmentos: list[str],
            categorias: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica os 4 filtros. Devolve (clientes filtrados, itens filtrados).

    Só ficam clientes que têm ao menos um item dentro do período/categoria escolhidos.
    """
    ini, fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
    it = d.itens[(d.itens["data_pedido"] >= ini) & (d.itens["data_pedido"] <= fim)
                 & d.itens["categoria"].isin(categorias)]
    cli = d.rfm[d.rfm["estado"].isin(estados) & d.rfm["segmento"].isin(segmentos)]
    it = it[it["cliente_id"].isin(cli.index)]
    cli = cli[cli.index.isin(it["cliente_id"].unique())]
    return cli, it


def indicadores(cli: pd.DataFrame, it: pd.DataFrame) -> dict:
    """KPIs do topo: receita, clientes, ticket médio e % de clientes em risco."""
    pedidos = it["pedido_id"].nunique()
    receita = float(it["receita"].sum())
    n = len(cli)
    em_risco = cli["segmento"].isin(SEGMENTOS_EM_RISCO).sum()
    return {
        "receita": receita,
        "clientes": n,
        "pedidos": pedidos,
        "ticket": receita / pedidos if pedidos else 0.0,
        "pct_risco": em_risco / n if n else 0.0,
    }
