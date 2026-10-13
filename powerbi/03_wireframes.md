# Wireframes · 4 páginas

Tela sugerida: **16:9, 1280 × 720**. Margem de 16 px, espaço de 12 px entre blocos.
Cores e tema: `boto_cafe_tema.json`. Medidas citadas estão em `02_medidas.dax`.

Regras para todas as páginas:
- Título da página como **pergunta ou conclusão**, não como rótulo ("Quem sustenta a receita?", e não "Gráfico de segmentos").
- Máximo de 6 visuais principais por página.
- Segmentadores sempre na mesma posição (faixa superior), sincronizados entre páginas (Exibir > Sincronizar segmentadores).
- Menu de páginas à esquerda (botões de navegação), com a página atual destacada em `#2E5E4E`.

---

## Página 1 · Visão Geral — "Como está o negócio?"

```
┌────────────────────────────────────────────────────────────────────────┐
│ ☕ Boto Café · Visão Geral     [Período ▾] [Região ▾] [Estado ▾] [Cat ▾]│
├──────┬─────────────┬─────────────┬─────────────┬─────────────┐         │
│ Nav  │ Receita     │ Pedidos     │ Ticket Médio│ % em Risco  │         │
│      ├─────────────┴─────────────┴─────────────┴─────────────┤         │
│ Visão│  Receita por mês (colunas) + Média móvel 3M (linha)   │         │
│ RFM  ├───────────────────────────┬───────────────────────────┤         │
│ VIP  │ Receita por região        │ Receita por categoria     │         │
│ Churn│ (barras horizontais)      │ (barras horizontais)      │         │
└──────┴───────────────────────────┴───────────────────────────┴─────────┘
```

| Visual | Campos | Observação |
|---|---|---|
| 4 cartões | `Receita`, `Pedidos`, `Ticket Médio`, `% Clientes em Risco` | Formatar R$ e % |
| Colunas + linha | Eixo `dim_calendario[ano_mes]`; valores `Receita` e `Receita Média Móvel 3M` | Linha em dourado |
| Barras (região) | `dim_clientes[regiao]` × `Receita` | Norte/Nordeste em destaque na legenda do texto |
| Barras (categoria) | `dim_produtos[categoria]` × `Receita` | |

Segmentadores: `dim_calendario[data]` (intervalo), `dim_clientes[regiao]`, `dim_clientes[estado]`, `dim_produtos[categoria]`.

---

## Página 2 · RFM — "Quem são nossos clientes?"

```
┌────────────────────────────────────────────────────────────────────────┐
│ Quem são os nossos clientes?          [Região ▾] [Estado ▾] [Segmento ▾]│
├──────┬──────────────────────────────┬─────────────────────────────────┤
│ Nav  │ Matriz R × F (heatmap)       │ Clientes por segmento (barras)  │
│      │ cor = nº de clientes         │ ordenado por segmento_ordem     │
│      ├──────────────────────────────┼─────────────────────────────────┤
│      │ % da receita por segmento    │ Tabela-resumo: segmento,        │
│      │ (barras)                     │ clientes, recência média,       │
│      │                              │ frequência média, ticket médio  │
└──────┴──────────────────────────────┴─────────────────────────────────┘
```

| Visual | Campos | Observação |
|---|---|---|
| Matriz (heatmap) | Linhas `dim_clientes[R]` (ordem decrescente), colunas `dim_clientes[F]`, valores `Clientes Compradores` | Formatação condicional de fundo: gradiente `#F5EDE0` → `#2E5E4E` |
| Barras | `segmento` × `Clientes Compradores` | Cores por segmento (guia, seção 7) |
| Barras | `segmento` × `% Receita do Segmento` | |
| Tabela | `segmento`, `Clientes Compradores`, `Recência Média (dias)`, `Frequência Média`, `Ticket Médio` | |

Lembrete visível na página (caixa de texto pequena): *"Segmentos são uma foto de todo o histórico; o filtro de período não os recalcula."*

