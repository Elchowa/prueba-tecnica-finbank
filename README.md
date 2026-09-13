# Prueba Técnica — Ingeniero de Datos — FinBank Pipeline

## Declaración inicial de decisiones

**Sector elegido:** Escenario A — Banca y Servicios Financieros (FinBank S.A.)

**Plataforma cloud elegida:** Amazon Web Services (S3 + Athena)

### Justificación de la plataforma

Se evaluaron tres plataformas antes de llegar a esta decisión:

1. **Microsoft Fabric** — descartada porque la creación de cuenta fue bloqueada por un filtro antifraude de Microsoft al intentar registrar una cuenta personal nueva.
2. **Google Cloud Platform (BigQuery)** — descartada porque la creación de la cuenta de facturación falló con el error `OR-CBAT-23`, un error del sistema de verificación de pagos de Google.
3. **Amazon AWS (S3 + Athena)** — plataforma finalmente utilizada. El registro se completó sin inconvenientes. Se eligió Athena sobre otras opciones de procesamiento (EMR, Glue con clusters) por ser completamente serverless, evitando costos por infraestructura inactiva y permitiendo trabajar con SQL estándar sobre los datos almacenados en S3, sin necesidad de gestionar clusters.

### Alcance de la solución

Dado el plazo real disponible (4 días hábiles desde la recepción del documento hasta la fecha límite), se priorizó **construir un pipeline funcional y coherente de punta a punta (Bronze → Silver → Gold)** sobre intentar cubrir el 100% de los requisitos opcionales del documento. Las decisiones de alcance específicas son:

* Se trabajó con **3 de las 6 tablas fuente**: `TB\\\_CLIENTES\\\_CORE`, `TB\\\_PRODUCTOS\\\_CAT` y `TB\\\_MOV\\\_FINANCIEROS`. Las tablas `TB\\\_OBLIGACIONES`, `TB\\\_SUCURSALES\\\_RED` y `TB\\\_COMISIONES\\\_LOG` quedaron fuera de alcance por tiempo. Se incorporarían siguiendo el mismo patrón de generación y carga ya implementado para las 3 tablas actuales, hubo un cumplimiento del volumen minimo de registros solicitados, dando como resultado una reduccion de alcance unicamente en la cantidad de tablas esperadas (3/6), no en el volumen de estas.
* Se implementó **ingesta full load** (no incremental). El modo incremental es la mejora natural siguiente: se abordaría comparando `fec\\\_mov`/`fec\\\_alta` contra la última fecha de ejecución registrada en una tabla de control.
* El **gobierno de datos** (roles diferenciados, permisos IAM granulares) se documenta como diseño en la sección correspondiente, sin implementación completa por prioridad de tiempo sobre el pipeline funcional.
* La **infraestructura** (bucket S3, bases de datos de Athena) se creó vía consola/UI de AWS en lugar de con una herramienta de IaC como Terraform, dado el tiempo disponible. La rúbrica del documento contempla explícitamente "UI" como opción válida de aprovisionamiento.

## Arquitectura

```
Generación de datos (Python) 
        │
        ▼
   S3: bronze/  (datos crudos + columnas de auditoría)
        │
        ▼
   Athena: finbank\\\_silver  (limpieza, deduplicación, enmascaramiento)
        │
        ▼
   Athena: finbank\\\_gold  (modelo dimensional + reglas de negocio)
```

## Estructura del repositorio

```
/data-generation   → script de generación de datos sintéticos
/pipelines         → consultas SQL de las capas Silver y Gold
/orchestration     → documentación/script del orden de ejecución
/docs              → diagrama ER y catálogo de datos
README.md
CHANGELOG.md
```

## Cómo ejecutar

1. Ejecutar `python data-generation/generate\\\_data.py` para generar los CSV
2. Subir los CSV generados a `s3://<nombre-bucket>/bronze/`
3. En Athena, ejecutar las consultas de `/pipelines` en orden: Bronze → Silver → Gold
4. Los resultados de Gold quedan disponibles como tablas consultables directamente en Athena

## Reglas de negocio implementadas

* `ind\\\_sospechoso`: se marca una transacción como sospechosa cuando su monto (`vr\\\_mov`) supera en más de 3 desviaciones estándar el promedio de los últimos 30 días del mismo cliente.

