CREATE DATABASE IF NOT EXISTS finbank_gold;

CREATE TABLE finbank_gold.dim_clientes
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/gold/dim_clientes/')
AS
SELECT
    id_cli,
    nomb_cli || ' ' || apell_cli AS nombre_completo,
    tip_doc,
    num_doc_hash,
    fec_nac,
    DATE_DIFF('year', fec_nac, DATE '2026-09-10') AS edad,
    fec_alta,
    cod_segmento AS segmento,
    score_buro,
    ciudad_res,
    depto_res,
    estado_cli,
    canal_adquis
FROM finbank_silver.tb_clientes_core;


CREATE TABLE finbank_gold.dim_productos
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/gold/dim_productos/')
AS
SELECT
    cod_prod,
    desc_prod AS descripcion_producto,
    tip_prod AS tipo_producto,
    tasa_ea AS tasa_efectiva_anual,
    POWER((1 + tasa_ea), CAST(1.0/12 AS DOUBLE)) - 1 AS tasa_mensual_equivalente,
    plazo_max_meses,
    cuota_min,
    comision_admin,
    CASE
        WHEN tip_prod LIKE '%redito%' THEN 'Credito'
        WHEN tip_prod LIKE '%horro%' THEN 'Ahorro'
        ELSE 'Transaccional'
    END AS familia_producto,
    estado_prod
FROM finbank_silver.tb_productos_cat;


CREATE TABLE finbank_gold.fact_transacciones
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/gold/fact_transacciones/')
AS
WITH client_stats AS (
    SELECT
        id_cli,
        AVG(vr_mov) AS avg_monto_cliente,
        STDDEV(vr_mov) AS std_monto_cliente
    FROM finbank_silver.tb_mov_financieros
    GROUP BY id_cli
)
SELECT
    m.id_mov,
    m.id_cli,
    m.cod_prod,
    m.fec_mov,
    m.hra_mov,
    m.vr_mov,
    ROUND(m.vr_mov / 4000.0, 2) AS monto_usd,
    m.tip_mov,
    m.cod_canal,
    m.cod_ciudad,
    CASE
        WHEN CAST(SPLIT_PART(m.hra_mov, ':', 1) AS INTEGER) BETWEEN 6 AND 22 THEN 'Habil'
        ELSE 'No habil'
    END AS flag_horario,
    CASE
        WHEN s.std_monto_cliente IS NOT NULL
             AND s.std_monto_cliente > 0
             AND m.vr_mov > (s.avg_monto_cliente + 3 * s.std_monto_cliente)
        THEN true
        ELSE false
    END AS ind_sospechoso
FROM finbank_silver.tb_mov_financieros m
LEFT JOIN client_stats s ON m.id_cli = s.id_cli;


CREATE TABLE finbank_gold.kpis_diarios
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/gold/kpis_diarios/')
AS
SELECT
    fec_mov AS fecha,
    cod_ciudad AS ciudad,
    cod_canal AS canal,
    COUNT(*) AS total_transacciones,
    SUM(vr_mov) AS monto_total,
    ROUND(AVG(vr_mov), 2) AS monto_promedio,
    SUM(CASE WHEN ind_sospechoso THEN 1 ELSE 0 END) AS transacciones_sospechosas
FROM finbank_gold.fact_transacciones
GROUP BY fec_mov, cod_ciudad, cod_canal;
