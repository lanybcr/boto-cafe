"""Persistência: cria o banco SQLite (loja.db) e exporta os CSVs brutos."""
import sqlite3
from pathlib import Path

import pandas as pd

from . import config as cfg

# O esquema é declarado explicitamente (e não deixado para o pandas inferir)
# para ter chaves primárias, chaves estrangeiras e regras CHECK — é assim que
# um banco de verdade protege a qualidade dos dados.
DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE clientes (
    id               INTEGER PRIMARY KEY,
    nome             TEXT NOT NULL,
    email            TEXT NOT NULL,
    cidade           TEXT,
    estado           TEXT NOT NULL,
    data_cadastro    TEXT NOT NULL,          -- formato ISO: AAAA-MM-DD
    canal_aquisicao  TEXT
);

CREATE TABLE produtos (
    id         INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    preco      REAL NOT NULL CHECK (preco > 0),
    custo      REAL NOT NULL CHECK (custo > 0)
);

CREATE TABLE pedidos (
    id           INTEGER PRIMARY KEY,
    cliente_id   INTEGER NOT NULL REFERENCES clientes(id),
    data_pedido  TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN
                 ('pendente','pago','enviado','entregue','cancelado','devolvido')),
    cupom_usado  TEXT,
    desconto     REAL NOT NULL DEFAULT 0 CHECK (desconto >= 0),
    valor_total  REAL NOT NULL CHECK (valor_total >= 0),
    canal        TEXT NOT NULL
);

CREATE TABLE itens_pedido (
    id              INTEGER PRIMARY KEY,
    pedido_id       INTEGER NOT NULL REFERENCES pedidos(id),
    produto_id      INTEGER NOT NULL REFERENCES produtos(id),
    quantidade      INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario  REAL NOT NULL CHECK (preco_unitario > 0)
);

-- Índices nas chaves estrangeiras: aceleram os JOINs das próximas fases.
CREATE INDEX idx_pedidos_cliente ON pedidos(cliente_id);
CREATE INDEX idx_pedidos_data    ON pedidos(data_pedido);
CREATE INDEX idx_itens_pedido    ON itens_pedido(pedido_id);
CREATE INDEX idx_itens_produto   ON itens_pedido(produto_id);
"""

TABELAS = ["clientes", "produtos", "pedidos", "itens_pedido"]


def salvar_sqlite(dados: dict, caminho: Path = cfg.CAMINHO_DB) -> None:
    """Recria o banco do zero e grava as 4 tabelas (ordem respeita as FKs)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists():
        caminho.unlink()  # recriar do zero garante idempotência
    with sqlite3.connect(caminho) as conn:
        conn.executescript(DDL)
        for tabela in TABELAS:
            dados[tabela].to_sql(tabela, conn, if_exists="append", index=False)
        conn.commit()


def exportar_csvs(dados: dict, pasta: Path = cfg.DIR_RAW) -> None:
    """Exporta as 4 tabelas para CSV (UTF-8) + o gabarito de perfis."""
    pasta.mkdir(parents=True, exist_ok=True)
    for tabela in TABELAS:
        dados[tabela].to_csv(pasta / f"{tabela}.csv", index=False, encoding="utf-8")
    # O gabarito fica FORA de data/raw: ele é a "resposta da prova" e a
    # análise RFM não deve usá-lo, só conferi-lo no final.
    dados["gabarito"].to_csv(cfg.CAMINHO_GABARITO, index=False, encoding="utf-8")


def ler_tabelas(caminho: Path = cfg.CAMINHO_DB) -> dict:
    """Lê as 4 tabelas do SQLite para DataFrames."""
    with sqlite3.connect(caminho) as conn:
        return {t: pd.read_sql(f"SELECT * FROM {t}", conn) for t in TABELAS}
