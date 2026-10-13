"""Análise RFM do Boto Café: limpeza, métricas, scores e segmentos.

Fluxo (cada passo é uma função):
    carregar_base_limpa -> calcular_rfm -> atribuir_scores -> segmentar
    (ou `construir_rfm`, que roda tudo de uma vez)

Importante: este módulo NÃO lê o gabarito de perfis. Ele só enxerga o que
um analista enxergaria no banco de verdade.
"""
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from . import banco, config as cfg
from .catalogo import ESTADOS

CAMINHO_RFM = cfg.DIR_DADOS / "rfm_clientes.csv"

# Ordem "do melhor para o pior" — usada em gráficos e tabelas.
ORDEM_SEGMENTOS = [
    "Campeões", "Clientes Fiéis", "Potenciais Fiéis", "Novos", "Promissores",
    "Precisam de Atenção", "Prestes a Dar Churn", "Hibernando", "Perdidos",
]

# Regras de segmentação, na ORDEM em que são avaliadas (a primeira que bater vence).
# R, F, M = scores de 1 (pior) a 5 (melhor). Documentadas aqui e no notebook.
REGRAS_SEGMENTOS = pd.DataFrame([
    ("Campeões",            "R=5 e F=5 e M=5", "Nota máxima em tudo: compram sempre, muito e agora. O coração da receita."),
    ("Novos",               "1 único pedido e R>=4", "Primeira compra recente: ainda não sabemos quem são."),
    ("Clientes Fiéis",      "R>=3 e F>=4", "Compram com frequência e ainda estão ativos."),
    ("Potenciais Fiéis",    "R>=4 e F 2–3", "Recentes, com 2+ compras: a um passo de virar fiéis."),
    ("Prestes a Dar Churn", "R<=2 e F>=3", "Já foram bons clientes e estão esfriando: prioridade de resgate."),
    ("Precisam de Atenção", "R=3 e F=3", "Meio-termo que pode escorregar se ninguém olhar."),
    ("Promissores",         "R>=3 e F<=2 (restante)", "Compraram pouco, mas há pouco tempo."),
    ("Hibernando",          "R=2 e F<=2", "Pouco engajados e já sumindo."),
    ("Perdidos",            "R=1 e F<=2", "Sem comprar há muito tempo e com pouco histórico."),
], columns=["segmento", "regra", "interpretação"])


def _sem_acento(texto: str) -> str:
    """Remove acentos e põe em minúsculas (chave de comparação de cidades)."""
    base = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in base if not unicodedata.combining(c)).lower().strip()


def carregar_base_limpa(caminho: Path = cfg.CAMINHO_DB) -> dict:
    """Lê o SQLite e aplica a limpeza combinada na Fase 1.

    - e-mail: strip + minúsculas;
    - cidade: restaura grafia oficial (ex.: 'sao paulo' -> 'São Paulo');
    - canal_aquisicao nulo -> 'Não informado' (nunca inventamos um canal);
    - datas viram datetime; pedidos ganham a flag `valido`.
    """
    t = banco.ler_tabelas(caminho)
    cli, ped = t["clientes"].copy(), t["pedidos"].copy()

    cli["email"] = cli["email"].str.strip().str.lower()
    # dicionário (UF, cidade sem acento) -> grafia oficial
    oficial = {(uf, _sem_acento(c)): c for uf, v in ESTADOS.items() for c in v[2]}
    cli["cidade"] = [oficial.get((uf, _sem_acento(c)), c) if isinstance(c, str) else c
                     for uf, c in zip(cli["estado"], cli["cidade"])]
    cli["canal_aquisicao"] = cli["canal_aquisicao"].fillna("Não informado")
    cli["data_cadastro"] = pd.to_datetime(cli["data_cadastro"])

    ped["data_pedido"] = pd.to_datetime(ped["data_pedido"])
    ped["valido"] = ped["status"].isin(cfg.STATUS_VALIDOS)

    t.update(clientes=cli, pedidos=ped)
    return t


