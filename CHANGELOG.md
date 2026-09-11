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

<!-- Próximas entradas se agregan aquí
