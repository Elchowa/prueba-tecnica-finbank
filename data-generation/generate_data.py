import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import uuid
 
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
 
NOMBRES = ["Juan", "Maria", "Carlos", "Ana", "Luis", "Laura", "Andres", "Camila",
           "Diego", "Valentina", "Santiago", "Isabella", "Miguel", "Sofia", "David",
           "Daniela", "Felipe", "Gabriela", "Jorge", "Paula"]
APELLIDOS = ["Martinez", "Rodriguez", "Gomez", "Puello", "Perez", "Garcia",
             "Lopez", "Diaz", "Hernandez", "Ramirez", "Torres", "Vargas",
             "Castro", "Rojas", "Morales", "Suarez", "Ortiz", "Jimenez"]
 
 
def fake_name():
    return random.choice(NOMBRES)
 
 
def fake_lastname():
    return random.choice(APELLIDOS)
 
 
def fake_unique_number(digits, _seen=set()):
    while True:
        n = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        if n not in _seen:
            _seen.add(n)
            return n
 
 
def fake_date_between(start_days_ago=365 * 5, end_days_ago=0):
    d = random.randint(end_days_ago, start_days_ago)
    return datetime(2026, 9, 10) - timedelta(days=d)
 
N_CLIENTES = 10000
N_PRODUCTOS = 50
N_MOVIMIENTOS = 500000
NULL_RATE = 0.05  
 
CIUDADES_DEPTOS = [
    ("Bogotá", "Cundinamarca"), ("Medellín", "Antioquia"),
    ("Cali", "Valle del Cauca"), ("Cartagena", "Bolívar"),
    ("Barranquilla", "Atlántico"), ("Bucaramanga", "Santander"),
]
 
SEGMENTOS = ["Basico", "Estandar", "Premium", "Elite"]
CANALES_ADQUIS = ["App movil", "Portal web", "Corresponsal bancario"]
TIPOS_PROD = ["Credito consumo", "Cuenta ahorro", "Servicio transaccional"]
TIPOS_MOV = ["Pago", "Transferencia", "Recarga", "Avance"]
CANALES_MOV = ["App", "Web", "Corresponsal", "ATM"]
 
 
def add_nulls(series, rate=NULL_RATE):
    
    mask = np.random.rand(len(series)) < rate
    series = series.copy()
    series[mask] = None
    return series
 
 
def audit_columns(df, source_system="TRANSACCIONAL_FINBANK"):
    
    df["ingest_timestamp"] = datetime.now().isoformat()
    df["source_system"] = source_system
    df["batch_id"] = f"batch_{datetime.now().strftime('%Y%m%d')}_001"
    return df
 
 
def generar_clientes(n=N_CLIENTES):
    ids = np.arange(1, n + 1)
    # Edades con distribución normal, entre 18 y 85 años
    edades = np.clip(np.random.normal(loc=38, scale=12, size=n), 18, 85).astype(int)
    hoy = datetime(2026, 9, 10)
    fec_nac = [hoy - timedelta(days=int(e * 365.25) + random.randint(0, 364)) for e in edades]
    fec_alta = [fake_date_between() for _ in range(n)]
 
    ciudades = [random.choice(CIUDADES_DEPTOS) for _ in range(n)]
 
    df = pd.DataFrame({
        "id_cli": ids,
        "nomb_cli": [fake_name() for _ in range(n)],
        "apell_cli": [fake_lastname() for _ in range(n)],
        "tip_doc": np.random.choice(["CC", "CE", "NIT"], size=n, p=[0.9, 0.08, 0.02]),
        "num_doc": [fake_unique_number(10) for _ in range(n)],
        "fec_nac": [d.strftime("%Y-%m-%d") for d in fec_nac],
        "fec_alta": [d.strftime("%Y-%m-%d") for d in fec_alta],
        "cod_segmento": np.random.choice(SEGMENTOS, size=n, p=[0.5, 0.3, 0.15, 0.05]),
        "score_buro": np.clip(np.random.normal(650, 100, n), 150, 950).astype(int),
        "ciudad_res": [c[0] for c in ciudades],
        "depto_res": [c[1] for c in ciudades],
        "estado_cli": np.random.choice(["Activo", "Inactivo"], size=n, p=[0.92, 0.08]),
        "canal_adquis": np.random.choice(CANALES_ADQUIS, size=n),
    })
 
    # Nulos controlados en campos no críticos
    df["canal_adquis"] = add_nulls(df["canal_adquis"])
    df["score_buro"] = add_nulls(df["score_buro"].astype("float"))
 
    return audit_columns(df)
 
 
