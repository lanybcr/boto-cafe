"""RFM em SQL: aplica as VIEWs de `sql/01_vw_rfm.sql` no SQLite e lê o resultado.

O Python (src/rfm.py) e o SQL calculam a MESMA coisa, por caminhos diferentes. Ter os dois é útil porque:
  - o SQL fica dentro do banco, então qualquer ferramenta (BI, notebook, outro time) lê as mesmas regras;
  - o teste `tests/test_rfm.py` compara os dois e acusa se um dia as regras divergirem.

Rodar:  python -m src.sql_rfm
"""
import sqlite3
from pathlib import Path

import pandas as pd

from . import config as cfg

CAMINHO_SQL = cfg.RAIZ / "sql" / "01_vw_rfm.sql"


def criar_views(caminho_db: Path = cfg.CAMINHO_DB) -> None:
    """Cria (ou recria) as VIEWs de RFM dentro do banco."""
    with sqlite3.connect(caminho_db) as conn:
        conn.executescript(CAMINHO_SQL.read_text(encoding="utf-8"))


def rfm_via_sql(caminho_db: Path = cfg.CAMINHO_DB) -> pd.DataFrame:
    """Lê a VIEW final (`vw_rfm_segmentos`): uma linha por cliente com compra válida, ordenada por cliente_id."""
    with sqlite3.connect(caminho_db) as conn:
        return pd.read_sql_query("SELECT * FROM vw_rfm_segmentos ORDER BY cliente_id", conn)


if __name__ == "__main__":
    criar_views()
    df = rfm_via_sql()
    print(f"vw_rfm_segmentos: {len(df):,} clientes")
    print(df["segmento"].value_counts().to_string())
