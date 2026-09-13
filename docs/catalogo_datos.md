# Catálogo de Datos — FinBank Pipeline

Catálogo de las tablas en las capas Silver y Gold, según lo requiere el documento de la prueba técnica.

## Capa Silver — `finbank_silver`

### `tb_clientes_core`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| id_cli | INTEGER | TB_CLIENTES_CORE.id_cli | No |
| nomb_cli | STRING | TB_CLIENTES_CORE.nomb_cli | No |
| apell_cli | STRING | TB_CLIENTES_CORE.apell_cli | No |
| tip_doc | STRING | TB_CLIENTES_CORE.tip_doc | No |
| num_doc_hash | STRING | TB_CLIENTES_CORE.num_doc (enmascarado con SHA-256) | Sí (derivado de dato sensible) |
| fec_nac | DATE | TB_CLIENTES_CORE.fec_nac | No |
| fec_alta | DATE | TB_CLIENTES_CORE.fec_alta | No |
| cod_segmento | STRING | TB_CLIENTES_CORE.cod_segmento | No |
| score_buro | DOUBLE | TB_CLIENTES_CORE.score_buro | No |
| ciudad_res / depto_res | STRING | TB_CLIENTES_CORE | No |
| estado_cli | STRING | TB_CLIENTES_CORE.estado_cli | No |
| canal_adquis | STRING | TB_CLIENTES_CORE.canal_adquis | No |

### `tb_productos_cat`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| cod_prod | INTEGER | TB_PRODUCTOS_CAT.cod_prod | No |
| desc_prod / tip_prod | STRING | TB_PRODUCTOS_CAT | No |
| tasa_ea | DOUBLE | TB_PRODUCTOS_CAT.tasa_ea | No |
| plazo_max_meses | INTEGER | TB_PRODUCTOS_CAT.plazo_max_meses | No |
| cuota_min / comision_admin | DOUBLE | TB_PRODUCTOS_CAT | No |
| estado_prod | STRING | TB_PRODUCTOS_CAT.estado_prod | No |

### `tb_mov_financieros`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| id_mov | INTEGER | TB_MOV_FINANCIEROS.id_mov | No |
| id_cli | INTEGER | TB_MOV_FINANCIEROS.id_cli (FK a tb_clientes_core) | No |
| cod_prod | INTEGER | TB_MOV_FINANCIEROS.cod_prod (FK a tb_productos_cat) | No |
| num_cuenta | STRING | TB_MOV_FINANCIEROS.num_cuenta | Sí (identificador de cuenta) |
| fec_mov / hra_mov | DATE / STRING | TB_MOV_FINANCIEROS | No |
| vr_mov | DOUBLE | TB_MOV_FINANCIEROS.vr_mov | No |
| tip_mov / cod_canal / cod_ciudad | STRING | TB_MOV_FINANCIEROS | No |
| cod_estado_mov | STRING | TB_MOV_FINANCIEROS.cod_estado_mov | No |
| id_dispositivo | STRING | TB_MOV_FINANCIEROS.id_dispositivo | Sí (identificador de dispositivo) |

### `tb_mov_financieros_errores`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| id_mov, id_cli, cod_prod, fec_mov, vr_mov | (igual que tb_mov_financieros) | TB_MOV_FINANCIEROS | No |
| motivo_error | STRING | Calculado (regla de validación) | No |
| fecha_deteccion | STRING | Calculado (CURRENT_TIMESTAMP) | No |

## Capa Gold — `finbank_gold`

### `dim_clientes`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| id_cli | INTEGER | Silver.tb_clientes_core.id_cli | No |
| nombre_completo | STRING | Calculado: nomb_cli + apell_cli | No |
| num_doc_hash | STRING | Silver.tb_clientes_core.num_doc_hash | Sí (derivado de dato sensible) |
| edad | INTEGER | Calculado: DATE_DIFF(fec_nac, hoy) | No |
| segmento | STRING | Silver.cod_segmento | No |
| score_buro, ciudad_res, estado_cli | (varios) | Silver.tb_clientes_core | No |

### `dim_productos`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| cod_prod | INTEGER | Silver.tb_productos_cat.cod_prod | No |
| descripcion_producto, tipo_producto | STRING | Silver.tb_productos_cat | No |
| tasa_efectiva_anual | DOUBLE | Silver.tasa_ea | No |
| tasa_mensual_equivalente | DOUBLE | Calculado: (1+tasa_ea)^(1/12)-1 | No |
| familia_producto | STRING | Calculado: clasificación por tip_prod | No |

### `fact_transacciones`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| id_mov | INTEGER | Silver.tb_mov_financieros.id_mov | No |
| id_cli | INTEGER | Silver.tb_mov_financieros.id_cli (FK a dim_clientes) | No |
| cod_prod | INTEGER | Silver.tb_mov_financieros.cod_prod (FK a dim_productos) | No |
| vr_mov | DOUBLE | Silver.tb_mov_financieros.vr_mov | No |
| monto_usd | DOUBLE | Calculado: vr_mov / 4000 (supuesto de tasa de cambio) | No |
| flag_horario | STRING | Calculado: hora hábil (6-22h) o no hábil | No |
| ind_sospechoso | BOOLEAN | Calculado: monto > promedio histórico del cliente + 3 desviaciones estándar | No |

### `kpis_diarios`
| Campo | Tipo | Origen | ¿Sensible? |
|---|---|---|---|
| fecha, ciudad, canal | (varios) | Agregado desde fact_transacciones | No |
| total_transacciones, monto_total, monto_promedio | (varios) | Calculado (agregación) | No |
| transacciones_sospechosas | INTEGER | Calculado: conteo de ind_sospechoso = true | No |

## Resumen de datos sensibles identificados

| Campo original | Tratamiento aplicado | Capa donde se aplica |
|---|---|---|
| num_doc (número de documento) | Hash SHA-256 → `num_doc_hash` | Silver en adelante |
| num_cuenta | Identificado como sensible, **no enmascarado aún** (mejora pendiente documentada) | — |
| id_dispositivo | Identificado como sensible, **no enmascarado aún** (mejora pendiente documentada) | — |

*Nota: por tiempo, solo `num_doc` fue efectivamente enmascarado, que era el ejemplo explícito mencionado en el documento de la prueba. `num_cuenta` e `id_dispositivo` quedan identificados como sensibles pero sin enmascarar — se aplicaría el mismo patrón de hash SHA-256 usado en `num_doc` con más tiempo disponible.*
