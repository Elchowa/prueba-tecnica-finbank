CREATE DATABASE IF NOT EXISTS finbank_bronze;

CREATE EXTERNAL TABLE IF NOT EXISTS finbank_bronze.tb_clientes_core (
    id_cli STRING,
    nomb_cli STRING,
    apell_cli STRING,
    tip_doc STRING,
    num_doc STRING,
    fec_nac STRING,
    fec_alta STRING,
    cod_segmento STRING,
    score_buro STRING,
    ciudad_res STRING,
    depto_res STRING,
    estado_cli STRING,
    canal_adquis STRING,
    ingest_timestamp STRING,
    source_system STRING,
    batch_id STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"'
)
LOCATION 's3://prueba-tecnica-finbank-jdm/bronze/tb_clientes_core/'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS finbank_bronze.tb_productos_cat (
    cod_prod STRING,
    desc_prod STRING,
    tip_prod STRING,
    tasa_ea STRING,
    plazo_max_meses STRING,
    cuota_min STRING,
    comision_admin STRING,
    estado_prod STRING,
    ingest_timestamp STRING,
    source_system STRING,
    batch_id STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"'
)
LOCATION 's3://prueba-tecnica-finbank-jdm/bronze/tb_productos_cat/'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS finbank_bronze.tb_mov_financieros (
    id_mov STRING,
    id_cli STRING,
    cod_prod STRING,
    num_cuenta STRING,
    fec_mov STRING,
    hra_mov STRING,
    vr_mov STRING,
    tip_mov STRING,
    cod_canal STRING,
    cod_ciudad STRING,
    cod_estado_mov STRING,
    id_dispositivo STRING,
    ingest_timestamp STRING,
    source_system STRING,
    batch_id STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar' = '"'
)
LOCATION 's3://prueba-tecnica-finbank-jdm/bronze/tb_mov_financieros/'
TBLPROPERTIES ('skip.header.line.count'='1');


