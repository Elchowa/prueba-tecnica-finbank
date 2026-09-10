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

<!-- Próximas entradas se agregan aquí, una por cada día de trabajo -->
