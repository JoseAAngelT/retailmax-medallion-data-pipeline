# Linaje de datos

Este documento resume el linaje de algunos campos calculados en la capa Gold.

El objetivo es explicar de dónde viene cada campo, qué transformación se aplica y para qué sirve en el análisis del negocio.

## Campos documentados

| Campo Gold | Tabla Gold | Origen | Transformación | Propósito |
|---|---|---|---|---|
| `vr_venta_neto` | `fact_ventas` | `TRANS_VENTAS.qty_vendida`, `TRANS_VENTAS.precio_unitario_venta`, `TRANS_VENTAS.descuento_aplicado` | Se calcula `venta_bruta = qty_vendida * precio_unitario_venta` y después `vr_venta_neto = venta_bruta - descuento_aplicado`. El resultado se limita a valores no negativos. | Medir el valor real de la venta después de descuentos. |
| `cobertura_dias` | `fact_inventario` | `INV_STOCK_DIARIO.stock_fisico`, `TRANS_VENTAS.qty_vendida` | Se calcula el consumo promedio de los últimos 14 días por artículo y tienda. Después se divide `stock_fisico / promedio_consumo_14dias`. | Estimar cuántos días puede cubrir el inventario actual. |
| `alerta_quiebre` | `fact_inventario` | `cobertura_dias`, `promedio_consumo_14dias` | Se marca como verdadero cuando la cobertura es menor a 7 días y existe consumo reciente. | Identificar riesgo de quiebre de stock. |
| `tasa_devolucion_articulo` | `fact_devoluciones` | `POST_DEVOLUCIONES.qty_devuelta`, `fact_ventas.qty_vendida` | Se calcula `unidades_devueltas / unidades_vendidas` por artículo. | Medir qué proporción de unidades vendidas fueron devueltas. |
| `segmento_rfm` | `fact_rfm_clientes` | `fact_ventas.fec_trans`, `fact_ventas.id_trans`, `fact_ventas.vr_venta_neto` | Se calculan recencia, frecuencia y valor monetario. Luego se asignan scores de 1 a 5 y se combinan en formato `R#-F#-M#`. | Segmentar clientes según comportamiento reciente de compra. |

## Notas

- Los campos calculados se generan en `src/gold_transform.py`.
- Las validaciones principales se ejecutan en `src/quality_checks.py`.
- El pipeline usa `quality_checks_summary.txt` como evidencia de aprobación de reglas básicas de calidad.