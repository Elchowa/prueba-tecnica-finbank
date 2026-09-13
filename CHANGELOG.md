# CHANGELOG

Historial de cambios del proyecto — Prueba Técnica Ingeniero de Datos (FinBank Pipeline)

## [2026-09-10] — Miércoles — Setup inicial

**Autor:** Juan David Martinez Puello

- Se evaluaron 3 plataformas cloud: Microsoft Fabric (bloqueada por filtro antifraude en creación de cuenta), Google Cloud Platform (bloqueada por error en creación de cuenta de facturación), y Amazon AWS (registro exitoso, plataforma elegida).
- Se definió el escenario de negocio: Escenario A — Banca y Servicios Financieros (FinBank S.A.)
- Se creó la estructura base del repositorio: `/data-generation`, `/pipelines`, `/orchestration`, `/docs`
- Se creó el bucket S3 con las carpetas `bronze/`, `silver/`, `gold/`
- Se desarrolló y validó `generate_data.py`: script de generación de datos sintéticos con semilla fija (42), cubriendo 3 de las 6 tablas fuente (`TB_CLIENTES_CORE`, `TB_PRODUCTOS_CAT`, `TB_MOV_FINANCIEROS`), con integridad referencial verificada, ~5% de nulos controlados, y 2 anomalías intencionales (duplicados, fecha fuera de rango)
- Se redactó la primera versión del README.md con la justificación de sector, plataforma y alcance
- Se ajustaron los volúmenes de datos generados a los mínimos exigidos por el documento: 10.000 clientes, 50 productos, 500.000 movimientos

## [2026-09-10/11] — Capa Bronze y Silver

**Autor:** Juan David Martinez Puello

- Capa Bronze: se crearon las 3 tablas externas en Athena (`finbank_bronze.tb_clientes_core`, `tb_productos_cat`, `tb_mov_financieros`) sobre los datos crudos en S3, usando `OpenCSVSerde` con todas las columnas tipadas como STRING (patrón estándar de Bronze: se preserva el dato crudo sin forzar conversión de tipos, dejando esa responsabilidad a la capa Silver)
- Capa Silver:
  - `tb_clientes_core`: deduplicación por `id_cli`, conversión de tipos (fechas, numéricos), enmascaramiento de `num_doc` mediante hash SHA-256
  - `tb_productos_cat`: conversión de tipos
  - `tb_mov_financieros_errores`: tabla de errores del pipeline que captura registros con `id_cli`/`cod_prod` inexistente en las dimensiones, o con fecha de movimiento fuera de rango (captura exitosamente la anomalía de fecha inyectada intencionalmente en la generación de datos)
  - `tb_mov_financieros`: deduplicación por `id_mov` (elimina duplicados exactos inyectados intencionalmente), exclusión de registros inválidos, conversión de tipos
- Verificación de conteos: 10.000 clientes, 50 productos, ~500.000 movimientos válidos, al menos 1 registro en la tabla de errores — todo confirmado correcto

<!-- Próximas entradas se agregan aquí, una por cada día de trabajo -->

## [2026-09-12] — Sábado — Capa Gold

**Autor:** Juan David Martinez Puello

- Se creó la base de datos `finbank_gold` con el modelo dimensional:
  - `dim_clientes`: nombre completo unificado, edad calculada, segmento legible
  - `dim_productos`: tasa mensual equivalente calculada, clasificación por familia de producto
  - `fact_transacciones`: monto convertido a USD (supuesto: 1 USD = 4000 COP), flag de horario hábil/no hábil, y regla de negocio `ind_sospechoso`
  - `kpis_diarios`: tabla de agregación por fecha/ciudad/canal (segunda vista de agregación, además de fact_transacciones)
- Regla de negocio implementada: `ind_sospechoso` marca una transacción cuando su monto supera en más de 3 desviaciones estándar el promedio histórico del cliente. Simplificación documentada: se usa el promedio histórico completo en vez de una ventana móvil exacta de 30 días, por tiempo disponible.
- Verificación: 10.000 clientes, 50 productos, 499.999 transacciones, 13.213 marcadas como sospechosas (~2.6%, coherente con la distribución sesgada de los montos generados), 10.950 filas de KPIs diarios

## [2026-09-12] — Sábado — Orquestación

**Autor:** Juan David Martinez Puello

- Se desarrolló `run_pipeline.py`: orquestador del pipeline vía boto3 (API de Athena) que ejecuta Bronze → Silver → Gold en secuencia, con control de dependencias (si una capa falla, las siguientes no se ejecutan) y reintentos automáticos con backoff exponencial (hasta 3 intentos por sentencia)
- Se desarrolló `reset_tables.py`: utilidad de soporte para limpiar el catálogo de tablas antes de una ejecución desde cero
- Se corrigió un bug detectado durante las pruebas: `CURRENT_TIMESTAMP` generaba un tipo `timestamp with time zone` no soportado por el formato Parquet en Athena; se resolvió con `CAST(... AS VARCHAR)`
- Se identificó y documentó una limitación de idempotencia: el pipeline actual requiere limpieza manual de S3 antes de una re-ejecución completa, porque `DROP TABLE` en Athena no elimina los archivos subyacentes en S3. Mejora futura identificada: agregar limpieza automática de S3 al inicio del orquestador, o migrar a `INSERT OVERWRITE`/tablas Iceberg para lograr idempotencia real
- Ejecución completa verificada de punta a punta: BRONZE: OK, SILVER: OK, GOLD: OK — con evidencia de conteos consistentes tras la re-ejecución automatizada (10.000 clientes, 50 productos, 499.999 transacciones, 10.950 filas de KPIs)

## [2026-09-13] — Domingo — Evidencias, documentación y cierre

**Autor:** Juan David Martinez Puello

- Se recibió información adicional de la empresa: el criterio de evaluación prioriza evidencia demostrable del manejo del entorno cloud sobre la perfección del código. Se ajustó el orden de trabajo del día para asegurar evidencia completa.
- Se capturó evidencia de ejecución real en AWS: estructura del bucket S3, catálogo de bases de datos en Athena, conteos de registros por capa, tabla de errores con datos reales, transacciones marcadas como sospechosas, y resumen de ejecución exitosa del orquestador — todo en `/docs/evidencias/`
- Se creó el diagrama Entidad-Relación (`/docs/diagrama_er.md`, formato Mermaid) cubriendo el modelo de origen (Bronze) y el modelo dimensional (Gold)
- Se creó el catálogo de datos (`/docs/catalogo_datos.md`) documentando cada tabla y campo de las capas Silver y Gold, incluyendo la identificación de 2 campos sensibles adicionales (`num_cuenta`, `id_dispositivo`) que quedaron identificados pero sin enmascarar, documentado como mejora pendiente honesta
- Se actualizó el README con la sección de evidencias y el resumen final de decisiones
