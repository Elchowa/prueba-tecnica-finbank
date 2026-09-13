import boto3
import time

REGION = "us-east-2"
BUCKET = "prueba-tecnica-finbank-jdm"
OUTPUT_LOCATION = f"s3://{BUCKET}/athena-results/"

athena = boto3.client("athena", region_name=REGION)

TABLES = [
    "finbank_bronze.tb_clientes_core",
    "finbank_bronze.tb_productos_cat",
    "finbank_bronze.tb_mov_financieros",
    "finbank_silver.tb_clientes_core",
    "finbank_silver.tb_productos_cat",
    "finbank_silver.tb_mov_financieros_errores",
    "finbank_silver.tb_mov_financieros",
    "finbank_gold.dim_clientes",
    "finbank_gold.dim_productos",
    "finbank_gold.fact_transacciones",
    "finbank_gold.kpis_diarios",
]

for table in TABLES:
    sql = f"DROP TABLE IF EXISTS {table}"
    print(f"Borrando {table}...")
    resp = athena.start_query_execution(
        QueryString=sql,
        ResultConfiguration={"OutputLocation": OUTPUT_LOCATION},
    )
    qid = resp["QueryExecutionId"]
    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)
        state = status["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    print(f"  -> {state}")

print("\nListo. Todas las tablas fueron eliminadas (si existían).")
