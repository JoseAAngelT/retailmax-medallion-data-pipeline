# Data Model

La capa Gold contiene dimensiones, tablas de hechos y salidas KPI para análisis.

```mermaid
erDiagram
    dim_clientes ||--o{ fact_ventas : "id_miembro"
    dim_productos ||--o{ fact_ventas : "art_id"
    dim_tiendas ||--o{ fact_ventas : "id_tienda"

    dim_productos ||--o{ fact_inventario : "art_id"
    dim_tiendas ||--o{ fact_inventario : "id_tienda"

    fact_ventas ||--o{ fact_devoluciones : "id_trans"
    dim_productos ||--o{ fact_devoluciones : "art_id"
    dim_tiendas ||--o{ fact_devoluciones : "id_tienda"

    dim_clientes ||--o{ fact_rfm_clientes : "id_miembro"

    dim_clientes {
        int id_miembro
        string id_miembro_hash
        string genero
        string rango_edad
        string canal_pref
        int antiguedad_dias
    }

    dim_productos {
        int art_id
        string desc_art
        string categoria_n1
        string categoria_n2
        string categoria_n3
        float precio_lista
        float margen_estimado_pct
    }

    dim_tiendas {
        int id_tienda
        string nom_tienda
        string tipo_tienda
        string id_ciudad
        string id_pais
        string zona_distribucion_asignada
    }

    fact_ventas {
        int id_trans
        int id_miembro
        int id_tienda
        int art_id
        date fec_trans
        int qty_vendida
        float vr_venta_neto
        boolean ind_venta_descuento
    }

    fact_inventario {
        int id_snapshot
        int art_id
        int id_tienda
        date fec_snapshot
        int stock_fisico
        float promedio_consumo_14dias
        float cobertura_dias
        boolean alerta_quiebre
    }

    fact_devoluciones {
        int id_devolucion
        int id_trans_origen
        int art_id
        int id_tienda
        date fec_devolucion
        int qty_devuelta
        float tasa_devolucion_articulo
    }

    fact_rfm_clientes {
        int id_miembro
        int recencia_dias
        int frecuencia_90d
        float valor_monetario_90d
        string segmento_rfm
    }
```

## Salidas KPI

Además del modelo dimensional principal, la capa Gold genera dos salidas analíticas agregadas:

| Tabla | Descripción | Uso |
|---|---|---|
| `kpi_ventas_diarias` | Ventas agregadas por fecha, país, canal y categoría. | Seguimiento diario de ventas y análisis ejecutivo. |
| `kpi_top_articulos_categoria` | Top 10 artículos por categoría según ventas. | Identificar productos principales por categoría. |

Estas tablas se generan a partir de `fact_ventas` y dimensiones relacionadas. No se incluyen como entidades principales del diagrama ER porque son salidas agregadas para consumo analítico.