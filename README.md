# Prueba Técnica — Ingeniero de Datos — FinBank Pipeline

## Declaración inicial de decisiones

**Sector elegido:** Escenario A — Banca y Servicios Financieros (FinBank S.A.)

**Plataforma cloud elegida:** Amazon Web Services (S3 + Athena)

### Justificación de la plataforma

Se evaluaron tres plataformas antes de llegar a esta decisión:

1. **Microsoft Fabric** — descartada porque la creación de cuenta fue bloqueada por un filtro antifraude de Microsoft al intentar registrar una cuenta personal nueva.
2. **Google Cloud Platform (BigQuery)** — descartada porque la creación de la cuenta de facturación falló repetidamente con el error `OR-CBAT-23` del sistema de verificación de pagos de Google.
3. **Amazon AWS (S3 + Athena)** — plataforma finalmente utilizada. El registro se completó sin inconvenientes. Se eligió Athena sobre otras opciones de procesamiento (EMR, Glue con clusters) por ser completamente serverless, evitando costos por infraestructura inactiva y permitiendo trabajar con SQL estándar sobre los datos almacenados en S3, sin necesidad de gestionar clusters.

### Principio de trabajo de esta entrega

Dado el plazo real disponible (recepción del documento un miércoles, con entrega el lunes siguiente), esta solución se guio por un principio deliberado: **es preferible entregar un alcance más pequeño pero completamente funcional y bien entendido, que un alcance más amplio a medias o simulado.** Cada recorte de alcance frente al documento original está documentado explícitamente abajo, junto con cómo se abordaría con más tiempo — no se oculta ninguna limitación.

### Alcance de la solución

* Se trabajó con **3 de las 6 tablas fuente**: `TB\\\_CLIENTES\\\_CORE`, `TB\\\_PRODUCTOS\\\_CAT` y `TB\\\_MOV\\\_FINANCIEROS`, **con el volumen mínimo de registros exigido por el documento** (10.000, 50 y 500.000 respectivamente). Las tablas `TB\\\_OBLIGACIONES`, `TB\\\_SUCURSALES\\\_RED` y `TB\\\_COMISIONES\\\_LOG` quedaron fuera de alcance por tiempo. Se incorporarían siguiendo el mismo patrón de generación y carga ya implementado para las 3 tablas actuales.
* Se implementó **ingesta full load** (no incremental). El modo incremental es la mejora natural siguiente: se abordaría comparando `fec\\\_mov`/`fec\\\_alta` contra la última fecha de ejecución registrada en una tabla de control.
* El **gobierno de datos** (roles diferenciados, permisos IAM granulares) se documenta como diseño en la sección correspondiente, sin implementación completa por prioridad de tiempo sobre el pipeline funcional.
* La **infraestructura** (bucket S3, bases de datos de Athena) se creó vía consola/UI de AWS en lugar de con una herramienta de IaC como Terraform, dado el tiempo disponible. La rúbrica del documento contempla explícitamente "UI" como opción válida de aprovisionamiento.
* El pipeline **no es 100% idempotente todavía**: una re-ejecución completa desde cero requiere limpiar manualmente los datos previos en S3, porque `DROP TABLE` en Athena no elimina los archivos subyacentes. Se identificó y documentó esta limitación durante las pruebas (ver sección de Orquestación).

## Arquitectura

```
Generación de datos sintéticos (Python, semilla fija)
        │
        ▼
   S3: bronze/  (datos crudos + columnas de auditoría, tablas externas en Athena)
        │
        ▼
   Athena: finbank\\\_silver
     - Deduplicación, tipado, enmascaramiento de datos sensibles (hash SHA-256)
     - Tabla de errores (integridad referencial + validación de fechas)
        │
        ▼
   Athena: finbank\\\_gold
     - Modelo dimensional (dim\\\_clientes, dim\\\_productos)
     - fact\\\_transacciones (con regla de negocio ind\\\_sospechoso)
     - kpis\\\_diarios (tabla de agregación)
        │
        ▼
   Orquestación: run\\\_pipeline.py (boto3) — ejecuta las 3 capas con
   control de dependencias y reintentos automáticos
```

## Estructura del repositorio

```
/data-generation
    generate\\\_data.py       → genera los datos sintéticos con semilla fija (42)
/pipelines
    bronze\\\_ddl.sql          → tablas externas de la capa Bronze
    silver\\\_ctas.sql          → limpieza, deduplicación, enmascaramiento, tabla de errores
    gold\\\_ctas.sql             → modelo dimensional y reglas de negocio
/orchestration
    run\\\_pipeline.py          → orquestador con reintentos y control de dependencias
    reset\\\_tables.py          → utilidad para reiniciar el pipeline desde cero
/docs
    (diagrama ER y catálogo de datos)
README.md
CHANGELOG.md
```

