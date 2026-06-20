# Catálogo de datos

Este catálogo resume las tablas principales del proyecto RetailMax y su uso dentro del pipeline.

## Capas del pipeline

| Capa | Descripción | Formato |
|---|---|---|
| Bronze | Datos fuente generados de forma sintética. | CSV |
| Silver | Datos limpios, tipados y estandarizados. | Parquet |
| Gold | Modelo analítico con dimensiones, hechos y KPIs. | Parquet |

## Tablas Bronze / Silver

| Tabla | Descripción | Origen | Sensible |
|---|---|---|---|
| `MSTR_PROVEEDORES` | Catálogo de proveedores. | Generación sintética | No |
| `MSTR_ARTICULOS` | Catálogo de artículos, categorías y precios. | Generación sintética | No |
| `MSTR_TIENDAS` | Catálogo de tiendas. | Generación sintética | No |
| `CRM_MIEMBROS` | Información de miembros/clientes. | Generación sintética | Sí |
| `TRANS_VENTAS` | Transacciones de venta. | Generación sintética | Sí |
| `INV_STOCK_DIARIO` | Inventario diario por artículo y tienda. | Generación sintética | No |
| `POST_DEVOLUCIONES` | Devoluciones asociadas a ventas. | Generación sintética | No |

## Tablas Gold

| Tabla | Descripción | Uso principal | Sensible |
|---|---|---|---|
| `dim_productos` | Dimensión de productos con categorías, proveedor y margen estimado. | Análisis por producto y categoría. | No |
| `dim_tiendas` | Dimensión de tiendas con país, ciudad y zona de distribución. | Análisis geográfico y operativo. | No |
| `dim_clientes` | Dimensión de clientes con hash de identificador, género, edad y antigüedad. | Segmentación de clientes. | Sí |
| `fact_ventas` | Hechos de ventas con venta bruta, venta neta y descuentos. | Análisis de ventas. | Sí |
| `fact_inventario` | Hechos de inventario con cobertura y alerta de quiebre. | Seguimiento de inventario. | No |
| `fact_devoluciones` | Hechos de devoluciones con motivo y tasa por artículo. | Análisis de devoluciones. | No |
| `fact_rfm_clientes` | Segmentación RFM de clientes activos. | Análisis de comportamiento de clientes. | Sí |
| `kpi_ventas_diarias` | KPIs diarios por fecha, país, canal y categoría. | Dashboard ejecutivo. | No |
| `kpi_top_articulos_categoria` | Top 10 artículos por categoría. | Ranking de productos. | No |

## Campos sensibles

| Campo | Tabla | Motivo | Tratamiento |
|---|---|---|---|
| `id_miembro` | `CRM_MIEMBROS`, `TRANS_VENTAS`, `dim_clientes`, `fact_ventas` | Identificador de cliente. | Se conserva para integridad, pero se agrega `id_miembro_hash` en Gold. |
| `id_miembro_hash` | `dim_clientes` | Identificador anonimizado. | Hash SHA-256 estable. |
| `genero` | `dim_clientes` | Atributo demográfico. | Se estandariza a `M`, `F` o `No informado`. |
| `rango_edad` | `dim_clientes` | Atributo demográfico. | Se imputa cuando viene nulo. |

## Campos calculados principales

| Campo | Tabla | Descripción |
|---|---|---|
| `venta_bruta` | `fact_ventas` | `qty_vendida * precio_unitario_venta`. |
| `vr_venta_neto` | `fact_ventas` | Venta bruta menos descuento aplicado. |
| `ind_venta_descuento` | `fact_ventas` | Indica si la venta tuvo descuento. |
| `antiguedad_dias` | `dim_clientes` | Días desde la fecha de registro del cliente. |
| `margen_estimado_pct` | `dim_productos` | Margen supuesto por categoría. |
| `margen_estimado_valor` | `dim_productos` | Precio de lista multiplicado por margen estimado. |
| `promedio_consumo_14dias` | `fact_inventario` | Consumo promedio reciente por artículo y tienda. |
| `cobertura_dias` | `fact_inventario` | Días estimados de cobertura de inventario. |
| `alerta_quiebre` | `fact_inventario` | Indica riesgo de quiebre de stock. |
| `tasa_devolucion_articulo` | `fact_devoluciones` | Proporción de unidades devueltas por artículo. |
| `segmento_rfm` | `fact_rfm_clientes` | Segmento construido con recencia, frecuencia y valor monetario. |

## Nota

Este catálogo es una versión básica para la prueba técnica. En un entorno productivo, podría mantenerse en una herramienta de catálogo o gobierno de datos.