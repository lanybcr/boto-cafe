"""Catálogo da Boto Café: produtos, geografia, cupons e canais.

São dados "de cadastro" (a regra do negócio), separados do código que
gera o comportamento dos clientes.
"""

# (nome, categoria, preço atual, custo)
PRODUTOS = [
    # --- Grãos (14) ---
    ("Cerrado Mineiro Torra Média 250g", "Grãos", 42.90, 19.00),
    ("Matas de Minas Torra Clara 250g", "Grãos", 46.90, 21.00),
    ("Sul de Minas Torra Média 250g", "Grãos", 39.90, 18.00),
    ("Mogiana Torra Escura 250g", "Grãos", 37.90, 17.00),
    ("Cerrado Mineiro Torra Média 1kg", "Grãos", 139.90, 66.00),
    ("Sul de Minas Torra Média 1kg", "Grãos", 129.90, 62.00),
    ("Conilon Capixaba Robusta 250g", "Grãos", 33.90, 15.00),
    ("Microlote Bourbon Amarelo 250g", "Grãos", 79.90, 36.00),
    ("Microlote Natural Fermentação Controlada 250g", "Grãos", 89.90, 42.00),
    ("Robusta Amazônico de Rondônia 250g", "Grãos", 54.90, 25.00),
    ("Blend da Casa Boto 250g", "Grãos", 35.90, 15.00),
    ("Café Descafeinado Suave 250g", "Grãos", 44.90, 21.00),
    ("Orgânico Chapada Diamantina 250g", "Grãos", 52.90, 24.00),
    ("Moagem Grossa para Cold Brew 250g", "Grãos", 40.90, 18.00),
    # --- Cafeteiras (7) ---
    ("Prensa Francesa 600ml", "Cafeteiras", 119.90, 62.00),
    ("Coador V60 de Cerâmica", "Cafeteiras", 149.90, 80.00),
    ("Aeropress Clássica", "Cafeteiras", 259.90, 150.00),
    ("Cafeteira Italiana Moka 3 xícaras", "Cafeteiras", 99.90, 52.00),
    ("Cafeteira Elétrica Programável", "Cafeteiras", 349.90, 215.00),
    ("Cafeteira Cold Brew 1L", "Cafeteiras", 139.90, 72.00),
    ("Máquina de Espresso Manual Compacta", "Cafeteiras", 899.90, 600.00),
    # --- Acessórios (10) ---
    ("Moedor Manual de Cerâmica", "Acessórios", 189.90, 95.00),
    ("Moedor Elétrico de Rebarbas", "Acessórios", 429.90, 270.00),
    ("Filtros de Papel V60 (100 un)", "Acessórios", 29.90, 12.00),
    ("Filtros de Papel nº 103 (30 un)", "Acessórios", 14.90, 6.00),
    ("Chaleira Bico de Ganso 1L", "Acessórios", 229.90, 125.00),
    ("Balança Digital com Timer", "Acessórios", 169.90, 90.00),
    ("Caneca de Cerâmica Boto", "Acessórios", 49.90, 20.00),
    ("Xícaras de Espresso (par)", "Acessórios", 69.90, 30.00),
    ("Garrafa Térmica 350ml", "Acessórios", 89.90, 42.00),
    ("Termômetro para Café", "Acessórios", 59.90, 25.00),
    # --- Kits presente (5) ---
    ("Kit Iniciante (V60 + café 250g)", "Kits Presente", 189.90, 100.00),
    ("Kit Degustação 4 Origens", "Kits Presente", 159.90, 75.00),
    ("Kit Presente Boto Café", "Kits Presente", 249.90, 125.00),
    ("Kit Dia dos Pais Barista", "Kits Presente", 299.90, 160.00),
    ("Kit Natal Café & Caneca", "Kits Presente", 219.90, 110.00),
    # --- Assinaturas (4) ---
    ("Assinatura Mensal 250g", "Assinaturas", 39.90, 18.00),
    ("Assinatura Mensal 500g", "Assinaturas", 74.90, 35.00),
    ("Assinatura Trimestral 250g (3 envios)", "Assinaturas", 109.90, 52.00),
    ("Assinatura Semestral 500g (6 envios)", "Assinaturas", 399.90, 195.00),
]