## Cómo ejecutar

1. `python data-generation/generate\\\_data.py` genera los 3 CSV (10.000 clientes, 50 productos, 500.000 movimientos)
2. Subir los CSV a `s3://<bucket>/bronze/<nombre\\\_tabla>/` (cada tabla en su propia carpeta)
3. Desde AWS CloudShell (o cualquier entorno con boto3 y credenciales de AWS configuradas):

```
   cd orchestration
   python3 run\\\_pipeline.py
   ```

Esto ejecuta Bronze → Silver → Gold en orden, deteniéndose si alguna capa falla.

4. Para una ejecución completamente limpia desde cero: correr primero `reset\\\_tables.py`, luego borrar manualmente el contenido de `silver/` y `gold/` en S3, y después `run\\\_pipeline.py` (ver limitación de idempotencia arriba).

## Reglas de negocio implementadas

* **`ind\\\_sospechoso`** (en `fact\\\_transacciones`): marca una transacción como sospechosa cuando su monto supera en más de 3 desviaciones estándar el promedio histórico del cliente.
*Simplificación documentada:* el documento original pide una ventana móvil exacta de los últimos 30 días; esta implementación usa el promedio histórico completo del cliente en lugar de una ventana móvil, por simplicidad de cálculo dado el tiempo disponible. Con más tiempo, se implementaría con una función de ventana `RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND CURRENT ROW`.
* **`kpis\\\_diarios`**: tabla de agregación por fecha, ciudad y canal (total de transacciones, monto total, monto promedio, conteo de transacciones sospechosas) — segunda vista de agregación, además de `fact\\\_transacciones`.

## Calidad de datos y manejo de errores

* La tabla `finbank\\\_silver.tb\\\_mov\\\_financieros\\\_errores` captura registros que fallan validación: `id\\\_cli` o `cod\\\_prod` inexistente en las dimensiones, o fecha de movimiento fuera de rango. Esto captura exitosamente una anomalía de fecha inyectada intencionalmente durante la generación de datos (`fec\\\_mov = '2099-01-01'`).
* Se inyectaron y se eliminaron correctamente duplicados exactos intencionales en `tb\\\_mov\\\_financieros` (deduplicación por `id\\\_mov` en la capa Silver).
* Enmascaramiento de `num\\\_doc` (número de documento del cliente) mediante hash SHA-256, aplicado desde la capa Silver en adelante — el dato original nunca llega a Gold.

## Orquestación

`run\\\_pipeline.py` ejecuta las 3 capas del pipeline vía la API de Athena (boto3), leyendo directamente los archivos `.sql` de `/pipelines`. Incluye:

* **Control de dependencias:** si la capa Bronze falla, Silver y Gold no se ejecutan; si Silver falla, Gold no se ejecuta.
* **Reintentos automáticos:** hasta 3 intentos por sentencia, con espera creciente (backoff exponencial: 5s, 10s, 20s).
* **Resumen final de ejecución:** estado de cada capa y tiempo total.

Se verificó una ejecución completa exitosa de punta a punta (BRONZE: OK, SILVER: OK, GOLD: OK, \~40 segundos de ejecución total), con conteos consistentes tras la reejecución.



**No implementado por tiempo** (documentado como diseño pendiente): programación automática diaria (se haría con Amazon EventBridge disparando este mismo script), alertas por correo/Slack ante fallos (se integraría con Amazon SNS), y un dashboard de monitoreo de ejecuciones históricas (se usaría CloudWatch Logs sobre los prints del propio script, o una tabla de logs de ejecución en el propio Athena).

## Gobierno de datos (diseño, no implementado)

Dado el tiempo disponible, esta sección queda a nivel de diseño documentado:

* **Ingeniero de Datos:** acceso de lectura/escritura a las 3 capas (Bronze, Silver, Gold). En AWS, se implementaría con un rol IAM dedicado con permisos `s3:\\\*` y `athena:\\\*` sobre el bucket y las bases de datos del proyecto.
* **Analista:** acceso de solo lectura a la capa Gold únicamente. Se implementaría con una política IAM que otorgue `athena:GetQueryResults` y `s3:GetObject` solo sobre `gold/`, denegando explícitamente acceso a `bronze/` y `silver/`.
* **Administrador:** control total sobre los recursos del proyecto (rol IAM con acceso administrativo al bucket y a Athena).
* **Principio de mínimo privilegio:** cada rol tendría únicamente los permisos estrictamente necesarios para su función, siguiendo el patrón estándar de IAM de AWS.



## Evidencias

Capturas de pantalla de la ejecución real en AWS disponibles en `/docs/evidencias/`

