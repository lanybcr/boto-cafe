"""Fase 5 — exporta as tabelas em MODELO ESTRELA para o Power BI.

Estrela = poucas tabelas "fato" (o que aconteceu: pedidos, itens) no centro,
ligadas a tabelas "dimensão" (quem/o quê/quando: clientes, produtos, calendário).

    dim_clientes ──┐                 ┌── dim_produtos
                   ├─ fato_pedidos   │
    dim_calendario ┤        │        │
                   └─ fato_itens ────┘

Rodar:  python -m src.powerbi
"""
from pathlib import Path

import pandas as pd

from src import config as cfg
from src import rfm as R
from src.cupons import PREMISSAS

# Convenção brasileira: o Power BI em pt-BR lê ';' e vírgula decimal sem configurar nada.
SEP, DECIMAL = ";", ","

REGIOES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}
UF_REGIAO = {uf: reg for reg, ufs in REGIOES.items() for uf in ufs}

# Segmentos tratados como "em risco" (mesma definição do dashboard).
EM_RISCO = ["Precisam de Atenção", "Prestes a Dar Churn", "Hibernando"]
SEM_COMPRA = "Sem compra válida"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def dim_calendario(inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Uma linha por dia, de 1º de jan do ano inicial a 31 de dez do ano final.

    Calendário sem buracos é exigido pelas funções de tempo do DAX (DATEADD etc.).
    Cada coluna `*_ordem` serve para o Power BI ordenar nomes de mês/dia corretamente.
    """
    dias = pd.date_range(f"{inicio.year}-01-01", f"{fim.year}-12-31", freq="D")
    c = pd.DataFrame({"data": dias})
    c["ano"] = c["data"].dt.year
    c["trimestre"] = "T" + c["data"].dt.quarter.astype(str)
    c["mes_num"] = c["data"].dt.month
    c["mes_nome"] = c["mes_num"].map(lambda m: MESES[m - 1].capitalize())
    c["ano_mes"] = c["data"].dt.strftime("%Y-%m")
    c["dia_semana_num"] = c["data"].dt.dayofweek + 1          # 1 = segunda
    c["dia_semana"] = c["dia_semana_num"].map(lambda d: DIAS[d - 1].capitalize())
    c["fim_de_semana"] = (c["dia_semana_num"] >= 6).map({True: "Sim", False: "Não"})
    return c


def dim_clientes(rfm: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Cliente + R/F/M, notas, segmento e cupom sugerido.

    Os clientes sem nenhuma compra válida ficam na dimensão (para não sumirem
    dos filtros), com segmento 'Sem compra válida'.
    """
    cols = ["recencia", "frequencia", "monetario", "ticket_medio", "R", "F", "M",
            "score_rfm", "score_soma", "primeira_compra", "ultima_compra"]
    d = clientes.set_index("id").rename_axis("cliente_id").join(rfm[cols + ["segmento"]], how="left")
    # o join deixa números como decimal (2.0) por causa dos clientes sem compra: volta a inteiro
    inteiros = ["recencia", "frequencia", "R", "F", "M", "score_soma"]
    d[inteiros] = d[inteiros].astype("Int64")
    d["segmento"] = d["segmento"].astype(object).fillna(SEM_COMPRA)
    ordem = {s: i + 1 for i, s in enumerate(R.ORDEM_SEGMENTOS)} | {SEM_COMPRA: len(R.ORDEM_SEGMENTOS) + 1}
    d["segmento_ordem"] = d["segmento"].map(ordem)
    d["em_risco"] = d["segmento"].isin(EM_RISCO).map({True: "Sim", False: "Não"})
    d["cupom_sugerido"] = d["segmento"].map(lambda s: PREMISSAS[s].cupom if s in PREMISSAS else "—")
    d["regiao"] = d["estado"].map(UF_REGIAO)
    ordem_cols = ["nome", "email", "cidade", "estado", "regiao", "canal_aquisicao", "data_cadastro",
                  "primeira_compra", "ultima_compra", "recencia", "frequencia", "monetario",
                  "ticket_medio", "R", "F", "M", "score_rfm", "score_soma", "segmento",
                  "segmento_ordem", "em_risco", "cupom_sugerido"]
    return d[ordem_cols].reset_index()


def dim_produtos(produtos: pd.DataFrame) -> pd.DataFrame:
    """Produto + margem unitária (preço − custo)."""
    p = produtos.rename(columns={"id": "produto_id", "nome": "produto"}).copy()
    p["margem_unitaria"] = p["preco"] - p["custo"]
    p["margem_pct"] = p["margem_unitaria"] / p["preco"]
    return p[["produto_id", "produto", "categoria", "preco", "custo", "margem_unitaria", "margem_pct"]]


def fato_pedidos(pedidos: pd.DataFrame) -> pd.DataFrame:
    """Um pedido por linha. TODOS os status vão (cancelados também), com a flag `valido`
    (1/0) para o DAX filtrar; assim dá para analisar cancelamento e devolução."""
    f = pedidos.rename(columns={"id": "pedido_id", "desconto": "desconto_valor"}).copy()
    f["valido"] = f["valido"].astype(int)
    f["usou_cupom"] = f["cupom_usado"].notna().astype(int)
    f["cupom_usado"] = f["cupom_usado"].fillna("Sem cupom")
    return f[["pedido_id", "cliente_id", "data_pedido", "status", "valido", "canal",
              "cupom_usado", "usou_cupom", "desconto_valor", "valor_total"]]


def fato_itens(itens: pd.DataFrame, pedidos: pd.DataFrame) -> pd.DataFrame:
    """Um item por linha, com cliente, data e `receita_rateada` (o desconto do pedido
    dividido entre os itens, proporcional ao subtotal). Somar a receita_rateada dos
    pedidos válidos dá exatamente a soma de valor_total.

    Cliente e data são copiados do pedido de propósito: assim o item se liga direto
    ao calendário e ao cliente, sem cadeia de relacionamentos."""
    p = pedidos[["id", "cliente_id", "data_pedido", "valor_total", "valido"]]
    f = itens.rename(columns={"id": "item_id"}).merge(p, left_on="pedido_id", right_on="id")
    f["subtotal"] = f["quantidade"] * f["preco_unitario"]
    f["receita_rateada"] = f["subtotal"] / f.groupby("pedido_id")["subtotal"].transform("sum") * f["valor_total"]
    f["valido"] = f["valido"].astype(int)
    return f[["item_id", "pedido_id", "cliente_id", "produto_id", "data_pedido", "valido",
              "quantidade", "preco_unitario", "subtotal", "receita_rateada"]]


def exportar(pasta: Path = cfg.DIR_POWERBI) -> dict[str, pd.DataFrame]:
    """Gera os 5 CSVs (utf-8-sig, ';' e vírgula decimal). Devolve as tabelas para conferência."""
    rfm, base, _ = R.construir_rfm()
    ped = base["pedidos"]
    tabelas = {
        "dim_clientes": dim_clientes(rfm, base["clientes"]),
        "dim_produtos": dim_produtos(base["produtos"]),
        "dim_calendario": dim_calendario(ped["data_pedido"].min(), ped["data_pedido"].max()),
        "fato_pedidos": fato_pedidos(ped),
        "fato_itens": fato_itens(base["itens_pedido"], ped),
    }
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, df in tabelas.items():
        df = df.copy()
        for col in df.select_dtypes("datetime").columns:   # datas ISO: lidas igual em qualquer idioma
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        df.round(4).to_csv(pasta / f"{nome}.csv", index=False, sep=SEP, decimal=DECIMAL,
                           encoding="utf-8-sig")
    return tabelas


if __name__ == "__main__":
    for nome, df in exportar().items():
        print(f"{nome:15s} {len(df):>7,} linhas · {df.shape[1]} colunas")
