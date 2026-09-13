import boto3
import time
import re
import sys
import os

BUCKET = "prueba-tecnica-finbank-jdm"
REGION = "us-east-2"
OUTPUT_LOCATION = f"s3://{BUCKET}/athena-results/"
PIPELINES_DIR = os.path.join(os.path.dirname(__file__), "..", "pipelines")

MAX_RETRIES = 3
POLL_INTERVAL_SECONDS = 2
BACKOFF_BASE_SECONDS = 5

LAYERS = [
    ("BRONZE", "bronze_ddl.sql"),
    ("SILVER", "silver_ctas.sql"),
    ("GOLD", "gold_ctas.sql"),
]

athena = boto3.client("athena", region_name=REGION)


def split_statements(sql_text):
    lines = [line for line in sql_text.splitlines() if not line.strip().startswith("--")]
    cleaned = "\n".join(lines)
    statements = [s.strip() for s in cleaned.split(";")]
    return [s for s in statements if s]


def run_query(sql, attempt=1):
    response = athena.start_query_execution(
        QueryString=sql,
        ResultConfiguration={"OutputLocation": OUTPUT_LOCATION},
    )
    query_id = response["QueryExecutionId"]

    while True:
        status_resp = athena.get_query_execution(QueryExecutionId=query_id)
        state = status_resp["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(POLL_INTERVAL_SECONDS)

    if state == "SUCCEEDED":
        return True, None

    reason = status_resp["QueryExecution"]["Status"].get("StateChangeReason", "sin detalle")

    if attempt < MAX_RETRIES:
        wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))  
        print(f"    Intento {attempt} falló ({reason}). Reintentando en {wait}s...")
        time.sleep(wait)
        return run_query(sql, attempt=attempt + 1)

    return False, reason


def run_layer(layer_name, filename):
    filepath = os.path.join(PIPELINES_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        sql_text = f.read().replace("TU-BUCKET", BUCKET)

    statements = split_statements(sql_text)
    print(f"\n=== Capa {layer_name} ({len(statements)} sentencias) ===")

    for i, stmt in enumerate(statements, start=1):
        preview = stmt.strip().split("\n")[0][:70]
        print(f"  [{i}/{len(statements)}] {preview}...")
        ok, error = run_query(stmt)
        if not ok:
            print(f"    FALLÓ definitivamente tras {MAX_RETRIES} intentos: {error}")
            return False

    print(f"  Capa {layer_name} completada con éxito.")
    return True


def main():
    start_time = time.time()
    print("Iniciando ejecución del pipeline FinBank...")

    resumen = {}
    for layer_name, filename in LAYERS:
        success = run_layer(layer_name, filename)
        resumen[layer_name] = success
        if not success:
            print(f"\nDeteniendo pipeline: la capa {layer_name} falló y las capas "
                  f"siguientes dependen de ella.")
            break

    elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 50)
    print("RESUMEN DE EJECUCIÓN")
    print("=" * 50)
    for layer_name, _ in LAYERS:
        estado = resumen.get(layer_name, "NO EJECUTADA")
        estado_txt = "OK" if estado is True else ("FALLÓ" if estado is False else estado)
        print(f"  {layer_name}: {estado_txt}")
    print(f"  Tiempo total: {elapsed} segundos")
    print("=" * 50)

    if not all(v is True for v in resumen.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
