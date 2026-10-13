"""Gerador de dados sintéticos da Boto Café.

Ideia central: primeiro definimos o "roteiro" de cada cliente (o PERFIL
comportamental) e só depois simulamos as compras. Assim a análise RFM da
Fase 2 tem uma "verdade" contra a qual pode ser conferida.
"""
import unicodedata

import numpy as np
import pandas as pd
from faker import Faker

from . import catalogo as cat
from . import config as cfg

# ---------------------------------------------------------------------------
# Perfis comportamentais
# ---------------------------------------------------------------------------
# prop        : proporção de clientes no perfil
# media/min   : nº de pedidos esperado (Poisson) e mínimo garantido
# cad         : intervalo (em dias desde o início da janela) do cadastro
# parada      : (min, max) dias ANTES do fim da janela em que o cliente para de
#               comprar; None = continua ativo até o fim
# recente     : (min, max) dias antes do fim da atividade em que cai o último
#               pedido (garante que VIPs/fiéis realmente estejam "quentes")
# cupom       : probabilidade de usar o cupom sazonal quando ele existe
# expo_preco  : >0 prefere itens caros; <0 prefere itens baratos
# itens       : média extra de itens por pedido (além de 1)
PERFIS = {
    "vip":       dict(prop=0.05, media=40, minimo=24, cad=(0, 365),   parada=None,       recente=(0, 30),  cupom=0.25, expo_preco=0.25,  itens=1.6),
    "fiel":      dict(prop=0.15, media=15, minimo=8,  cad=(0, 420),   parada=None,       recente=(0, 60),  cupom=0.50, expo_preco=0.0,   itens=1.0),
    "ocasional": dict(prop=0.30, media=3.5, minimo=1, cad=(0, 600),   parada=None,       recente=None,     cupom=0.60, expo_preco=-0.1,  itens=0.7),
    "novo":      dict(prop=0.12, media=1.8, minimo=1, cad=(650, 720), parada=None,       recente=None,     cupom=0.55, expo_preco=0.0,   itens=0.7),
    "em_risco":  dict(prop=0.12, media=6,  minimo=4,  cad=(0, 365),   parada=(100, 200), recente=(0, 20),  cupom=0.50, expo_preco=0.0,   itens=0.9),
    "perdido":   dict(prop=0.18, media=3,  minimo=1,  cad=(0, 400),   parada=(300, 560), recente=None,     cupom=0.60, expo_preco=-0.1,  itens=0.7),
    "cacador":   dict(prop=0.08, media=9,  minimo=5,  cad=(0, 500),   parada=None,       recente=(0, 120), cupom=0.95, expo_preco=-0.3,  itens=0.8),
}

# Preferência de categoria por perfil (soma 1 em cada linha).
PESO_CATEGORIA = {
    #            Grãos  Cafeteiras Acessórios Kits  Assinaturas
    "vip":       [0.40, 0.12, 0.12, 0.14, 0.22],
    "fiel":      [0.50, 0.08, 0.12, 0.08, 0.22],
    "ocasional": [0.45, 0.15, 0.25, 0.12, 0.03],
    "novo":      [0.45, 0.15, 0.20, 0.17, 0.03],
    "em_risco":  [0.52, 0.10, 0.14, 0.10, 0.14],
    "perdido":   [0.45, 0.15, 0.25, 0.12, 0.03],
    "cacador":   [0.40, 0.20, 0.20, 0.17, 0.03],
}
CATEGORIAS = ["Grãos", "Cafeteiras", "Acessórios", "Kits Presente", "Assinaturas"]

# Probabilidade de cancelamento / devolução de um pedido.
P_CANCELADO = 0.035
P_DEVOLVIDO = 0.025


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def _sem_acento(texto: str) -> str:
    """Remove acentos e cedilhas (ex.: 'São Luís' -> 'Sao Luis')."""
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def _dia_para_data(idx: int) -> pd.Timestamp:
    """Converte o índice do dia (0 = início da janela) em data."""
    return cfg.DATA_INICIO + pd.Timedelta(days=int(idx))


