# Storytelling · como contar a história do painel

Números abaixo vêm dos dados **fictícios** do Boto Café (conferidos por código sobre os CSVs de `data/powerbi/`).
Em um projeto real, substitua pelos seus.

## A história em 4 atos

| Ato | Página | Mensagem | Número de apoio |
|---|---|---|---|
| 1. Contexto | Visão Geral | "A loja fatura bem, mas para quem?" | Receita R$ 4,15 mi · 14.860 pedidos · ticket R$ 279 |
| 2. Quem são | RFM | "Dois grupos carregam o negócio." | Campeões (44,4%) + Clientes Fiéis (33,6%) = 78% da receita |
| 3. Dependência | Clientes VIP | "A receita é concentrada." | Os 10% maiores clientes geram 52,2% da receita |
| 4. Ação | Churn e Ações | "Há dinheiro parado em clientes que estão sumindo." | 600 clientes em risco (30,3%) já gastaram R$ 583 mil; Prestes a Dar Churn ainda responde por 9,9% da receita |

Fecho: a recomendação (campanhas por segmento, cupom com desconto abaixo do ponto de equilíbrio) e o próximo
passo (medir com teste A/B, porque a taxa de resposta usada é uma hipótese).

## Boas práticas

1. **Pergunta antes de gráfico.** Cada página responde uma pergunta, escrita no título.
2. **Conclusão no título.** "Campeões e Fiéis geram 78% da receita" informa mais que "Receita por segmento".
3. **Uma cor de destaque por visual.** O resto fica em tons neutros do tema. O olho vai para o que importa.
4. **Menos é mais.** Se um visual não ajuda a responder a pergunta da página, tire.
5. **Ordem lógica:** do geral para o específico, e do problema para a ação.
6. **Mostre a comparação.** Um número sem referência não diz nada (versus mês anterior, versus meta, versus outro segmento).
7. **Termine em decisão.** Última página: quem contatar, com qual cupom, a que custo.

## Armadilhas honestas (cite na apresentação)

- **Dados fictícios.** Os padrões foram gerados para o estudo; não são resultado de um negócio real.
- **Segmento é uma foto.** Não se recalcula com o filtro de período; muda só quando rodamos o RFM de novo.
- **Cupom é simulação.** Taxa de resposta e % incremental são hipóteses; o teste A/B é quem confirma.
- **Base de 2 anos.** Comparação ano contra ano só vale a partir do 13º mês.
- **Correlação não é causa.** Cliente em risco não significa cliente perdido, só um sinal para agir.

## Roteiro de apresentação (5 minutos)

1. (30 s) O problema: "Como saber quem vale investir e quem está sumindo?"
2. (60 s) Visão geral: receita, região, categoria.
3. (60 s) RFM: o mapa e os 9 segmentos.
4. (60 s) VIPs: a concentração.
5. (90 s) Churn e ações: a lista de resgate e o ponto de equilíbrio do cupom.
6. Pergunta final: "O que você faria com R$ 5 mil de orçamento de campanha?"
