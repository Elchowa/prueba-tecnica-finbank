# CHANGELOG

Historial de cambios del proyecto — Prueba Técnica Ingeniero de Datos (FinBank Pipeline)

## \[2026-09-10] — Miércoles — Setup inicial

**Autor:** Juan David Martinez Puello

* Se evaluaron 3 plataformas cloud: Microsoft Fabric (bloqueada por filtro antifraude en creación de cuenta), Google Cloud Platform (bloqueada por error en creación de cuenta de facturación), y Amazon AWS (registro exitoso, plataforma elegida).
* Se definió el escenario de negocio: Escenario A — Banca y Servicios Financieros (FinBank S.A.)
* Se creó la estructura base del repositorio: `/data-generation`, `/pipelines`, `/orchestration`, `/docs`
* Se creó el bucket S3 con las carpetas `bronze/`, `silver/`, `gold/`
* Se desarrolló y validó `generate\\\_data.py`: script de generación de datos sintéticos con semilla fija (42), cubriendo 3 de las 6 tablas fuente (`TB\\\_CLIENTES\\\_CORE`, `TB\\\_PRODUCTOS\\\_CAT`, `TB\\\_MOV\\\_FINANCIEROS`), con integridad referencial verificada, \~5% de nulos controlados, y 2 anomalías intencionales (duplicados, fecha fuera de rango)
* Se redactó la primera versión del README.md con la justificación de sector, plataforma y alcance
* Se ajustaron los volúmenes de datos generados a los mínimos exigidos por el documento: 10.000 clientes, 50 productos, 500.000 movimientos

## \[2026-09-10/11] — Capa Bronze y Silver

**Autor:** Juan David Martinez Puello

* Capa Bronze: se crearon las 3 tablas externas en Athena (`finbank\\\_bronze.tb\\\_clientes\\\_core`, `tb\\\_productos\\\_cat`, `tb\\\_mov\\\_financieros`) sobre los datos crudos en S3, usando `OpenCSVSerde` con todas las columnas tipadas como STRING (patrón estándar de Bronze: se preserva el dato crudo sin forzar conversión de tipos, dejando esa responsabilidad a la capa Silver)
* Capa Silver:

  * `tb\\\_clientes\\\_core`: deduplicación por `id\\\_cli`, conversión de tipos (fechas, numéricos), enmascaramiento de `num\\\_doc` mediante hash SHA-256
  * `tb\\\_productos\\\_cat`: conversión de tipos
  * `tb\\\_mov\\\_financieros\\\_errores`: tabla de errores del pipeline que captura registros con `id\\\_cli`/`cod\\\_prod` inexistente en las dimensiones, o con fecha de movimiento fuera de rango (captura exitosamente la anomalía de fecha inyectada intencionalmente en la generación de datos)
  * `tb\\\_mov\\\_financieros`: deduplicación por `id\\\_mov` (elimina duplicados exactos inyectados intencionalmente), exclusión de registros inválidos, conversión de tipos
* Verificación de conteos: 10.000 clientes, 50 productos, \~500.000 movimientos válidos, al menos 1 registro en la tabla de errores — todo confirmado correcto

<!-- Próximas entradas se agregan aquí, una por cada día de trabajo -->

## \[2026-09-12] — Sábado — Capa Gold

**Autor:** Juan David Martinez Puello

* Se creó la base de datos `finbank\\\_gold` con el modelo dimensional:

  * `dim\\\_clientes`: nombre completo unificado, edad calculada, segmento legible
  * `dim\\\_productos`: tasa mensual equivalente calculada, clasificación por familia de producto
  * `fact\\\_transacciones`: monto convertido a USD (supuesto: 1 USD = 4000 COP), flag de horario hábil/no hábil, y regla de negocio `ind\\\_sospechoso`
  * `kpis\\\_diarios`: tabla de agregación por fecha/ciudad/canal (segunda vista de agregación, además de fact\_transacciones)
* Regla de negocio implementada: `ind\\\_sospechoso` marca una transacción cuando su monto supera en más de 3 desviaciones estándar el promedio histórico del cliente. Simplificación documentada: se usa el promedio histórico completo en vez de una ventana móvil exacta de 30 días, por tiempo disponible.
* Verificación: 10.000 clientes, 50 productos, 499.999 transacciones, 13.213 marcadas como sospechosas (\~2.6%, coherente con la distribución sesgada de los montos generados), 10.950 filas de KPIs diarios

## \[2026-09-12] — Sábado — Orquestación

**Autor:** Juan David Martinez Puello

* Se desarrolló `run\\\_pipeline.py`: orquestador del pipeline vía boto3 (API de Athena) que ejecuta Bronze → Silver → Gold en secuencia, con control de dependencias (si una capa falla, las siguientes no se ejecutan) y reintentos automáticos con backoff exponencial (hasta 3 intentos por sentencia)
* Se desarrolló `reset\\\_tables.py`: utilidad de soporte para limpiar el catálogo de tablas antes de una ejecución desde cero
* Se corrigió un bug detectado durante las pruebas: `CURRENT\\\_TIMESTAMP` generaba un tipo `timestamp with time zone` no soportado por el formato Parquet en Athena; se resolvió con `CAST(... AS VARCHAR)`
* Se identificó y documentó una limitación de idempotencia: el pipeline actual requiere limpieza manual de S3 antes de una re-ejecución completa, porque `DROP TABLE` en Athena no elimina los archivos subyacentes en S3. Mejora futura identificada: agregar limpieza automática de S3 al inicio del orquestador, o migrar a `INSERT OVERWRITE`/tablas Iceberg para lograr idempotencia real
* Ejecución completa verificada de punta a punta: BRONZE: OK, SILVER: OK, GOLD: OK — con evidencia de conteos consistentes tras la re-ejecución automatizada (10.000 clientes, 50 productos, 499.999 transacciones, 10.950 filas de KPIs)

## \[2026-09-13] — Domingo — Evidencias, documentación y cierre

**Autor:** Juan David Martinez Puello

* Se recibió información adicional de la empresa: el criterio de evaluación prioriza evidencia demostrable del manejo del entorno cloud sobre la perfección del código. Se ajustó el orden de trabajo del día para asegurar evidencia completa.
* Se capturó evidencia de ejecución real en AWS: estructura del bucket S3, catálogo de bases de datos en Athena, conteos de registros por capa, tabla de errores con datos reales, transacciones marcadas como sospechosas, y resumen de ejecución exitosa del orquestador — todo en `/docs/evidencias/`
* Se creó el diagrama Entidad-Relación (`/docs/diagrama\\\_er.md`, formato Mermaid) cubriendo el modelo de origen (Bronze) y el modelo dimensional (Gold)
* Se creó el catálogo de datos (`/docs/catalogo\\\_datos.md`) documentando cada tabla y campo de las capas Silver y Gold, incluyendo la identificación de 2 campos sensibles adicionales (`num\\\_cuenta`, `id\\\_dispositivo`) que quedaron identificados pero sin enmascarar, documentado como mejora pendiente honesta
* Se actualizó el README con la sección de evidencias y el resumen final de decisiones