def _sexta_black_friday(ano: int) -> pd.Timestamp:
    """Black Friday = sexta-feira seguinte ao Dia de Ação de Graças (4ª quinta de nov.)."""
    quintas = pd.date_range(f"{ano}-11-01", f"{ano}-11-30", freq="W-THU")
    return quintas[3] + pd.Timedelta(days=1)


def _domingo_dia_dos_pais(ano: int) -> pd.Timestamp:
    """Dia dos Pais no Brasil = 2º domingo de agosto."""
    domingos = pd.date_range(f"{ano}-08-01", f"{ano}-08-31", freq="W-SUN")
    return domingos[1]


# ---------------------------------------------------------------------------
# Calendário de sazonalidade
# ---------------------------------------------------------------------------
def montar_calendario() -> dict:
    """Cria, para cada dia da janela, o peso de demanda e o cupom sazonal ativo.

    Retorna dict com:
      peso  : np.ndarray (dias,) - quanto cada dia "atrai" pedidos
      cupom : lista (dias,)      - código do cupom sazonal do dia (ou None)
      promo : np.ndarray (dias,) - 1 se há campanha ativa, 0 caso contrário
    """
    n_dias = cfg.JANELA_DIAS + 1
    datas = [_dia_para_data(i) for i in range(n_dias)]
    peso = np.ones(n_dias)
    cupom = [None] * n_dias

    for i, d in enumerate(datas):
        # Tendência: a loja cresce ~30% ao longo dos 24 meses.
        peso[i] *= 1 + 0.3 * i / cfg.JANELA_DIAS
        # Fins de semana vendem um pouco mais (compra por lazer).
        if d.weekday() >= 5:
            peso[i] *= 1.1

        bf = _sexta_black_friday(d.year)
        pais = _domingo_dia_dos_pais(d.year)
        if -3 <= (d - bf).days <= 3:                      # semana da Black Friday
            peso[i] *= 6 if d == bf else 4
            cupom[i] = "BLACK25"
        elif d.month == 12 and d.day <= 22:               # corrida de Natal
            peso[i] *= 2.0
            cupom[i] = "NATAL15"
        elif -10 <= (d - pais).days <= 0:                 # 10 dias antes do Dia dos Pais
            peso[i] *= 2.5
            cupom[i] = "PAIS12"

    promo = np.array([c is not None for c in cupom], dtype=float)
    return {"peso": peso, "cupom": cupom, "promo": promo}


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
def gerar_produtos() -> pd.DataFrame:
    """Monta a tabela produtos a partir do catálogo."""
    df = pd.DataFrame(cat.PRODUTOS, columns=["nome", "categoria", "preco", "custo"])
    df.insert(0, "id", range(1, len(df) + 1))
    return df


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------
def gerar_clientes(rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    """Gera os clientes já com o perfil comportamental (coluna extra `perfil`).

    A coluna `perfil` NÃO vai para o banco: é o "gabarito" que guardamos à parte.
    Também injeta pequenas sujeiras reais (e-mail em caixa alta, cidade sem
    acento, canal nulo) para treino de limpeza.
    """
    n = cfg.N_CLIENTES
    nomes_perfis = list(PERFIS)
    contagens = {p: round(PERFIS[p]["prop"] * n) for p in nomes_perfis}
    contagens["ocasional"] += n - sum(contagens.values())  # ajusta o arredondamento

    perfis = np.repeat(list(contagens), list(contagens.values()))
    perfis = rng.permutation(perfis)  # embaralha: id não pode "entregar" o perfil

    # Estados e cidades
    siglas = list(cat.ESTADOS)
    p_estado = np.array([cat.ESTADOS[s][0] for s in siglas])
    p_estado = p_estado / p_estado.sum()

    # Canal de aquisição: VIP vem mais de indicação/orgânico; caçador de
    # marketplace/TikTok/Instagram.
    p_canal_base = np.array([0.30, 0.22, 0.14, 0.14, 0.10, 0.10])
    p_canal_perfil = {
        "vip": np.array([0.20, 0.18, 0.30, 0.24, 0.04, 0.04]),
        "cacador": np.array([0.30, 0.10, 0.04, 0.06, 0.25, 0.25]),
    }

    dominios = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br", "uol.com.br", "icloud.com"]
    p_dominio = [0.50, 0.15, 0.13, 0.09, 0.08, 0.05]

    registros = []
    emails_usados = set()
    for perfil in perfis:
        par = PERFIS[perfil]
        sigla = rng.choice(siglas, p=p_estado)
        cidades = cat.ESTADOS[sigla][2]
        p_cid = 0.55 ** np.arange(len(cidades))  # capital pesa mais
        cidade = rng.choice(cidades, p=p_cid / p_cid.sum())

        nome = f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"
        base = _sem_acento(nome).lower().replace(" ", rng.choice([".", "_", ""]))
        email = f"{base}@{rng.choice(dominios, p=p_dominio)}"
        while email in emails_usados:  # garante e-mail único
            email = f"{base}{rng.integers(1, 999)}@{rng.choice(dominios, p=p_dominio)}"
        emails_usados.add(email)

        p_can = p_canal_perfil.get(perfil, p_canal_base)
        registros.append({
            "nome": nome,
            # O domínio sorteado acima é descartado de propósito: o sorteio e a checagem de unicidade continuam
            # iguais (para a sequência aleatória e todos os números do projeto não mudarem), mas o e-mail gravado
            # usa example.com, domínio reservado, para que nenhum e-mail dos dados fictícios possa ser real.
            "email": email.split("@")[0] + "@example.com",
            "cidade": cidade,
            "estado": sigla,
            "cad_idx": int(rng.integers(par["cad"][0], par["cad"][1] + 1)),
            "canal_aquisicao": rng.choice(cat.CANAIS_AQUISICAO, p=p_can),
            "perfil": perfil,
        })

    df = pd.DataFrame(registros).sort_values("cad_idx", kind="stable").reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))
    df["data_cadastro"] = [_dia_para_data(i).strftime("%Y-%m-%d") for i in df["cad_idx"]]

    # --- Sujeiras intencionais (para treino de limpeza) ---
    m = len(df)
    sujo_email = rng.random(m)
    df.loc[sujo_email < 0.03, "email"] = df["email"].str.upper()          # 3% em CAIXA ALTA
    df.loc[(sujo_email >= 0.03) & (sujo_email < 0.05), "email"] = " " + df["email"] + " "  # 2% com espaços
    sujo_cidade = rng.random(m) < 0.04                                    # 4% sem acento/minúscula
    df.loc[sujo_cidade, "cidade"] = df.loc[sujo_cidade, "cidade"].map(lambda c: _sem_acento(c).lower())
    df.loc[rng.random(m) < 0.02, "canal_aquisicao"] = None                # 2% sem canal
    return df


