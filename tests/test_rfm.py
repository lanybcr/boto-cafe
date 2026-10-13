"""Testes da análise RFM e dos cupons."""
import pytest

from src import cupons
from src import rfm as R


def test_notas_vao_de_1_a_5(analise):
    rfm, _, _ = analise
    for nota in ("R", "F", "M"):
        assert set(rfm[nota].unique()) == {1, 2, 3, 4, 5}


def test_quintis_sao_equilibrados(analise):
    """Cada nota recebe ~20% dos clientes (o rank 'first' desempata os valores repetidos)."""
    rfm, _, _ = analise
    for nota in ("R", "F", "M"):
        proporcao = rfm[nota].value_counts(normalize=True)
        assert proporcao.between(0.19, 0.21).all(), f"{nota}: {proporcao.to_dict()}"


def test_todo_cliente_cai_em_um_segmento_conhecido(analise):
    rfm, _, _ = analise
    assert rfm["segmento"].notna().all()
    assert set(rfm["segmento"].astype(str)) <= set(R.ORDEM_SEGMENTOS)


def test_recencia_minima_e_1_dia(analise):
    """A data de referência é o dia seguinte à última compra, então a recência nunca é 0."""
    rfm, _, _ = analise
    assert rfm["recencia"].min() >= 1


def test_monetario_soma_a_receita_valida(analise):
    rfm, base, _ = analise
    pedidos = base["pedidos"]
    receita = pedidos.loc[pedidos["valido"], "valor_total"].sum()
    assert rfm["monetario"].sum() == pytest.approx(receita)


def test_regras_de_segmento_casos_conhecidos():
    assert R.classificar_segmento(5, 5, 5, 20) == "Campeões"
    assert R.classificar_segmento(5, 1, 1, 1) == "Novos"            # 1 pedido e recente
    assert R.classificar_segmento(4, 4, 3, 10) == "Clientes Fiéis"
    assert R.classificar_segmento(2, 4, 4, 9) == "Prestes a Dar Churn"
    assert R.classificar_segmento(1, 1, 1, 1) == "Perdidos"


def test_rfm_em_sql_e_igual_ao_do_pandas(analise):
    """A camada SQL (sql/01_vw_rfm.sql) calcula exatamente o mesmo que o pandas: R, F, M, notas e segmento."""
    from src import sql_rfm
    sql_rfm.criar_views()
    sq = sql_rfm.rfm_via_sql().set_index("cliente_id")
    py = analise[0].loc[sq.index]
    assert len(sq) == len(py)
    assert (sq["recencia"].values == py["recencia"].values).all()
    assert (sq["frequencia"].values == py["frequencia"].values).all()
    assert abs(sq["monetario"].values - py["monetario"].values).max() < 1e-6
    for nota in ("R", "F", "M"):
        assert (sq[nota].values == py[nota].values).all(), f"nota {nota} diverge"
    assert (sq["segmento"].values == py["segmento"].astype(str).values).all()


def test_desconto_de_equilibrio_e_incremental_vezes_margem():
    """Regra da Fase 3: o cupom só compensa se desconto < incremental × margem."""
    p = cupons.PREMISSAS["Prestes a Dar Churn"]
    assert cupons.desconto_ponto_equilibrio(p, 0.5) == pytest.approx(p.incremental * 0.5)


def test_simulacao_nao_tem_segmento_faltando(analise):
    rfm, base, _ = analise
    sim = cupons.simular(rfm, cupons.calcular_margem(base))
    assert set(sim.index) == set(R.ORDEM_SEGMENTOS)
    assert (sim["custo_total"] >= 0).all()
