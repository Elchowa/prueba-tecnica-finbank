# CHANGELOG

Historial de cambios del proyecto — Prueba Técnica Ingeniero de Datos (FinBank Pipeline)

## \[2026-09-9] — Miércoles — Setup inicial

**Autor:** Juan David Martinez Puello

* Se evaluaron 3 plataformas cloud: Microsoft Fabric (bloqueada por filtro antifraude en creación de cuenta), Google Cloud Platform (bloqueada por error en creación de cuenta de facturación), y Amazon AWS (registro exitoso, plataforma elegida).
* Se definió el escenario de negocio: Escenario A — Banca y Servicios Financieros (FinBank S.A.)
* Se creó la estructura base del repositorio: `/data-generation`, `/pipelines`, `/orchestration`, `/docs`
* Se creó el bucket S3 con las carpetas `bronze/`, `silver/`, `gold/`
* Se desarrolló y validó `generate\\\_data.py`: script de generación de datos sintéticos con semilla fija (42), cubriendo 3 de las 6 tablas fuente (`TB\\\_CLIENTES\\\_CORE`, `TB\\\_PRODUCTOS\\\_CAT`, `TB\\\_MOV\\\_FINANCIEROS`), con integridad referencial verificada, \~5% de nulos controlados, y 2 anomalías intencionales (duplicados, fecha fuera de rango)
* Se redactó la primera versión del README.md con la justificación de sector, plataforma y alcance
* Se ajustaron los volúmenes de datos generados a los mínimos exigidos por el documento: 10.000 clientes, 50 productos, 500.000 movimientos

## \[2026-09-/10] — Capa Bronze y Silver

**Autor:** Juan David Martinez Puello

* Capa Bronze: se crearon las 3 tablas externas en Athena (`finbank\\\_bronze.tb\\\_clientes\\\_core`, `tb\\\_productos\\\_cat`, `tb\\\_mov\\\_financieros`) sobre los datos crudos en S3, usando `OpenCSVSerde` con todas las columnas tipadas como STRING (patrón estándar de Bronze: se preserva el dato crudo sin forzar conversión de tipos, dejando esa responsabilidad a la capa Silver)
* Capa Silver:

  * `tb\\\_clientes\\\_core`: deduplicación por `id\\\_cli`, conversión de tipos (fechas, numéricos), enmascaramiento de `num\\\_doc` mediante hash SHA-256
  * `tb\\\_productos\\\_cat`: conversión de tipos
  * `tb\\\_mov\\\_financieros\\\_errores`: tabla de errores del pipeline que captura registros con `id\\\_cli`/`cod\\\_prod` inexistente en las dimensiones, o con fecha de movimiento fuera de rango (captura exitosamente la anomalía de fecha inyectada intencionalmente en la generación de datos)
  * `tb\\\_mov\\\_financieros`: deduplicación por `id\\\_mov` (elimina duplicados exactos inyectados intencionalmente), exclusión de registros inválidos, conversión de tipos
* Verificación de conteos: 10.000 clientes, 50 productos, \~500.000 movimientos válidos, al menos 1 registro en la tabla de errores — todo confirmado correcto

## \[2026-09-12] — Sábado — Capa Gold

**Autor:** Juan David Martinez Puello

* Se creó la base de datos `finbank\\\_gold` con el modelo dimensional:

  * `dim\\\_clientes`: nombre completo unificado, edad calculada, segmento legible
  * `dim\\\_productos`: tasa mensual equivalente calculada, clasificación por familia de producto
  * `fact\\\_transacciones`: monto convertido a USD (supuesto: 1 USD = 4000 COP), flag de horario hábil/no hábil, y regla de negocio `ind\\\_sospechoso`
  * `kpis\\\_diarios`: tabla de agregación por fecha/ciudad/canal (segunda vista de agregación, además de fact\_transacciones)
* Regla de negocio implementada: `ind\\\_sospechoso` marca una transacción cuando su monto supera en más de 3 desviaciones estándar el promedio histórico del cliente. Simplificación documentada: se usa el promedio histórico completo en vez de una ventana móvil exacta de 30 días, por tiempo disponible.
* Verificación: 10.000 clientes, 50 productos, 499.999 transacciones, 13.213 marcadas como sospechosas (\~2.6%, coherente con la distribución sesgada de los montos generados), 10.950 filas de KPIs diarios