# Produtos sazonais: nome -> (mês/dia inicial, mês/dia final). Fora da janela
# o produto praticamente não vende (é um item de campanha).
PRODUTOS_SAZONAIS = {
    "Kit Dia dos Pais Barista": ((7, 20), (8, 15)),
    "Kit Natal Café & Caneca": ((11, 20), (12, 24)),
}

# estado -> (peso na população de clientes, região, cidades da mais para a menos populosa)
ESTADOS = {
    # Norte
    "PA": (8.0, "Norte", ["Belém", "Ananindeua", "Santarém", "Marabá", "Castanhal"]),
    "AM": (7.0, "Norte", ["Manaus", "Parintins", "Itacoatiara"]),
    "AP": (1.0, "Norte", ["Macapá", "Santana"]),
    "RR": (0.5, "Norte", ["Boa Vista"]),
    "RO": (1.0, "Norte", ["Porto Velho", "Ji-Paraná"]),
    "AC": (0.5, "Norte", ["Rio Branco"]),
    "TO": (1.0, "Norte", ["Palmas", "Araguaína"]),
    # Nordeste
    "BA": (8.0, "Nordeste", ["Salvador", "Feira de Santana", "Vitória da Conquista", "Ilhéus", "Lauro de Freitas"]),
    "PE": (7.0, "Nordeste", ["Recife", "Olinda", "Caruaru", "Petrolina", "Jaboatão dos Guararapes"]),
    "CE": (7.0, "Nordeste", ["Fortaleza", "Sobral", "Juazeiro do Norte", "Caucaia"]),
    "MA": (4.0, "Nordeste", ["São Luís", "Imperatriz", "Caxias"]),
    "PI": (2.5, "Nordeste", ["Teresina", "Parnaíba"]),
    "RN": (2.5, "Nordeste", ["Natal", "Mossoró", "Parnamirim"]),
    "PB": (2.5, "Nordeste", ["João Pessoa", "Campina Grande"]),
    "AL": (1.5, "Nordeste", ["Maceió", "Arapiraca"]),
    "SE": (1.5, "Nordeste", ["Aracaju", "Nossa Senhora do Socorro"]),
    # Sudeste
    "SP": (15.0, "Sudeste", ["São Paulo", "Campinas", "Santos", "Ribeirão Preto", "Sorocaba"]),
    "RJ": (7.0, "Sudeste", ["Rio de Janeiro", "Niterói", "Petrópolis"]),
    "MG": (7.0, "Sudeste", ["Belo Horizonte", "Uberlândia", "Juiz de Fora"]),
    # Sul
    "PR": (3.0, "Sul", ["Curitiba", "Londrina"]),
    "RS": (3.0, "Sul", ["Porto Alegre", "Caxias do Sul"]),
    "SC": (2.0, "Sul", ["Florianópolis", "Joinville"]),
    # Centro-Oeste
    "DF": (3.0, "Centro-Oeste", ["Brasília"]),
    "GO": (2.5, "Centro-Oeste", ["Goiânia"]),
    "MT": (1.0, "Centro-Oeste", ["Cuiabá"]),
    "MS": (0.5, "Centro-Oeste", ["Campo Grande"]),
}

# código do cupom -> % de desconto sobre o subtotal
CUPONS = {
    "BOTO10": 0.10,        # cupom genérico (newsletter/Instagram)
    "BEMVINDO": 0.10,      # primeira compra
    "NATAL15": 0.15,       # campanha de Natal
    "PAIS12": 0.12,        # campanha Dia dos Pais
    "BLACK25": 0.25,       # Black Friday
    "RELAMPAGO20": 0.20,   # ações relâmpago divulgadas em grupos de cupom
}

CANAIS_AQUISICAO = ["Instagram", "Google", "Indicação", "Orgânico", "Marketplace", "TikTok"]
CANAIS_PEDIDO = ["site", "app", "whatsapp", "marketplace"]
STATUS_PEDIDO = ["pendente", "pago", "enviado", "entregue", "cancelado", "devolvido"]