# ---------------------------------------------------------------------------
# Pedidos e itens
# ---------------------------------------------------------------------------
def _pesos_produtos_base(produtos: pd.DataFrame, rng: np.random.Generator) -> dict:
    """Peso de cada produto por perfil = categoria x popularidade x preço."""
    popularidade = rng.lognormal(0, 0.5, len(produtos))  # alguns viram campeões de venda
    cats = produtos["categoria"].to_numpy()
    preco = produtos["preco"].to_numpy()
    pesos = {}
    for perfil, par in PERFIS.items():
        bruto = popularidade * (preco / 50.0) ** par["expo_preco"]
        w = np.zeros(len(produtos))
        for c, p_cat in zip(CATEGORIAS, PESO_CATEGORIA[perfil]):
            mascara = cats == c
            w[mascara] = p_cat * bruto[mascara] / bruto[mascara].sum()
        pesos[perfil] = w
    return pesos


def _fator_sazonal_produtos(produtos: pd.DataFrame) -> np.ndarray:
    """Matriz (dias x produtos) com o multiplicador sazonal de cada produto."""
    n_dias = cfg.JANELA_DIAS + 1
    fator = np.ones((n_dias, len(produtos)))
    for j, nome in enumerate(produtos["nome"]):
        if nome not in cat.PRODUTOS_SAZONAIS:
            continue
        (m1, d1), (m2, d2) = cat.PRODUTOS_SAZONAIS[nome]
        for i in range(n_dias):
            d = _dia_para_data(i)
            dentro = (d.month, d.day) >= (m1, d1) and (d.month, d.day) <= (m2, d2)
            fator[i, j] = 8.0 if dentro else 0.02  # item de campanha
    return fator


