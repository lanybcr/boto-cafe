# Dicionário de dados · Boto Café

Todos os dados são **fictícios**. Este documento descreve cada tabela, o que cada coluna significa e as regras de negócio por trás.
Há duas camadas:

| Camada | Onde | Para quê |
|---|---|---|
| **Bruta** | `data/loja.db` (SQLite) e `data/raw/*.csv` | O que "veio do sistema da loja", incluindo sujeira controlada |
| **Modelo estrela** | `data/powerbi/*.csv` | Tabelas limpas, com RFM e chaves prontas para BI |
| **Views SQL** | dentro de `data/loja.db` (`sql/01_vw_rfm.sql`) | O RFM calculado em SQL, equivalente ao do Python |

Convenções: datas em `AAAA-MM-DD`; valores em R$; CSVs do Power BI com `;` como separador, vírgula decimal e UTF-8 com BOM.

## Regras de negócio

| Regra | Definição |
|---|---|
| **Pedido válido** | `status` em `pago`, `enviado` ou `entregue`. `cancelado`, `devolvido` e `pendente` ficam fora da receita e do RFM. |
| **Receita** | Valor **pago** (já com desconto) dos pedidos válidos. |
| **Data de referência** | Dia seguinte à última compra válida do banco (08/10/2026). A recência mínima é 1 dia. |
| **Recência (R)** | Dias entre a data de referência e a última compra válida do cliente. |
| **Frequência (F)** | Número de pedidos válidos. |
| **Monetário (M)** | Soma do valor pago nos pedidos válidos. |
| **Notas R, F, M** | De 1 (pior) a 5 (melhor), por quintis. Empates são desfeitos pela ordem do `cliente_id`. Na recência a escala é invertida (menos dias = nota maior). |
| **Segmento** | 9 segmentos, avaliados em ordem (a primeira regra que bater vence). Regras em `REGRAS_SEGMENTOS` (`src/rfm.py`). |
| **Em risco** | Segmento *Precisam de Atenção*, *Prestes a Dar Churn* ou *Hibernando*. |
| **Sem compra válida** | Cliente cadastrado que nunca teve pedido válido (19 casos). Fica no modelo, sem R, F, M. |
| **Segmento é uma foto** | Calculado sobre todo o histórico. Não muda quando se filtra o período. |

## Camada bruta (SQLite)

### `clientes` (2.000 linhas)
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | inteiro | Chave primária |
| `nome` | texto | Nome fictício |
| `email` | texto | Sempre `@example.com` (domínio reservado). Pode vir com espaços ou em maiúsculas (sujeira controlada); a limpeza faz `strip` e minúsculas |
| `cidade` | texto | Pode vir sem acento ou em minúsculas (ex.: `sao paulo`); a limpeza restaura a grafia oficial |
| `estado` | texto | UF |
| `data_cadastro` | texto (data) | Dia do cadastro |
| `canal_aquisicao` | texto | `Google`, `Instagram`, `Marketplace`, `TikTok`, `Indicação`, `Orgânico`. Nulo vira `Não informado` na limpeza |

### `produtos` (40 linhas)
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | inteiro | Chave primária |
| `nome` | texto | Nome do produto |
| `categoria` | texto | `Grãos`, `Cafeteiras`, `Acessórios`, `Kits Presente`, `Assinaturas` |
| `preco` | decimal | Preço de tabela (> 0) |
| `custo` | decimal | Custo do produto (> 0 e menor que o preço) |

### `pedidos` (15.882 linhas)
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | inteiro | Chave primária |
| `cliente_id` | inteiro | Chave estrangeira para `clientes.id` |
| `data_pedido` | texto (data) | Nunca anterior ao cadastro do cliente |
| `status` | texto | `pago`, `enviado`, `entregue`, `pendente`, `cancelado`, `devolvido` |
| `cupom_usado` | texto | `BEMVINDO`, `BOTO10`, `RELAMPAGO20`, `BLACK25`, `NATAL15`, `PAIS12`, ou nulo (sem cupom) |
| `desconto` | decimal | Valor em R$ descontado (zero quando não há cupom) |
| `valor_total` | decimal | Valor pago = soma dos itens − `desconto` |
| `canal` | texto | Canal da venda: `site`, `app`, `marketplace`, `whatsapp` |

### `itens_pedido` (32.813 linhas)
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | inteiro | Chave primária |
| `pedido_id` | inteiro | Chave estrangeira para `pedidos.id` |
| `produto_id` | inteiro | Chave estrangeira para `produtos.id` |
| `quantidade` | inteiro | Maior que zero |
| `preco_unitario` | decimal | Preço praticado no pedido (pode diferir do preço de tabela, por exemplo após reajuste) |

