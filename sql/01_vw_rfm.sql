-- ============================================================================
-- Boto Café · RFM em SQL (SQLite)
--
-- Mesma lógica do Python (src/rfm.py), escrita como VIEWs encadeadas:
--   vw_pedidos_validos -> vw_data_referencia -> vw_rfm_metricas -> vw_rfm_scores -> vw_rfm_segmentos
-- Cada VIEW é uma camada com uma responsabilidade (como os "modelos" de uma ferramenta tipo dbt).
-- O teste tests/test_rfm.py garante que o resultado é IGUAL ao do pandas.
-- ============================================================================

DROP VIEW IF EXISTS vw_rfm_segmentos;
DROP VIEW IF EXISTS vw_rfm_scores;
DROP VIEW IF EXISTS vw_rfm_metricas;
DROP VIEW IF EXISTS vw_data_referencia;
DROP VIEW IF EXISTS vw_pedidos_validos;


-- 1. Pedido válido = pago, enviado ou entregue (cancelado, devolvido e pendente ficam de fora).
CREATE VIEW vw_pedidos_validos AS
SELECT *
FROM pedidos
WHERE status IN ('pago', 'enviado', 'entregue');


-- 2. Data de referência = dia seguinte à última compra válida (a recência mínima é 1 dia, nunca 0).
CREATE VIEW vw_data_referencia AS
SELECT date(MAX(data_pedido), '+1 day') AS data_ref
FROM vw_pedidos_validos;


-- 3. R, F e M "brutos" por cliente (só quem tem ao menos uma compra válida).
CREATE VIEW vw_rfm_metricas AS
SELECT
    p.cliente_id,
    MIN(p.data_pedido)  AS primeira_compra,
    MAX(p.data_pedido)  AS ultima_compra,
    COUNT(*)            AS frequencia,                 -- F: nº de pedidos
    SUM(p.valor_total)  AS monetario,                  -- M: valor pago (já com desconto)
    CAST(julianday(r.data_ref) - julianday(MAX(p.data_pedido)) AS INTEGER) AS recencia   -- R: dias
FROM vw_pedidos_validos AS p
CROSS JOIN vw_data_referencia AS r
GROUP BY p.cliente_id;


-- 4. Notas de 1 a 5 (quintis).
-- ROW_NUMBER faz o papel do rank(method='first') do pandas: desempata valores iguais pela ordem do cliente_id.
-- O corte de cada nota replica o pd.qcut sobre o ranque: o limite k vale 1 + (n-1)*k/5.
-- A conta é feita multiplicando tudo por 5 para evitar números decimais:  rn*5 <= 5 + (n-1)*k
-- Recência: MENOR é melhor, por isso a ordem é invertida (maior nº de dias = nota 1).
CREATE VIEW vw_rfm_scores AS
WITH ranque AS (
    SELECT
        *,
        COUNT(*) OVER ()                                         AS n,
        ROW_NUMBER() OVER (ORDER BY recencia DESC, cliente_id)   AS rn_r,
        ROW_NUMBER() OVER (ORDER BY frequencia,    cliente_id)   AS rn_f,
        ROW_NUMBER() OVER (ORDER BY monetario,     cliente_id)   AS rn_m
    FROM vw_rfm_metricas
)
SELECT
    cliente_id, primeira_compra, ultima_compra, recencia, frequencia, monetario,
    CASE WHEN rn_r * 5 <= 5 + (n - 1) * 1 THEN 1 WHEN rn_r * 5 <= 5 + (n - 1) * 2 THEN 2
         WHEN rn_r * 5 <= 5 + (n - 1) * 3 THEN 3 WHEN rn_r * 5 <= 5 + (n - 1) * 4 THEN 4 ELSE 5 END AS R,
    CASE WHEN rn_f * 5 <= 5 + (n - 1) * 1 THEN 1 WHEN rn_f * 5 <= 5 + (n - 1) * 2 THEN 2
         WHEN rn_f * 5 <= 5 + (n - 1) * 3 THEN 3 WHEN rn_f * 5 <= 5 + (n - 1) * 4 THEN 4 ELSE 5 END AS F,
    CASE WHEN rn_m * 5 <= 5 + (n - 1) * 1 THEN 1 WHEN rn_m * 5 <= 5 + (n - 1) * 2 THEN 2
         WHEN rn_m * 5 <= 5 + (n - 1) * 3 THEN 3 WHEN rn_m * 5 <= 5 + (n - 1) * 4 THEN 4 ELSE 5 END AS M
FROM ranque;


-- 5. Segmento: as regras são avaliadas NA ORDEM (a primeira que bater vence), igual a REGRAS_SEGMENTOS no Python.
CREATE VIEW vw_rfm_segmentos AS
SELECT
    cliente_id, primeira_compra, ultima_compra, recencia, frequencia, monetario,
    R, F, M,
    CAST(R AS TEXT) || CAST(F AS TEXT) || CAST(M AS TEXT) AS score_rfm,
    R + F + M AS score_soma,
    CASE
        WHEN R = 5 AND F = 5 AND M = 5       THEN 'Campeões'
        WHEN frequencia = 1 AND R >= 4       THEN 'Novos'
        WHEN R >= 3 AND F >= 4               THEN 'Clientes Fiéis'
        WHEN R >= 4 AND F >= 2               THEN 'Potenciais Fiéis'
        WHEN R <= 2 AND F >= 3               THEN 'Prestes a Dar Churn'
        WHEN R = 3 AND F = 3                 THEN 'Precisam de Atenção'
        WHEN R >= 3                          THEN 'Promissores'
        WHEN R = 2                           THEN 'Hibernando'
        ELSE 'Perdidos'
    END AS segmento
FROM vw_rfm_scores;