---

## Página 3 · Clientes VIP — "Quem sustenta a receita?"

```
┌────────────────────────────────────────────────────────────────────────┐
│ Quem sustenta a receita?           [Período ▾] [Segmento ▾] [Estado ▾] │
├──────┬────────────┬────────────┬────────────────────────────────────────┤
│ Nav  │ Clientes   │ % receita  │                                        │
│      │ Campeões   │ top 10%    │  Top 15 clientes por Receita (barras)  │
│      ├────────────┴────────────┤                                        │
│      │ Receita por canal de    ├────────────────────────────────────────┤
│      │ aquisição (rosca)       │ Tabela: nome, cidade, estado, segmento,│
│      │                         │ pedidos, recência, Receita             │
└──────┴─────────────────────────┴────────────────────────────────────────┘
```

| Visual | Campos | Observação |
|---|---|---|
| Cartão | `Clientes Compradores` com filtro de visual `segmento = Campeões` | |
| Cartão | `% Receita Top 10% Clientes` | Principal número da página |
| Barras | `dim_clientes[nome]` × `Receita`; filtro de visual **N primeiros: 15** por `Receita` | Cor pelo segmento |
| Rosca | `canal_aquisicao` × `Receita` | Máx. 5 fatias |
| Tabela | `nome`, `cidade`, `estado`, `segmento`, `frequencia`, `recencia`, `Receita` | Ordenar por `Receita` |

---

## Página 4 · Churn e Ações — "Quem a gente ainda consegue recuperar?"

```
┌────────────────────────────────────────────────────────────────────────┐
│ Quem ainda dá para recuperar?       [Região ▾] [Estado ▾] [Segmento ▾] │
├──────┬────────────┬────────────┬────────────┬────────────────────────────┤
│ Nav  │ Clientes   │ Gasto      │ % Cancel./ │                            │
│      │ em risco   │ histórico  │ Devolvido  │ Clientes em risco por      │
│      │            │ em risco   │            │ segmento e região (barras  │
│      ├────────────┴────────────┴────────────┤ empilhadas)                │
│      │ Tabela de ação (ordenada por gasto): ├────────────────────────────┤
│      │ nome, e-mail, segmento, dias sem     │ Controle "% Incremental"   │
│      │ comprar, gasto, cupom_sugerido       │ + cartão Desconto de       │
│      │                                      │ Equilíbrio                 │
└──────┴──────────────────────────────────────┴────────────────────────────┘
```

| Visual | Campos | Observação |
|---|---|---|
| 3 cartões | `Clientes em Risco`, `Gasto Histórico em Risco`, `% Cancelado ou Devolvido` | |
| Tabela de ação | `nome`, `email`, `segmento`, `recencia`, `monetario`, `cupom_sugerido` | Filtro de visual `em_risco = Sim`; ordenar por `monetario` decrescente; exportar com "..." > Exportar dados |
| Barras empilhadas | `regiao` × `Clientes em Risco`, legenda `segmento` | |
| Controle + cartão | Parâmetro `% Incremental` e medida `Desconto de Equilíbrio` | Mostra de forma visual até onde dá para ir no desconto |

Dica: use **dicas de ferramenta (tooltip)** para mostrar nesta página o cupom e a ação sugerida de cada segmento
(veja `src/cupons.py` e `data/campanhas/`).

---

## Checklist de design

- [ ] Fonte de no mínimo 10 pt em qualquer rótulo
- [ ] Cartões alinhados à grade (use "Alinhar" e "Distribuir")
- [ ] Nenhum gráfico de pizza com mais de 5 fatias
- [ ] Eixos com título só quando a unidade não for óbvia
- [ ] Todas as páginas testadas com o filtro de **Estado** em um único valor (ex.: PA) para ver se não quebram
- [ ] Texto alternativo nos visuais principais (Formatar > Geral > Texto alternativo)