### Views de RFM em SQL
`vw_pedidos_validos` → `vw_data_referencia` → `vw_rfm_metricas` → `vw_rfm_scores` → `vw_rfm_segmentos`.
A última tem uma linha por cliente com compra válida (1.981) e as colunas `recencia`, `frequencia`, `monetario`, `R`, `F`, `M`, `score_rfm`, `score_soma` e `segmento`.

## Modelo estrela (`data/powerbi/`)

### `dim_clientes` (2.000 linhas · uma por cliente)
| Coluna | Descrição |
|---|---|
| `cliente_id` | Chave |
| `nome`, `email`, `cidade`, `estado` | Dados do cliente, já limpos |
| `regiao` | Norte, Nordeste, Centro-Oeste, Sudeste ou Sul (derivada do estado) |
| `canal_aquisicao` | Como o cliente chegou (nulo vira `Não informado`) |
| `data_cadastro`, `primeira_compra`, `ultima_compra` | Datas (as duas últimas ficam vazias para quem nunca comprou) |
| `recencia`, `frequencia`, `monetario`, `ticket_medio` | R, F, M e valor médio por pedido (vazios para *Sem compra válida*) |
| `R`, `F`, `M` | Notas de 1 a 5 |
| `score_rfm` | Texto com as 3 notas (ex.: `545`). É texto de propósito: não é um número |
| `score_soma` | Soma das 3 notas (3 a 15) |
| `segmento` | Um dos 9 segmentos, ou `Sem compra válida` |
| `segmento_ordem` | 1 a 9 na ordem do "melhor ao pior", 10 para *Sem compra válida*. Serve para ordenar `segmento` |
| `em_risco` | `Sim` ou `Não` |
| `cupom_sugerido` | Cupom da campanha do segmento (`—` quando a ação é um brinde, sem desconto) |

### `dim_produtos` (40 linhas)
| Coluna | Descrição |
|---|---|
| `produto_id`, `produto`, `categoria`, `preco`, `custo` | Como na camada bruta |
| `margem_unitaria` | `preco − custo` |
| `margem_pct` | `margem_unitaria ÷ preco` |

### `dim_calendario` (1.096 linhas · um dia por linha, sem buracos)
| Coluna | Descrição |
|---|---|
| `data` | Chave |
| `ano`, `trimestre`, `mes_num`, `mes_nome`, `ano_mes` | Partes da data. `ano_mes` (ex.: `2025-03`) ordena meses de anos diferentes sem misturá-los |
| `dia_semana_num`, `dia_semana`, `fim_de_semana` | Dia da semana (1 = segunda) e se é fim de semana (`Sim`/`Não`) |

### `fato_pedidos` (15.882 linhas · um pedido por linha, todos os status)
| Coluna | Descrição |
|---|---|
| `pedido_id`, `cliente_id`, `data_pedido`, `status`, `canal` | Como na camada bruta |
| `valido` | 1 para `pago`/`enviado`/`entregue`, 0 para os outros |
| `cupom_usado` | Nome do cupom, ou `Sem cupom` |
| `usou_cupom` | 1 ou 0 |
| `desconto_valor` | R$ de desconto (de `pedidos.desconto`) |
| `valor_total` | R$ pago |

### `fato_itens` (32.813 linhas · um item por linha)
| Coluna | Descrição |
|---|---|
| `item_id`, `pedido_id`, `produto_id` | Chaves |
| `cliente_id`, `data_pedido`, `valido` | Copiados do pedido, para o item se ligar direto às dimensões |
| `quantidade`, `preco_unitario` | Como na camada bruta |
| `subtotal` | `quantidade × preco_unitario` |
| `receita_rateada` | Valor pago do pedido dividido entre os itens, proporcional ao `subtotal`. A soma dos itens válidos bate com a soma de `valor_total` dos pedidos válidos (R$ 4.149.291,90) |

**Relacionamentos do Power BI:** `dim_calendario[data]` → `fato_pedidos[data_pedido]` e `fato_itens[data_pedido]`; `dim_clientes[cliente_id]` → `fato_pedidos[cliente_id]` e `fato_itens[cliente_id]`; `dim_produtos[produto_id]` → `fato_itens[produto_id]`. Fato com fato **não** é ligado, por isso receita, pedidos e ticket usam `fato_itens`.

## Arquivos auxiliares
| Arquivo | Conteúdo |
|---|---|
| `data/rfm_clientes.csv` | Resultado do RFM por cliente (saída do notebook 02) |
| `data/campanhas/*.csv` | Lista de clientes por campanha: `cliente, nome, email, estado, segmento, cupom_sugerido, desconto_pct, acao, motivo, dias_sem_comprar, pedidos, gasto_total` |
| `data/gabarito_perfis.csv` | O perfil "verdadeiro" plantado no gerador (`em_risco`, `fiel`…). **Só serve para conferir a segmentação**; a análise nunca lê este arquivo |
