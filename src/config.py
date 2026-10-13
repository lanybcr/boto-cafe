"""Configurações globais do projeto Boto Café.

Tudo que é "parâmetro" (seed, tamanho da base, datas, caminhos) fica aqui,
para que mudar o experimento seja mexer em um único lugar.
"""
from pathlib import Path

import pandas as pd

# --- Caminhos -------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
DIR_DADOS = RAIZ / "data"
DIR_RAW = DIR_DADOS / "raw"          # CSVs brutos (saída da Fase 1)
DIR_POWERBI = DIR_DADOS / "powerbi"  # CSVs em modelo estrela (Fase 5)
CAMINHO_DB = DIR_DADOS / "loja.db"
CAMINHO_GABARITO = DIR_DADOS / "gabarito_perfis.csv"

# --- Reprodutibilidade ----------------------------------------------------
SEED = 42  # mesma seed => exatamente os mesmos dados em qualquer máquina

# --- Volume e janela de tempo ---------------------------------------------
N_CLIENTES = 2000
# Data final FIXA (e não "hoje"): se a data mudasse a cada execução, os dados
# e todos os resultados das análises mudariam junto.
DATA_FIM = pd.Timestamp("2026-10-07")
JANELA_DIAS = 730  # ~24 meses
DATA_INICIO = DATA_FIM - pd.Timedelta(days=JANELA_DIAS)

# Reajuste de preços: pedidos anteriores a esta data usam o preço antigo.
DATA_REAJUSTE = pd.Timestamp("2026-01-01")
FATOR_REAJUSTE = 1.06

# Lançamento do app: antes disso, o canal "app" não existe.
DATA_LANCAMENTO_APP = pd.Timestamp("2025-03-01")

# Status considerados "pedido válido" para análises de receita (Fase 2).
STATUS_VALIDOS = ("pago", "enviado", "entregue")
