"""Itens compartilhados pelos testes (fixtures do pytest).

Os testes leem `data/loja.db`. Se ele não existir, rode antes:  python -m src.gerar_dados
"""
import warnings

import pytest

from src import config as cfg
from src import powerbi as pbi
from src import rfm as R

warnings.filterwarnings("ignore")


@pytest.fixture(scope="session", autouse=True)
def _banco_existe():
    """Falha cedo, com uma mensagem útil, se o banco ainda não foi gerado."""
    if not cfg.CAMINHO_DB.exists():
        pytest.exit("data/loja.db não existe. Rode primeiro: python -m src.gerar_dados", returncode=2)


@pytest.fixture(scope="session")
def analise():
    """Pipeline RFM completo (calculado uma vez e reaproveitado). Devolve (rfm, base, data_ref)."""
    return R.construir_rfm()


@pytest.fixture(scope="session")
def tabelas_powerbi(analise):
    """As 5 tabelas do modelo estrela, em memória."""
    rfm, base, _ = analise
    ped_raw = base["pedidos"]
    return {
        "dim_clientes": pbi.dim_clientes(rfm, base["clientes"]),
        "fato_pedidos": pbi.fato_pedidos(ped_raw),
        "fato_itens": pbi.fato_itens(base["itens_pedido"], ped_raw),
    }
