"""Fase 6 — gera o dashboard em HTML (um único arquivo, abre com duplo clique).

Como funciona:
  1. Python monta um pacote de dados COMPACTO (listas em vez de objetos, para ocupar pouco).
  2. O molde `dashboard/template.html` recebe esse pacote e a biblioteca Plotly dentro dele.
  3. Sai `dashboard/index.html`: sem servidor, sem Python, funciona offline.
  Os filtros e cálculos rodam no navegador (JavaScript), sobre os dados embutidos.

Rodar:  python -m src.html_dashboard
"""
import json
from pathlib import Path

import pandas as pd
import plotly

from src import config as cfg
from src import powerbi as pbi
from src import rfm as R
from src.cupons import PREMISSAS, calcular_margem

DIR_DASH = cfg.RAIZ / "dashboard"
MOLDE = DIR_DASH / "template.html"
SAIDA = DIR_DASH / "index.html"


def _indice(serie: pd.Series, ordem: list) -> pd.Series:
    """Troca textos por posição numa lista (ex.: 'Norte' -> 0). Deixa o JSON bem menor."""
    return serie.map({v: i for i, v in enumerate(ordem)}).astype(int)


def montar_pacote() -> dict:
    """Lê o banco, aplica o RFM e devolve tudo que o dashboard precisa, em formato compacto."""
    rfm, base, data_ref = R.construir_rfm()
    ped_raw = base["pedidos"]
    cli = pbi.dim_clientes(rfm, base["clientes"]).sort_values("cliente_id").reset_index(drop=True)
    prod = pbi.dim_produtos(base["produtos"])
    ped = pbi.fato_pedidos(ped_raw)
    itens = pbi.fato_itens(base["itens_pedido"], ped_raw)

    segmentos = R.ORDEM_SEGMENTOS + [pbi.SEM_COMPRA]
    regioes = list(pbi.REGIOES)
    canais = sorted(cli["canal_aquisicao"].unique())
    categorias = sorted(prod["categoria"].unique())
    meses = pd.period_range(ped["data_pedido"].min(), ped["data_pedido"].max(), freq="M").astype(str).tolist()
    status = sorted(ped["status"].unique())

    pos_cli = pd.Series(cli.index, index=cli["cliente_id"])      # cliente_id -> posição na lista
    mes_de = lambda s: _indice(pd.to_datetime(s).dt.to_period("M").astype(str), meses)

    # clientes: uma linha (lista) por cliente, na ordem de `colunas_clientes` — o JS conhece essa ordem.
    clientes = pd.DataFrame({
        "id": cli["cliente_id"], "nome": cli["nome"], "email": cli["email"], "cidade": cli["cidade"],
        "estado": cli["estado"], "regiao": _indice(cli["regiao"], regioes),
        "canal": _indice(cli["canal_aquisicao"], canais),
        "recencia": cli["recencia"].astype("float").round(0), "freq": cli["frequencia"].astype("float"),
        "monet": cli["monetario"].astype("float").round(2),
        "R": cli["R"].astype("float"), "F": cli["F"].astype("float"),
        "seg": _indice(cli["segmento"], segmentos),
        "risco": (cli["em_risco"] == "Sim").astype(int), "cupom": cli["cupom_sugerido"],
    })
    clientes = clientes.astype(object).where(clientes.notna(), None)

    validos = itens[itens["valido"] == 1].merge(prod[["produto_id", "categoria"]], on="produto_id")
    it = [
        pos_cli[validos["cliente_id"]].tolist(), mes_de(validos["data_pedido"]).tolist(),
        _indice(validos["categoria"], categorias).tolist(), validos["pedido_id"].tolist(),
        validos["receita_rateada"].round(4).tolist(),
    ]
    pe = [
        pos_cli[ped["cliente_id"]].tolist(), mes_de(ped["data_pedido"]).tolist(),
        _indice(ped["status"], status).tolist(), ped["valido"].tolist(), ped["usou_cupom"].tolist(),
    ]
    margem = calcular_margem(base)
    cupons = {s: {"cupom": p.cupom, "desconto": p.desconto, "incremental": p.incremental, "acao": p.acao}
              for s, p in PREMISSAS.items()}

    return {
        "geradoEm": str(pd.Timestamp(data_ref).date()), "margem": round(margem, 4),
        "segmentos": segmentos, "emRisco": pbi.EM_RISCO, "regioes": regioes, "canais": canais,
        "categorias": categorias, "meses": meses, "status": status,
        "colunasClientes": list(clientes.columns),
        "clientes": clientes.values.tolist(), "itens": it, "pedidos": pe, "cupons": cupons,
    }


def gerar(saida: Path = SAIDA) -> Path:
    """Injeta dados + Plotly no molde e grava o HTML final."""
    pacote = montar_pacote()
    plotly_js = (Path(plotly.__file__).parent / "package_data" / "plotly.min.js").read_text(encoding="utf-8")
    html = MOLDE.read_text(encoding="utf-8")
    # '</' dentro de um <script> poderia fechar a tag cedo; escapar é a precaução padrão.
    dados = json.dumps(pacote, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/*__PLOTLY__*/", plotly_js.replace("</script", "<\\/script")).replace("/*__DADOS__*/", dados)
    saida.write_text(html, encoding="utf-8")
    return saida


if __name__ == "__main__":
    destino = gerar()
    print(f"{destino.relative_to(cfg.RAIZ)} · {destino.stat().st_size / 1e6:.1f} MB")
