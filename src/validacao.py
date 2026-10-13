"""Validações de integridade do banco gerado.

Cada checagem devolve (nome, passou?, detalhe). Distinguimos dois grupos:
  - Integridade: DEVE passar (chaves, datas, totais).
  - Sujeira intencional: é esperado ENCONTRAR problemas (para você limpar).
"""
import sqlite3
from pathlib import Path

import pandas as pd

from . import config as cfg


def _resultado(nome: str, qtd_erros: int, detalhe: str = "") -> dict:
    return {"checagem": nome, "ok": qtd_erros == 0, "violações": qtd_erros, "detalhe": detalhe}


def validar_integridade(caminho: Path = cfg.CAMINHO_DB) -> pd.DataFrame:
    """Executa as checagens de integridade lendo o banco SQLite já gravado."""
    with sqlite3.connect(caminho) as conn:
        cli = pd.read_sql("SELECT * FROM clientes", conn)
        prod = pd.read_sql("SELECT * FROM produtos", conn)
        ped = pd.read_sql("SELECT * FROM pedidos", conn)
        itn = pd.read_sql("SELECT * FROM itens_pedido", conn)
        fk_erros = conn.execute("PRAGMA foreign_key_check").fetchall()

    r = []
    # 1) Chaves primárias únicas
    for nome, df in [("clientes", cli), ("produtos", prod), ("pedidos", ped), ("itens_pedido", itn)]:
        r.append(_resultado(f"PK única em {nome}", int(df["id"].duplicated().sum())))

    # 2) Chaves estrangeiras (checagem do SQLite + checagem própria)
    r.append(_resultado("PRAGMA foreign_key_check", len(fk_erros)))
    r.append(_resultado("pedidos.cliente_id existe em clientes", int((~ped["cliente_id"].isin(cli["id"])).sum())))
    r.append(_resultado("itens.pedido_id existe em pedidos", int((~itn["pedido_id"].isin(ped["id"])).sum())))
    r.append(_resultado("itens.produto_id existe em produtos", int((~itn["produto_id"].isin(prod["id"])).sum())))
    r.append(_resultado("todo pedido tem >= 1 item", int((~ped["id"].isin(itn["pedido_id"])).sum())))

    # 3) Datas
    d_ped = pd.to_datetime(ped["data_pedido"])
    d_cad = pd.to_datetime(cli["data_cadastro"])
    r.append(_resultado("pedidos dentro da janela de 24 meses",
                        int(((d_ped < cfg.DATA_INICIO) | (d_ped > cfg.DATA_FIM)).sum())))
    r.append(_resultado("cadastros dentro da janela",
                        int(((d_cad < cfg.DATA_INICIO) | (d_cad > cfg.DATA_FIM)).sum())))
    primeira = ped.merge(cli[["id", "data_cadastro"]], left_on="cliente_id", right_on="id", suffixes=("", "_cli"))
    r.append(_resultado("nenhum pedido antes do cadastro do cliente",
                        int((pd.to_datetime(primeira["data_pedido"]) < pd.to_datetime(primeira["data_cadastro"])).sum())))

    # 4) Totais batendo com os itens: valor_total = soma(qtd x preço) - desconto
    subtotal = (itn.assign(s=itn["quantidade"] * itn["preco_unitario"])
                   .groupby("pedido_id")["s"].sum().rename("subtotal"))
    conf = ped.set_index("id").join(subtotal)
    dif = (conf["valor_total"] - (conf["subtotal"] - conf["desconto"])).abs()
    r.append(_resultado("valor_total = soma dos itens - desconto", int((dif > 0.01).sum()),
                        f"maior diferença: R$ {dif.max():.4f}"))
    r.append(_resultado("desconto <= subtotal", int((conf["desconto"] > conf["subtotal"] + 0.01).sum())))
    r.append(_resultado("cupom nulo <=> desconto zero",
                        int(((conf["cupom_usado"].isna()) != (conf["desconto"] == 0)).sum())))

    # 5) Regras de negócio
    r.append(_resultado("custo < preço em todos os produtos", int((prod["custo"] >= prod["preco"]).sum())))
    r.append(_resultado("quantidade e preço unitário positivos",
                        int(((itn["quantidade"] <= 0) | (itn["preco_unitario"] <= 0)).sum())))
    return pd.DataFrame(r)


def diagnosticar_sujeira(caminho: Path = cfg.CAMINHO_DB) -> pd.DataFrame:
    """Conta as imperfeições deixadas de propósito para você praticar limpeza."""
    with sqlite3.connect(caminho) as conn:
        cli = pd.read_sql("SELECT * FROM clientes", conn)
        ped = pd.read_sql("SELECT status, COUNT(*) AS n FROM pedidos GROUP BY status", conn)
    n_ped = int(ped["n"].sum())
    inv = ped.set_index("status")["n"]
    return pd.DataFrame([
        {"problema": "e-mails com espaços nas pontas", "qtd": int((cli["email"] != cli["email"].str.strip()).sum())},
        {"problema": "e-mails em CAIXA ALTA", "qtd": int(cli["email"].str.strip().str.contains(r"[A-Z]").sum())},
        {"problema": "cidades sem acento/minúsculas",
         "qtd": int((cli["cidade"] == cli["cidade"].str.lower()).sum())},
        {"problema": "canal_aquisicao nulo", "qtd": int(cli["canal_aquisicao"].isna().sum())},
        {"problema": f"pedidos cancelados (de {n_ped})", "qtd": int(inv.get("cancelado", 0))},
        {"problema": f"pedidos devolvidos (de {n_ped})", "qtd": int(inv.get("devolvido", 0))},
        {"problema": "pedidos pendentes (em andamento)", "qtd": int(inv.get("pendente", 0))},
    ])
