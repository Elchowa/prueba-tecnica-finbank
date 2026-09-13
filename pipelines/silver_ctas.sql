CREATE DATABASE IF NOT EXISTS finbank_silver;

CREATE TABLE finbank_silver.tb_clientes_core
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/silver/tb_clientes_core/')
AS
SELECT
    CAST(id_cli AS INTEGER) AS id_cli,
    nomb_cli,
    apell_cli,
    tip_doc,
    to_hex(sha256(to_utf8(num_doc))) AS num_doc_hash,
    CAST(fec_nac AS DATE) AS fec_nac,
    CAST(fec_alta AS DATE) AS fec_alta,
    cod_segmento,
    CAST(NULLIF(score_buro, '') AS DOUBLE) AS score_buro,
    ciudad_res,
    depto_res,
    estado_cli,
    NULLIF(canal_adquis, '') AS canal_adquis,
    ingest_timestamp,
    source_system,
    batch_id
FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id_cli ORDER BY ingest_timestamp DESC) AS rn
    FROM finbank_bronze.tb_clientes_core
)
WHERE rn = 1;


CREATE TABLE finbank_silver.tb_productos_cat
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/silver/tb_productos_cat/')
AS
SELECT
    CAST(cod_prod AS INTEGER) AS cod_prod,
    desc_prod,
    tip_prod,
    CAST(tasa_ea AS DOUBLE) AS tasa_ea,
    CAST(plazo_max_meses AS INTEGER) AS plazo_max_meses,
    CAST(cuota_min AS DOUBLE) AS cuota_min,
    CAST(comision_admin AS DOUBLE) AS comision_admin,
    estado_prod,
    ingest_timestamp,
    source_system,
    batch_id
FROM finbank_bronze.tb_productos_cat;

CREATE TABLE finbank_silver.tb_mov_financieros_errores
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/silver/errores/')
AS
SELECT
    m.id_mov,
    m.id_cli,
    m.cod_prod,
    m.fec_mov,
    m.vr_mov,
    CASE
        WHEN c.id_cli IS NULL THEN 'id_cli inexistente en dim_clientes'
        WHEN p.cod_prod IS NULL THEN 'cod_prod inexistente en dim_productos'
        WHEN CAST(m.fec_mov AS DATE) > DATE '2026-09-10' THEN 'fecha de movimiento fuera de rango (futuro)'
        ELSE 'otro'
    END AS motivo_error,
    CAST(CURRENT_TIMESTAMP AS VARCHAR) AS fecha_deteccion
FROM finbank_bronze.tb_mov_financieros m
LEFT JOIN finbank_silver.tb_clientes_core c ON CAST(m.id_cli AS INTEGER) = c.id_cli
LEFT JOIN finbank_silver.tb_productos_cat p ON CAST(m.cod_prod AS INTEGER) = p.cod_prod
WHERE c.id_cli IS NULL
   OR p.cod_prod IS NULL
   OR CAST(m.fec_mov AS DATE) > DATE '2026-09-10';



CREATE TABLE finbank_silver.tb_mov_financieros
WITH (format = 'PARQUET', external_location = 's3://prueba-tecnica-finbank-jdm/silver/tb_mov_financieros/')
AS
SELECT
    CAST(id_mov AS INTEGER) AS id_mov,
    CAST(id_cli AS INTEGER) AS id_cli,
    CAST(cod_prod AS INTEGER) AS cod_prod,
    num_cuenta,
    CAST(fec_mov AS DATE) AS fec_mov,
    hra_mov,
    CAST(vr_mov AS DOUBLE) AS vr_mov,
    tip_mov,
    NULLIF(cod_canal, '') AS cod_canal,
    cod_ciudad,
    cod_estado_mov,
    id_dispositivo,
    ingest_timestamp,
    source_system,
    batch_id
FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id_mov ORDER BY ingest_timestamp DESC) AS rn
    FROM finbank_bronze.tb_mov_financieros
    WHERE CAST(id_cli AS INTEGER) IN (SELECT id_cli FROM finbank_silver.tb_clientes_core)
      AND CAST(cod_prod AS INTEGER) IN (SELECT cod_prod FROM finbank_silver.tb_productos_cat)
      AND CAST(fec_mov AS DATE) <= DATE '2026-09-10'
)
WHERE rn = 1;