def calcular_rfm(pedidos: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Calcula R, F e M por cliente usando só pedidos válidos.

    - Data de referência = dia seguinte à última compra válida (assim a
      recência mínima é 1 dia, nunca 0).
    - R = dias desde a última compra; F = nº de pedidos; M = soma do valor
      pago (já com desconto), ou seja, a receita que de fato entrou.
    """
    v = pedidos[pedidos["valido"]]
    data_ref = v["data_pedido"].max() + pd.Timedelta(days=1)
    rfm = v.groupby("cliente_id").agg(
        ultima_compra=("data_pedido", "max"),
        primeira_compra=("data_pedido", "min"),
        frequencia=("id", "count"),
        monetario=("valor_total", "sum"),
    )
    rfm["recencia"] = (data_ref - rfm["ultima_compra"]).dt.days
    rfm["ticket_medio"] = rfm["monetario"] / rfm["frequencia"]
    return rfm, data_ref


def _quintil(serie: pd.Series, melhor_alto: bool = True) -> pd.Series:
    """Nota de 1 a 5 por quintis. O `rank(method='first')` desempata valores
    iguais (ex.: muitos clientes com 1 pedido) para os grupos ficarem
    equilibrados; sem isso o qcut falharia por bordas repetidas."""
    ranque = serie.rank(method="first", ascending=melhor_alto)
    return pd.qcut(ranque, 5, labels=[1, 2, 3, 4, 5]).astype(int)


def atribuir_scores(rfm: pd.DataFrame) -> pd.DataFrame:
    """Gera R, F, M (1–5) e o score combinado (ex.: '545' e soma 14).

    Recência: MENOR é melhor, por isso a escala é invertida.
    """
    out = rfm.copy()
    out["R"] = _quintil(out["recencia"], melhor_alto=False)
    out["F"] = _quintil(out["frequencia"])
    out["M"] = _quintil(out["monetario"])
    out["score_rfm"] = out["R"].astype(str) + out["F"].astype(str) + out["M"].astype(str)
    out["score_soma"] = out[["R", "F", "M"]].sum(axis=1)
    return out


def classificar_segmento(r: int, f: int, m: int, frequencia: int) -> str:
    """Aplica `REGRAS_SEGMENTOS` na ordem. Cobre todas as combinações."""
    if r == 5 and f == 5 and m == 5:
        return "Campeões"
    if frequencia == 1 and r >= 4:
        return "Novos"
    if r >= 3 and f >= 4:
        return "Clientes Fiéis"
    if r >= 4 and f >= 2:
        return "Potenciais Fiéis"
    if r <= 2 and f >= 3:
        return "Prestes a Dar Churn"
    if r == 3 and f == 3:
        return "Precisam de Atenção"
    if r >= 3:
        return "Promissores"
    if r == 2:
        return "Hibernando"
    return "Perdidos"


def segmentar(rfm: pd.DataFrame) -> pd.DataFrame:
    """Adiciona a coluna `segmento` (categórica ordenada)."""
    out = rfm.copy()
    out["segmento"] = [classificar_segmento(r, f, m, q) for r, f, m, q
                       in zip(out["R"], out["F"], out["M"], out["frequencia"])]
    out["segmento"] = pd.Categorical(out["segmento"], categories=ORDEM_SEGMENTOS, ordered=True)
    return out


def construir_rfm(caminho: Path = cfg.CAMINHO_DB) -> tuple[pd.DataFrame, dict, pd.Timestamp]:
    """Pipeline completo. Devolve (tabela RFM com dados do cliente, base limpa, data_ref)."""
    base = carregar_base_limpa(caminho)
    rfm, data_ref = calcular_rfm(base["pedidos"])
    rfm = segmentar(atribuir_scores(rfm))
    rfm = base["clientes"].set_index("id").join(rfm, how="inner").rename_axis("cliente_id")
    return rfm, base, data_ref


def resumo_segmentos(rfm: pd.DataFrame) -> pd.DataFrame:
    """Tabela-resumo por segmento: tamanho, receita, % da receita e médias de R/F/M."""
    g = rfm.groupby("segmento", observed=True).agg(
        clientes=("monetario", "size"),
        receita=("monetario", "sum"),
        recencia_media=("recencia", "mean"),
        frequencia_media=("frequencia", "mean"),
        ticket_medio=("ticket_medio", "mean"),
    )
    g["% clientes"] = g["clientes"] / g["clientes"].sum() * 100
    g["% receita"] = g["receita"] / g["receita"].sum() * 100
    return g.reindex([s for s in ORDEM_SEGMENTOS if s in g.index])
