# Kit Power BI · Boto Café

> Dados fictícios. O painel foi montado e conferido no Power BI Desktop seguindo este kit (capturas em
> `powerbi/capturas/`). Duas medidas precisaram de correção durante a montagem e já estão ajustadas em
> `02_medidas.dax`. O tema `boto_cafe_tema.json` não foi confirmado: o painel usa formatação feita à mão.
> Se algo der erro ao colar, anote a mensagem e ajuste: é parte do processo.

## Arquivos do kit

| Arquivo | Para quê |
|---|---|
| `data/powerbi/*.csv` | As 5 tabelas do modelo estrela (gerar com `python -m src.powerbi`) |
| `powerbi/02_medidas.dax` | Medidas DAX comentadas, para colar (padrão internacional) |
| `powerbi/03_wireframes.md` | Desenho das 4 páginas |
| `powerbi/boto_cafe_tema.json` | Tema de cores da marca |
| `powerbi/04_storytelling.md` | Como contar a história com o painel |

## 1. Gerar os CSVs

Na raiz do projeto:

```bash
.venv/Scripts/python -m src.powerbi
```

Saem 5 arquivos em `data/powerbi/`, em UTF-8, separados por `;` e com vírgula decimal (padrão pt-BR).
Datas vão como `AAAA-MM-DD`, que o Power BI entende em qualquer idioma.

| Tabela | Tipo | Linhas | Uma linha é… |
|---|---|---|---|
| `dim_clientes` | dimensão | 2.000 | um cliente, com R/F/M, notas, segmento, região, cupom sugerido |
| `dim_produtos` | dimensão | 40 | um produto, com margem unitária |
| `dim_calendario` | dimensão | 1.096 | um dia (2024 a 2026, sem buracos) |
| `fato_pedidos` | fato | 15.882 | um pedido (todos os status; `valido` = 1 para pago/enviado/entregue) |
| `fato_itens` | fato | 32.813 | um item de pedido, com `receita_rateada` |

Pontos de atenção:
- 19 clientes nunca tiveram compra válida. Ficam em `dim_clientes` com segmento **Sem compra válida**.
- `receita_rateada` = valor pago (já com desconto) dividido entre os itens do pedido. A soma dos itens válidos
  é R$ 4.149.291,90, igual à soma de `valor_total` dos pedidos válidos.
- Segmento, R, F e M são uma **foto** de todo o histórico. Não mudam quando você filtra o período.

## 2. Importar no Power BI Desktop

1. **Obter dados > Texto/CSV**, escolha o primeiro arquivo.
2. Confira: origem do arquivo **65001: UTF-8**, delimitador **ponto e vírgula**.
3. Clique em **Transformar Dados** (abre o Power Query) e repita para os 5 arquivos.
4. No Power Query, para cada tabela, confira os tipos (veja a tabela abaixo).
5. **Fechar e Aplicar**.

Se os valores em R$ aparecerem 100 vezes maiores ou como texto, o Power BI está lendo a vírgula com o idioma
errado. Corrija em **Transformar coluna > Tipo de dados > Usando localidade…**, escolhendo *Número decimal* e
*Português (Brasil)*.

### Tipos de dados esperados

| Tabela | Colunas | Tipo |
|---|---|---|
| todas | `*_id`, `valido`, `usou_cupom`, `quantidade`, `ano`, `mes_num`, `R`, `F`, `M`, `recencia`, `frequencia`, `score_soma`, `segmento_ordem`, `dia_semana_num` | Número inteiro |
| todas | `data`, `data_pedido`, `data_cadastro`, `primeira_compra`, `ultima_compra` | Data |
| `dim_clientes` | `monetario`, `ticket_medio` | Número decimal fixo (moeda) |
| `dim_clientes` | `score_rfm` | **Texto** (é um código como "545", não um valor) |
| `dim_produtos` | `preco`, `custo`, `margem_unitaria` | Número decimal fixo; `margem_pct` decimal (%) |
| `fato_*` | `valor_total`, `desconto_valor`, `preco_unitario`, `subtotal`, `receita_rateada` | Número decimal fixo |

### Dica de Power Query: pasta como parâmetro

Em vez de apontar o caminho em 5 consultas, crie um parâmetro `PastaDados` (Gerenciar Parâmetros > Novo, tipo
Texto) com o caminho da pasta `data\powerbi`. Cada consulta fica assim (no Editor Avançado):