def _escolher_datas(rng, par, a, b, n, peso_dias, promo, cacador) -> list:
    """Sorteia as datas (índices de dia) dos pedidos de um cliente.

    O 1º pedido acontece logo após o cadastro; os demais seguem o calendário
    de demanda (mais pedidos em datas promocionais). Caçadores de cupom têm
    peso extra nos dias de campanha.
    """
    n = min(n, b - a + 1)
    primeiro = min(a + int(rng.geometric(0.4)) - 1, b)
    datas = {primeiro}
    if n > 1 and b > primeiro:
        dias = np.arange(primeiro, b + 1)
        w = peso_dias[dias] * (1 + 4 * promo[dias] if cacador else 1)
        extra = rng.choice(dias, size=min(n - 1, len(dias)), replace=False, p=w / w.sum())
        datas.update(int(x) for x in extra)
    # Garante um pedido "recente" para perfis que ainda estão ativos.
    if par["recente"] is not None:
        lo, hi = par["recente"]
        forcado = int(b - rng.integers(lo, hi + 1))
        datas.add(int(np.clip(forcado, primeiro, b)))
    return sorted(datas)


def _escolher_cupom(rng, perfil, par, idx, eh_primeiro, cal) -> str | None:
    """Decide qual cupom (se algum) o cliente usa neste pedido."""
    sazonal = cal["cupom"][idx]
    if perfil == "cacador":
        if rng.random() < par["cupom"]:
            if sazonal:
                return sazonal
            if eh_primeiro and rng.random() < 0.5:
                return "BEMVINDO"
            return "RELAMPAGO20" if rng.random() < 0.35 else "BOTO10"
        return None
    if sazonal and rng.random() < par["cupom"]:
        return sazonal
    if eh_primeiro and rng.random() < 0.5:
        return "BEMVINDO"
    return "BOTO10" if rng.random() < 0.06 else None


def _escolher_status(rng, idx) -> str:
    """Status do pedido: pedidos muito recentes ainda estão em andamento."""
    dias_ate_fim = cfg.JANELA_DIAS - idx
    if dias_ate_fim <= 3:
        return str(rng.choice(["pendente", "pago", "enviado"], p=[0.25, 0.4, 0.35]))
    if dias_ate_fim <= 10:
        return str(rng.choice(["enviado", "entregue"], p=[0.5, 0.5]))
    r = rng.random()
    if r < P_CANCELADO:
        return "cancelado"
    if r < P_CANCELADO + P_DEVOLVIDO:
        return "devolvido"
    return "entregue"


