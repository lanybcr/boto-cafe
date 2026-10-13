"""Testes dos dados: integridade do banco, privacidade e coerência dos totais."""
import pandas as pd

from src import banco, config as cfg, validacao


def test_integridade_do_banco_sem_violacoes():
    """Todas as checagens da Fase 1 (chaves, datas, totais batendo com itens) passam."""
    resultado = validacao.validar_integridade()
    reprovadas = resultado.loc[~resultado["ok"], "checagem"].tolist()
    assert not reprovadas, f"checagens reprovadas: {reprovadas}"


def test_volumes_esperados():
    """O banco tem o volume pedido: ~2.000 clientes e ~15.000 pedidos."""
    t = banco.ler_tabelas()
    assert len(t["clientes"]) == cfg.N_CLIENTES
    assert len(t["produtos"]) == 40
    assert 14_000 <= len(t["pedidos"]) <= 17_000


def test_emails_sao_todos_ficticios():
    """Nenhum e-mail pode usar domínio real: todos terminam em example.com (domínio reservado)."""
    emails = banco.ler_tabelas()["clientes"]["email"].str.strip().str.lower()
    assert emails.str.endswith("@example.com").all()


def test_emails_sao_unicos():
    emails = banco.ler_tabelas()["clientes"]["email"].str.strip().str.lower()
    assert emails.is_unique


def test_receita_dos_itens_bate_com_a_dos_pedidos(tabelas_powerbi):
    """A receita rateada por item, somada, é igual ao valor pago dos pedidos válidos (centavo a centavo)."""
    itens, pedidos = tabelas_powerbi["fato_itens"], tabelas_powerbi["fato_pedidos"]
    por_item = itens.loc[itens["valido"] == 1, "receita_rateada"].sum()
    por_pedido = pedidos.loc[pedidos["valido"] == 1, "valor_total"].sum()
    assert abs(por_item - por_pedido) < 0.01


def test_status_invalidos_ficam_fora_da_receita(tabelas_powerbi):
    pedidos = tabelas_powerbi["fato_pedidos"]
    validos = set(pedidos.loc[pedidos["valido"] == 1, "status"])
    assert validos == {"pago", "enviado", "entregue"}


def test_clientes_sem_compra_viram_segmento_proprio(tabelas_powerbi):
    """Quem nunca comprou não some do modelo: entra como 'Sem compra válida'."""
    dim = tabelas_powerbi["dim_clientes"]
    assert len(dim) == cfg.N_CLIENTES
    assert dim["segmento"].notna().all()
    sem_compra = dim[dim["segmento"] == "Sem compra válida"]
    assert (sem_compra["frequencia"].fillna(0) == 0).all()
