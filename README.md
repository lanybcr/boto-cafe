# ☕ Boto Café · Segmentação de clientes com RFM

Projeto de portfólio de **Analytics Engineering**: do banco de dados sintético até um dashboard e um kit de Power BI,
passando por análise RFM e estratégia de cupons.

> **Os dados são fictícios.** O Boto Café é uma loja de cafés especiais inventada, com clientes em todo o Brasil
> (mais concentrados no Norte e Nordeste). Os padrões foram gerados para o estudo e não representam um negócio real.

## A pergunta de negócio

*Como saber quem vale investir, quem está sumindo e quanto podemos gastar para trazer essas pessoas de volta?*

## O que tem aqui

| Fase | Entrega | Onde |
|---|---|---|
| 1 | Banco sintético (SQLite + CSVs) com sujeira controlada e validação de integridade | `src/gerador.py`, `data/loja.db` |
| 2 | Análise RFM: limpeza, métricas, notas, 9 segmentos | `src/rfm.py`, `notebooks/02_analise_rfm.ipynb` |
| 3 | Estratégia de cupons por segmento, com simulação de lucro e listas de campanha | `src/cupons.py`, `data/campanhas/` |
| 4 | Dashboard interativo (Streamlit + Plotly) | `app/` |
| 5 | Kit Power BI: modelo estrela, medidas DAX, wireframes, tema e storytelling | `src/powerbi.py`, `powerbi/`, `data/powerbi/` |
| 6 | Dashboard em HTML: um único arquivo, abre com duplo clique, sem servidor | `src/html_dashboard.py`, `dashboard/index.html` |

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
# Fase 1: gerar o banco e validar a integridade
.venv/Scripts/python -m src.gerar_dados

# Fases 2 e 3: abrir os notebooks (o 02 grava data/rfm_clientes.csv; o 03 grava data/campanhas/)
.venv/Scripts/jupyter lab notebooks/

# Fase 4: dashboard
.venv/Scripts/streamlit run app/streamlit_app.py

# Fase 5: gerar os CSVs do Power BI
.venv/Scripts/python -m src.powerbi

# Fase 6: gerar o dashboard em HTML (depois é só abrir dashboard/index.html no navegador)
.venv/Scripts/python -m src.html_dashboard
```

A geração é determinística (`SEED = 42`): rodar de novo produz os mesmos dados.
Para montar o painel no Power BI Desktop, siga `powerbi/01_guia_passo_a_passo.md` e `powerbi/03_wireframes.md`.

## Estrutura

```
boto-cafe/
├── src/          # lógica reutilizável (gerador, banco, validação, rfm, cupons, powerbi)
├── notebooks/    # 01 geração · 02 análise RFM · 03 estratégia de cupons
├── app/          # dashboard Streamlit (dados, gráficos, página)
├── dashboard/    # dashboard HTML: template.html (molde) e index.html (gerado)
├── powerbi/      # guia, medidas DAX, wireframes, tema, storytelling
├── data/         # raw/, loja.db, rfm_clientes.csv, campanhas/, powerbi/
└── requirements.txt
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

## Decisões de projeto

- **Pedido válido** = status pago, enviado ou entregue. Cancelados e devolvidos ficam fora da receita e do RFM.
- **O RFM não enxerga o gabarito.** O gerador grava os perfis "verdadeiros" dos clientes em um arquivo separado
  (`data/gabarito_perfis.csv`) só para conferir se a segmentação encontra o que foi plantado. A análise nunca lê esse arquivo.
- **Segmento é uma foto** de todo o histórico. Não muda quando você filtra o período no dashboard.
- **Cupom só compensa se `desconto < incremental × margem`.** *Incremental* é a fatia de pedidos que só acontece por causa
  da ação. Campeões, por exemplo, ganham brinde em vez de desconto, porque já comprariam de qualquer forma.
- **Margem real calculada do custo dos produtos** (cerca de 48,4%), não chutada.
- **Receita por item com o desconto rateado**, para que a soma dos itens bata com o valor do pedido.
- **Modelo estrela no Power BI**, sem ligar fato com fato. Por isso receita, pedidos e ticket usam `fato_itens`.
- **CSVs no padrão pt-BR** (`;`, vírgula decimal, UTF-8 com BOM, datas ISO).
- **19 clientes nunca compraram** e entram como "Sem compra válida" no Power BI, em vez de sumirem do modelo.

## Principais achados

Todos medidos sobre os dados fictícios:

- **Receita válida:** R$ 4,15 milhões, 14.860 pedidos, ticket médio de R$ 279.
- **Dois grupos carregam a loja:** Campeões (44,4%) e Clientes Fiéis (33,6%) geram **78% da receita**.
- **Concentração:** os 10% maiores clientes geram **52,2%** da receita.
- **Dinheiro parado:** 600 clientes (30,3%) estão em risco (Precisam de Atenção + Prestes a Dar Churn + Hibernando)
  e já gastaram R$ 583 mil na vida. Só Prestes a Dar Churn ainda responde por 9,9% da receita.
- **Cancelamento e devolução:** 6,2% dos pedidos.
- **Cupons:** 26,5% dos pedidos válidos usaram cupom.
- **Simulação de campanha:** com as premissas do projeto, a estratégia por segmento rende cerca de R$ 14 mil de lucro
  líquido, e o maior retorno vem de **Prestes a Dar Churn** (cerca de R$ 4,4 mil), onde ainda há cliente para recuperar.

## Limitações

- **Dados fictícios:** a conclusão serve para mostrar o método, não para decidir um negócio real.
- **Taxas de resposta e % incremental dos cupons são hipóteses** (`PREMISSAS` em `src/cupons.py`). Em um caso real,
  um teste A/B é o que confirma.
- **Base de cerca de 2 anos:** comparação ano contra ano só vale a partir do 13º mês.
- **Power BI:** o painel foi montado e conferido no Power BI Desktop (cartões, filtro por estado e totais batem com
  o HTML e o pandas). Na montagem, duas medidas foram corrigidas (`% Receita do Segmento`, por causa da ordenação
  do segmento, e `Desconto de Equilíbrio`). O tema JSON não foi confirmado.
- **Margem do simulador:** o Power BI usa a margem sobre a receita já com desconto (46,8%), e a Fase 3 usa a
  margem sobre o preço de tabela (48,4%). Por isso o desconto de equilíbrio com 50% de incremental é 23,4%, e não 24,2%.
- **Correlação não é causa:** cliente em risco é um sinal para agir, não um cliente perdido.

## Tecnologias

Python 3.12 · pandas · NumPy · Faker · SQLite · Plotly · Streamlit · Jupyter · Power BI (DAX e Power Query)