```m
let
    Fonte = Csv.Document(File.Contents(PastaDados & "\dim_clientes.csv"),
                [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {
                {"cliente_id", Int64.Type}, {"monetario", Currency.Type},
                {"ticket_medio", Currency.Type}, {"data_cadastro", type date},
                {"score_rfm", type text}}, "pt-BR")
in
    Tipos
```

Se a pasta mudar de lugar, você troca o parâmetro uma vez e pronto.

## 3. Relacionamentos (aba Modelo)

Todos **um para muitos (1:*)**, direção do filtro **única** (da dimensão para o fato):

| De (lado 1) | Para (lado *) |
|---|---|
| `dim_calendario[data]` | `fato_pedidos[data_pedido]` |
| `dim_calendario[data]` | `fato_itens[data_pedido]` |
| `dim_clientes[cliente_id]` | `fato_pedidos[cliente_id]` |
| `dim_clientes[cliente_id]` | `fato_itens[cliente_id]` |
| `dim_produtos[produto_id]` | `fato_itens[produto_id]` |

Por que `fato_itens` tem cliente e data copiados? Assim ele se liga direto às dimensões. A única ligação que
**não** criamos é `fato_pedidos` ↔ `fato_itens` (fato com fato é fonte de ambiguidade). Consequência prática:
o filtro de **categoria** (que vem de `dim_produtos`) só alcança `fato_itens`. Por isso as medidas de receita,
pedidos e ticket usam `fato_itens`, como no dashboard Streamlit.

## 4. Ajustes no modelo

1. **Tabela de datas:** selecione `dim_calendario` > *Marcar como tabela de datas* > coluna `data`.
   (Necessário para as funções de tempo, como "mesmo período do ano anterior".)
2. **Ordenar por coluna** (aba Ferramentas de coluna):
   - `dim_calendario[mes_nome]` por `mes_num`
   - `dim_calendario[dia_semana]` por `dia_semana_num`
   - `dim_clientes[segmento]` por `segmento_ordem`
3. **Ocultar** do modo de relatório as colunas técnicas: todos os `*_id` dos fatos, `valido`, `segmento_ordem`,
   `mes_num`, `dia_semana_num`. Quem monta o relatório só vê o que importa.
4. **Desligar data/hora automática:** Arquivo > Opções > Carregamento de dados > desmarcar "Data/Hora automática".
   Já temos um calendário de verdade, e a automática cria tabelas escondidas.
5. **Resumo padrão = Nenhum** para `R`, `F`, `M`, `recencia`, `frequencia` (são atributos, não valores a somar).
6. **Medidas:** crie a tabela `_Medidas` (Inserir dados, vazia) e cole nela as medidas de `02_medidas.dax`.
7. **Tema:** Exibir > Temas > *Procurar por temas* > `boto_cafe_tema.json`.

## 5. Conferência rápida (faça antes de desenhar)

Com as medidas coladas, crie 4 cartões sem nenhum filtro. Os valores devem ser:

| Cartão | Esperado |
|---|---|
| Receita | R$ 4.149.292 |
| Clientes compradores | 1.981 |
| Ticket médio | R$ 279,23 |
| % clientes em risco | 30,3% |

Se bater, o modelo está certo. Se não bater, o erro está na importação ou nos relacionamentos, não no visual.

## 6. Montar as páginas

Veja `03_wireframes.md`. Ordem sugerida: Visão Geral > RFM > Clientes VIP > Churn e Ações.
Em cada página, comece pelos cartões (KPIs), depois os gráficos, e deixe os filtros (segmentadores) por último.

## 7. Colorir os segmentos com as cores do dashboard

O tema não consegue fixar cor por segmento. Nos gráficos que usam `segmento`, vá em **Formatar > Cores dos
elementos de dados** e aplique:

| Segmento | Cor |
|---|---|
| Campeões | `#C8963E` |
| Clientes Fiéis | `#2E5E4E` |
| Potenciais Fiéis | `#5E9C84` |
| Novos | `#9FCBB8` |
| Promissores | `#F2D3DC` |
| Precisam de Atenção | `#E8C27A` |
| Prestes a Dar Churn | `#E8A0B4` |
| Hibernando | `#8D6E63` |
| Perdidos | `#BCAAA4` |
