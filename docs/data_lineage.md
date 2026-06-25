# Linaje de datos

Este documento resume el origen y la transformación de los principales campos calculados en la capa Gold.

## Campos calculados principales

| Campo                      | Tabla destino       | Origen                                                                                              | Transformación                                                                                                                                                              | Uso                                                                       |
| -------------------------- | ------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `id_miembro_hash`          | `dim_clientes`      | `CRM_MIEMBROS.id_miembro`                                                                           | Se genera un hash SHA-256 estable a partir del identificador del cliente.                                                                                                   | Reducir exposición directa del identificador del cliente en la capa Gold. |
| `antiguedad_dias`          | `dim_clientes`      | `CRM_MIEMBROS.fecha_registro`                                                                       | Se calcula la diferencia en días entre la fecha de referencia del pipeline y la fecha de registro del cliente.                                                              | Analizar antigüedad de clientes.                                          |
| `margen_estimado_pct`      | `dim_productos`     | `MSTR_ARTICULOS.categoria`                                                                          | Se asigna un margen supuesto según la categoría del producto.                                                                                                               | Estimar margen cuando no existe costo unitario en las fuentes.            |
| `margen_estimado_valor`    | `dim_productos`     | `MSTR_ARTICULOS.precio_lista`, `margen_estimado_pct`                                                | Se calcula como `precio_lista * margen_estimado_pct`.                                                                                                                       | Estimar valor de margen por producto.                                     |
| `venta_bruta`              | `fact_ventas`       | `TRANS_VENTAS.qty_vendida`, `TRANS_VENTAS.precio_unitario_venta`                                    | Se calcula como `qty_vendida * precio_unitario_venta`.                                                                                                                      | Medir el valor de la venta antes de descuentos.                           |
| `vr_venta_neto`            | `fact_ventas`       | `TRANS_VENTAS.qty_vendida`, `TRANS_VENTAS.precio_unitario_venta`, `TRANS_VENTAS.descuento_aplicado` | Se calcula `venta_bruta = qty_vendida * precio_unitario_venta` y después `vr_venta_neto = venta_bruta - descuento_aplicado`. El resultado se limita a valores no negativos. | Medir el valor real de la venta después de descuentos.                    |
| `ind_venta_descuento`      | `fact_ventas`       | `TRANS_VENTAS.descuento_aplicado`                                                                   | Se marca como verdadero cuando el descuento aplicado es mayor a cero.                                                                                                       | Identificar ventas con descuento.                                         |
| `promedio_consumo_14dias`  | `fact_inventario`   | `INV_STOCK_DIARIO`, `TRANS_VENTAS`                                                                  | Se calcula el consumo promedio de los últimos 14 días por artículo y tienda.                                                                                                | Medir consumo reciente para inventario.                                   |
| `cobertura_dias`           | `fact_inventario`   | `INV_STOCK_DIARIO.stock_fisico`, `promedio_consumo_14dias`                                          | Se divide `stock_fisico / promedio_consumo_14dias`. Si no existe consumo reciente, la cobertura se deja controlada para evitar divisiones inválidas.                        | Estimar cuántos días puede cubrir el inventario actual.                   |
| `dif_vs_stock_minimo`      | `fact_inventario`   | `INV_STOCK_DIARIO.stock_fisico`, `INV_STOCK_DIARIO.stock_minimo`                                    | Se calcula como `stock_fisico - stock_minimo`.                                                                                                                              | Identificar inventario por encima o por debajo del mínimo esperado.       |
| `alerta_quiebre`           | `fact_inventario`   | `cobertura_dias`, `promedio_consumo_14dias`                                                         | Se marca como verdadero cuando la cobertura es menor a 7 días y existe consumo reciente.                                                                                    | Identificar riesgo de quiebre de stock.                                   |
| `tasa_devolucion_articulo` | `fact_devoluciones` | `POST_DEVOLUCIONES`, `fact_ventas`                                                                  | Se calcula la proporción de unidades devueltas respecto a las unidades vendidas por artículo.                                                                               | Analizar comportamiento de devoluciones por producto.                     |
| `recencia`                 | `fact_rfm_clientes` | `fact_ventas.fec_trans`                                                                             | Se calcula la cantidad de días desde la última compra del cliente hasta la fecha de referencia.                                                                             | Medir qué tan reciente fue la última compra.                              |
| `frecuencia`               | `fact_rfm_clientes` | `fact_ventas.id_trans`                                                                              | Se cuenta el número de transacciones por cliente.                                                                                                                           | Medir frecuencia de compra.                                               |
| `valor_monetario`          | `fact_rfm_clientes` | `fact_ventas.vr_venta_neto`                                                                         | Se suma el valor neto de ventas por cliente.                                                                                                                                | Medir valor económico del cliente.                                        |
| `segmento_rfm`             | `fact_rfm_clientes` | `recencia`, `frecuencia`, `valor_monetario`                                                         | Se asignan scores de 1 a 5 y se combinan en formato `R#-F#-M#`.                                                                                                             | Segmentar clientes según comportamiento de compra.                        |

## Linaje por capa

```text
Bronze
  └── Tablas fuente sintéticas en CSV

Silver
  └── Limpieza, tipado, estandarización, validación de fechas y tratamiento de nulos

Gold
  ├── Dimensiones: productos, tiendas y clientes
  ├── Hechos: ventas, inventario, devoluciones y RFM
  └── KPIs: ventas diarias y top artículos por categoría
```

## Salida particionada

Además de las salidas Gold principales, se agregó una muestra separada de salida particionada para `kpi_ventas_diarias`.

```text
data/gold_partitioned/kpi_ventas_diarias/
```

La partición se genera por:

```text
year
month
```

La evidencia se encuentra en:

```text
docs/evidence/partitioned_outputs_summary.txt
```

Esta salida particionada se genera como parte del flujo orquestado del pipeline y sirve como evidencia de optimización de consumo analítico por periodo.

## Nota

Este linaje se enfoca en los campos calculados más relevantes para la prueba técnica. En un entorno productivo, el linaje podría mantenerse en una herramienta especializada de gobierno de datos.