def gerar_pedidos_e_itens(rng, clientes: pd.DataFrame, produtos: pd.DataFrame, cal: dict):
    """Simula todos os pedidos e itens a partir do perfil de cada cliente."""
    pesos_base = _pesos_produtos_base(produtos, rng)
    saz = _fator_sazonal_produtos(produtos)
    precos = produtos["preco"].to_numpy()
    cats = produtos["categoria"].to_numpy()
    ids_prod = produtos["id"].to_numpy()
    fim = cfg.JANELA_DIAS

    pedidos, itens = [], []
    for cli in clientes.itertuples(index=False):
        par = PERFIS[cli.perfil]
        a = cli.cad_idx
        b = fim if par["parada"] is None else max(a + 20, fim - int(rng.integers(*par["parada"])))
        n = max(par["minimo"], int(rng.poisson(par["media"])))
        datas = _escolher_datas(rng, par, a, b, n, cal["peso"], cal["promo"], cli.perfil == "cacador")

        for k, idx in enumerate(datas):
            data = _dia_para_data(idx)
            cupom = _escolher_cupom(rng, cli.perfil, par, idx, k == 0, cal)

            # --- itens do pedido ---
            w = pesos_base[cli.perfil] * saz[idx]
            qtd_itens = min(1 + int(rng.poisson(par["itens"])), 5)
            escolhidos = rng.choice(len(produtos), size=qtd_itens, replace=False, p=w / w.sum())
            subtotal = 0.0
            linhas = []
            for j in escolhidos:
                # Grãos e itens baratos podem ser comprados em maior quantidade.
                if cats[j] == "Grãos":
                    p_q = [0.45, 0.30, 0.25] if cli.perfil == "vip" else [0.70, 0.20, 0.10]
                    qtd = int(rng.choice([1, 2, 3], p=p_q))
                elif cats[j] == "Acessórios" and precos[j] < 60:
                    qtd = int(rng.choice([1, 2], p=[0.7, 0.3]))
                else:
                    qtd = 1
                preco_un = precos[j]
                if data < cfg.DATA_REAJUSTE:  # antes do reajuste de preços
                    preco_un = round(preco_un / cfg.FATOR_REAJUSTE, 2)
                subtotal += qtd * preco_un
                linhas.append((int(ids_prod[j]), qtd, float(preco_un)))

            desconto = round(subtotal * cat.CUPONS[cupom], 2) if cupom else 0.0
            if data < cfg.DATA_LANCAMENTO_APP:
                canal = rng.choice(["site", "whatsapp", "marketplace"], p=[0.65, 0.18, 0.17])
            else:
                canal = rng.choice(cat.CANAIS_PEDIDO, p=[0.50, 0.28, 0.11, 0.11])

            pedidos.append({
                "cliente_id": int(cli.id),
                "data_pedido": data.strftime("%Y-%m-%d"),
                "status": _escolher_status(rng, idx),
                "cupom_usado": cupom,
                "desconto": desconto,
                "valor_total": round(subtotal - desconto, 2),
                "canal": str(canal),
                "_linhas": linhas,
            })

    # Numera os pedidos em ordem cronológica e expande os itens.
    pedidos.sort(key=lambda p: (p["data_pedido"], p["cliente_id"]))
    linhas_itens = []
    for i, p in enumerate(pedidos, start=1):
        p["id"] = i
        for prod_id, qtd, preco_un in p.pop("_linhas"):
            linhas_itens.append({"pedido_id": i, "produto_id": prod_id,
                                 "quantidade": qtd, "preco_unitario": preco_un})

    df_ped = pd.DataFrame(pedidos)[["id", "cliente_id", "data_pedido", "status",
                                    "cupom_usado", "desconto", "valor_total", "canal"]]
    df_it = pd.DataFrame(linhas_itens)
    df_it.insert(0, "id", range(1, len(df_it) + 1))
    return df_ped, df_it


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------
def gerar_tudo(seed: int = cfg.SEED) -> dict:
    """Gera as 4 tabelas + o gabarito de perfis. Mesma seed => mesmos dados."""
    rng = np.random.default_rng(seed)
    Faker.seed(seed)
    fake = Faker("pt_BR")

    cal = montar_calendario()
    produtos = gerar_produtos()
    clientes_int = gerar_clientes(rng, fake)
    pedidos, itens = gerar_pedidos_e_itens(rng, clientes_int, produtos, cal)

    gabarito = clientes_int[["id", "perfil"]].rename(columns={"id": "cliente_id"})
    colunas = ["id", "nome", "email", "cidade", "estado", "data_cadastro", "canal_aquisicao"]
    return {
        "clientes": clientes_int[colunas],
        "produtos": produtos,
        "pedidos": pedidos,
        "itens_pedido": itens,
        "gabarito": gabarito,
    }