def generar_productos(n=N_PRODUCTOS):
    ids = np.arange(1, n + 1)
    tipo = np.random.choice(TIPOS_PROD, size=n)
    df = pd.DataFrame({
        "cod_prod": ids,
        "desc_prod": [f"{t} - Producto {i}" for i, t in zip(ids, tipo)],
        "tip_prod": tipo,
        "tasa_ea": np.round(np.random.uniform(0.08, 0.35, n), 4),
        "plazo_max_meses": np.random.choice([12, 24, 36, 48, 60], size=n),
        "cuota_min": np.round(np.random.uniform(50000, 500000, n), -3),
        "comision_admin": np.round(np.random.uniform(0, 25000, n), -2),
        "estado_prod": np.random.choice(["Activo", "Inactivo"], size=n, p=[0.85, 0.15]),
    })
    return audit_columns(df)
 
 
def generar_movimientos(n=N_MOVIMIENTOS, n_clientes=N_CLIENTES, n_productos=N_PRODUCTOS):
    ids = np.arange(1, n + 1)
    id_cli = np.random.randint(1, n_clientes + 1, size=n)
    cod_prod = np.random.randint(1, n_productos + 1, size=n)
 
    # Fechas cubriendo 12 meses de histórico
    fecha_base = datetime(2026, 9, 10)
    dias_atras = np.random.randint(0, 365, size=n)
    fec_mov = [(fecha_base - timedelta(days=int(d))) for d in dias_atras]
 
    # Horarios concentrados en horario laboral (distribución no uniforme, realista)
    horas = np.clip(np.random.normal(loc=13, scale=4, size=n), 0, 23).astype(int)
    hra_mov = [f"{h:02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}" for h in horas]
 
    # Montos con distribución log-normal (típico de comportamiento financiero real)
    vr_mov = np.round(np.random.lognormal(mean=11, sigma=1.2, size=n), -2)
    vr_mov = np.clip(vr_mov, 5000, 15000000)
 
    df = pd.DataFrame({
        "id_mov": ids,
        "id_cli": id_cli,
        "cod_prod": cod_prod,
        "num_cuenta": [fake_unique_number(12) for _ in range(n)],
        "fec_mov": [d.strftime("%Y-%m-%d") for d in fec_mov],
        "hra_mov": hra_mov,
        "vr_mov": vr_mov,
        "tip_mov": np.random.choice(TIPOS_MOV, size=n, p=[0.4, 0.35, 0.15, 0.1]),
        "cod_canal": np.random.choice(CANALES_MOV, size=n),
        "cod_ciudad": [random.choice(CIUDADES_DEPTOS)[0] for _ in range(n)],
        "cod_estado_mov": np.random.choice(["Exitoso", "Fallido", "Pendiente"], size=n, p=[0.92, 0.05, 0.03]),
        "id_dispositivo": [str(uuid.uuid4()) for _ in range(n)],
    })
 
    # Nulos controlados
    df["cod_canal"] = add_nulls(df["cod_canal"])
 
    # Anomalías intencionales documentadas
    # Duplicados exactos (simula error de reintento de transacción)
    n_dupes = max(1, int(n * 0.001))
    dupes = df.sample(n_dupes, random_state=SEED)
    df = pd.concat([df, dupes], ignore_index=True)
 
    # Registro con fecha fuera de rango (simula error de sistema fuente)
    if len(df) > 0:
        idx = df.sample(1, random_state=SEED).index[0]
        df.loc[idx, "fec_mov"] = "2099-01-01"
 
    return audit_columns(df)
 
 
if __name__ == "__main__":
    print(f"Generando datos sintéticos con semilla fija = {SEED}...")
 
    df_clientes = generar_clientes()
    df_productos = generar_productos()
    df_movimientos = generar_movimientos()
 
    df_clientes.to_csv("TB_CLIENTES_CORE.csv", index=False)
    df_productos.to_csv("TB_PRODUCTOS_CAT.csv", index=False)
    df_movimientos.to_csv("TB_MOV_FINANCIEROS.csv", index=False)
 
    print(f"TB_CLIENTES_CORE.csv      -> {len(df_clientes)} registros")
    print(f"TB_PRODUCTOS_CAT.csv      -> {len(df_productos)} registros")
    print(f"TB_MOV_FINANCIEROS.csv    -> {len(df_movimientos)} registros")