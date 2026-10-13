# ☕ Boto Café · Segmentação de clientes com RFM

[![CI](https://github.com/lanybcr/boto-cafe/actions/workflows/ci.yml/badge.svg)](https://github.com/lanybcr/boto-cafe/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Licença](https://img.shields.io/badge/licença-MIT-green)

Projeto de portfólio de **Analytics Engineering**: do banco de dados sintético até três dashboards (HTML, Streamlit e Power BI),
passando por análise RFM em Python **e em SQL**, estratégia de cupons e testes automáticos.

> **Os dados são fictícios.** O Boto Café é uma loja de cafés especiais inventada, com clientes em todo o Brasil
> (mais concentrados no Norte e Nordeste). Os padrões foram gerados para o estudo e não representam um negócio real.

[![Dashboard](dashboard/capa.png)](https://lanybcr.github.io/boto-cafe/dashboard/)

**▶ [Abrir o dashboard (HTML, direto no navegador)](https://lanybcr.github.io/boto-cafe/dashboard/)** ·
[Painel no Power BI (capturas)](#dashboard-no-power-bi) ·
[Dicionário de dados](docs/dicionario_de_dados.md)

## A pergunta de negócio

*Como saber quem vale investir, quem está sumindo e quanto podemos gastar para trazer essas pessoas de volta?*

**A resposta em 3 linhas** (sobre os dados fictícios):
1. Dois grupos, Campeões e Clientes Fiéis, geram **78% da receita**; os 10% maiores clientes geram **52%**.
2. **600 clientes (30%) estão em risco** e já gastaram **R$ 583 mil**: é dinheiro parado em quem está sumindo.
3. Um cupom só compensa se **desconto < incremental × margem**; com as premissas do projeto, a estratégia por segmento rende cerca de R$ 14 mil de lucro líquido.

## Qual dashboard usar?

O mesmo conteúdo foi construído três vezes, de propósito, para mostrar três jeitos de entregar dados:

| | HTML | Streamlit | Power BI |
|---|---|---|---|
| **Para quem** | Qualquer pessoa, só com o link | Quem usa Python | Quem trabalha com BI na empresa |
| **Precisa de** | Navegador | Python instalado | Power BI Desktop |
| **Funciona offline** | Sim (um único arquivo) | Sim, rodando local | Sim, com o `.pbix` |
| **Ponto forte** | Compartilhar e abrir em qualquer lugar, inclusive no celular | Simulador de cupom e lógica em Python | Modelo estrela, medidas DAX, padrão de mercado |
| **Onde** | `dashboard/` | `app/` | `powerbi/` |

## O que tem aqui

| Fase | Entrega | Onde |
|---|---|---|
| 1 | Banco sintético (SQLite + CSVs) com sujeira controlada e validação de integridade | `src/gerador.py`, `data/loja.db` |
| 2 | Análise RFM: limpeza, métricas, notas, 9 segmentos | `src/rfm.py`, `notebooks/02_analise_rfm.ipynb` |
| 3 | Estratégia de cupons por segmento, com simulação de lucro e listas de campanha | `src/cupons.py`, `data/campanhas/` |
| 4 | Dashboard interativo (Streamlit + Plotly) | `app/` |
| 5 | Modelo estrela, medidas DAX, wireframes, tema e storytelling para o Power BI (painel montado e conferido) | `src/powerbi.py`, `powerbi/`, `data/powerbi/` |
| 6 | Dashboard em HTML: um único arquivo, abre com duplo clique, sem servidor | `src/html_dashboard.py`, `dashboard/index.html` |
| 7 | Qualidade: RFM em SQL (views), testes automáticos, CI e dicionário de dados | `sql/`, `tests/`, `.github/`, `docs/` |

## Dashboard no Power BI

Arquivo: `powerbi/boto-cafe.pbix`. Quatro páginas, uma pergunta por página.

| Página | Pergunta | Captura |
|---|---|---|
| Visão Geral | Como está o negócio? | ![Visão Geral](powerbi/capturas/01_visao_geral.png) |
| RFM | Quem são os nossos clientes? | ![RFM](powerbi/capturas/02_rfm.png) |
| Clientes VIP | Quem sustenta a receita? | ![Clientes VIP](powerbi/capturas/03_clientes_vip.png) |
| Churn e Ações | Quem ainda dá para recuperar? | ![Churn e Ações](powerbi/capturas/04_churn_e_acoes.png) |

## Como rodar

Requer Python 3.12. Na raiz do projeto:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

(no Linux/macOS, troque `.venv/Scripts` por `.venv/bin`)

```bash
# Fase 1: gerar o banco (com as views SQL de RFM) e validar a integridade
.venv/Scripts/python -m src.gerar_dados

# Fases 2 e 3: abrir os notebooks (o 02 grava data/rfm_clientes.csv; o 03 grava data/campanhas/)
.venv/Scripts/jupyter lab notebooks/

# Fase 4: dashboard Streamlit
.venv/Scripts/streamlit run app/streamlit_app.py

# Fase 5: gerar os CSVs do Power BI
.venv/Scripts/python -m src.powerbi

# Fase 6: gerar o dashboard em HTML (depois é só abrir dashboard/index.html no navegador)
.venv/Scripts/python -m src.html_dashboard

# Fase 7: testes
.venv/Scripts/pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest
```

A geração é determinística (`SEED = 42` e versões fixadas em `requirements.txt`): rodar de novo produz os mesmos dados.
Para montar o painel no Power BI Desktop, siga `powerbi/01_guia_passo_a_passo.md` e `powerbi/03_wireframes.md`.

## Estrutura

```
boto-cafe/
├── src/          # lógica reutilizável (gerador, banco, validação, rfm, sql_rfm, cupons, powerbi, html_dashboard)
├── sql/          # RFM em SQL: views encadeadas dentro do banco
├── tests/        # testes automáticos (pytest)
├── notebooks/    # 01 geração · 02 análise RFM · 03 estratégia de cupons
├── app/          # dashboard Streamlit (dados, gráficos, página)
├── dashboard/    # dashboard HTML: template.html (molde), index.html (gerado) e capa.png
├── powerbi/      # painel .pbix, guia, medidas DAX, wireframes, tema, storytelling, capturas
├── docs/         # dicionário de dados
├── data/         # raw/, loja.db, rfm_clientes.csv, campanhas/, powerbi/
├── .github/      # CI (GitHub Actions)
└── requirements.txt, requirements-dev.txt, LICENSE
```

## Como o RFM funciona

| Letra | Mede | Como calculamos |
|---|---|---|
| **R**ecência | Há quanto tempo comprou | Dias desde a última compra válida (data de referência: 08/10/2026) |
| **F**requência | Quantas vezes comprou | Número de pedidos válidos |
| **M**onetário | Quanto gastou | Soma do valor pago (já com desconto) |

Cada métrica vira uma nota de 1 a 5 por quintis, e a combinação das três cai em um de 9 segmentos:
Campeões, Clientes Fiéis, Potenciais Fiéis, Novos, Promissores, Precisam de Atenção, Prestes a Dar Churn,
Hibernando e Perdidos. As regras estão em `REGRAS_SEGMENTOS` (`src/rfm.py`), avaliadas em ordem.

O mesmo cálculo existe em **SQL** (`sql/01_vw_rfm.sql`), e um teste confirma que o resultado é **idêntico** ao do pandas
(1.981 clientes, mesmas notas e mesmos segmentos).

## Decisões de projeto

- **Pedido válido** = status pago, enviado ou entregue. Cancelados, devolvidos e pendentes ficam fora da receita e do RFM.
- **O RFM não enxerga o gabarito.** O gerador grava os perfis "verdadeiros" dos clientes em um arquivo separado
  (`data/gabarito_perfis.csv`) só para conferir se a segmentação encontra o que foi plantado. A análise nunca lê esse arquivo.
- **Segmento é uma foto** de todo o histórico. Não muda quando você filtra o período no dashboard.
- **Cupom só compensa se `desconto < incremental × margem`.** *Incremental* é a fatia de pedidos que só acontece por causa
  da ação. Campeões, por exemplo, ganham brinde em vez de desconto, porque já comprariam de qualquer forma.
- **Margem real calculada do custo dos produtos**, não chutada. Há duas leituras, e as duas aparecem no projeto: sobre as vendas
  **antes do desconto** (48,4%, usada na simulação da Fase 3) e sobre a receita **já com desconto** (46,8%, usada no Power BI).
  Por isso o desconto de equilíbrio com 50% de incremental é 24,2% na Fase 3 e 23,4% no Power BI.
- **Receita por item com o desconto rateado**, para que a soma dos itens bata com o valor do pedido.
- **Modelo estrela no Power BI**, sem ligar fato com fato. Por isso receita, pedidos e ticket usam `fato_itens`.
- **CSVs no padrão pt-BR** (`;`, vírgula decimal, UTF-8 com BOM, datas ISO).
- **19 clientes nunca compraram** e entram como "Sem compra válida" no Power BI, em vez de sumirem do modelo.
- **E-mails fictícios em `example.com`**, domínio reservado, para que nenhum endereço dos dados possa ser de uma pessoa real.

## Principais achados

> Atenção: os dados são sintéticos, com perfis de cliente plantados no gerador. Os números abaixo mostram **como o método
> lê os dados**, não uma conclusão sobre um negócio real.

Todos medidos sobre os dados fictícios:

- **Receita válida:** R$ 4,15 milhões, 14.860 pedidos, ticket médio de R$ 279.
- **Dois grupos carregam a loja:** Campeões (44,4%) e Clientes Fiéis (33,6%) geram **78% da receita**.
- **Concentração:** os 10% maiores clientes geram **52,2%** da receita.
- **Dinheiro parado:** 600 clientes (30,3%) estão em risco (Precisam de Atenção + Prestes a Dar Churn + Hibernando)
  e já gastaram R$ 583 mil na vida. Só Prestes a Dar Churn ainda responde por 9,9% da receita.
- **Cancelamento e devolução:** 6,2% dos pedidos.
- **Cupons:** 26,5% dos pedidos válidos usaram cupom.
- **Simulação de campanha:** com as premissas do projeto, a estratégia por segmento rende cerca de R$ 14 mil de lucro
  líquido (R$ 11,8 mil de custo, ROI geral de 1,2). O **maior lucro em reais** vem de **Prestes a Dar Churn** (cerca de R$ 4,4 mil),
  onde há mais cliente para recuperar. O **maior retorno por real gasto** (ROI ≈ 1,7) fica em Novos, Promissores, Precisam de
  Atenção e Hibernando; em Prestes a Dar Churn o ROI é ≈ 1,0 porque o desconto (20%) é o maior.

## Qualidade

- **Validação de integridade** (Fase 1): chaves, datas, totais dos pedidos batendo com os itens, regras do cupom.
- **16 testes automáticos** (`tests/`): integridade, volumes, e-mails fictícios, receita dos itens igual à dos pedidos,
  notas de 1 a 5 equilibradas, regras de segmento e equivalência **SQL × pandas**.
- **CI no GitHub Actions** (`.github/workflows/ci.yml`): a cada push, regenera o banco do zero e roda os testes.
- **Conferência cruzada** entre os três dashboards: mesmos totais (R$ 4.149.292, 1.981 compradores, 30,3% em risco) e mesmo resultado ao filtrar um estado.

## Limitações

- **Dados fictícios:** a conclusão serve para mostrar o método, não para decidir um negócio real.
- **Taxas de resposta e % incremental dos cupons são hipóteses** (`PREMISSAS` em `src/cupons.py`). Em um caso real,
  um teste A/B é o que confirma. O lucro da simulação depende inteiramente delas.
- **Base de cerca de 2 anos:** comparação ano contra ano só vale a partir do 13º mês. O último mês (out/2026) é parcial (7 dias).
- **Power BI:** o painel foi montado e conferido no Power BI Desktop (cartões, filtro por estado e totais batem com
  o HTML e o pandas). Na montagem, duas medidas foram corrigidas (`% Receita do Segmento`, por causa da ordenação
  do segmento, e `Desconto de Equilíbrio`). O tema JSON (`boto_cafe_tema.json`) não foi validado no Desktop; o painel usa formatação manual.
- **Dashboard HTML:** testado no Chrome e no navegador do app (desktop e celular). Não foi testado em Firefox nem Safari.
  O visual é só em tema claro.
- **Correlação não é causa:** cliente em risco é um sinal para agir, não um cliente perdido.

## Autoria e licença

Projeto de portfólio de **Alany Cruz** ([GitHub](https://github.com/lanybcr)).
O código é licenciado sob a [MIT](LICENSE). Os dados são fictícios e podem ser reutilizados livremente.

## Tecnologias

Python 3.12 · pandas · NumPy · Faker · SQLite e SQL (views, funções de janela) · Plotly · Streamlit · Jupyter · Power BI (DAX e Power Query) · pytest · GitHub Actions
