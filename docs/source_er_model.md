# Source ER Model

Este diagrama representa las relaciones principales entre las tablas fuente generadas para el escenario Retail.

```mermaid
erDiagram
    MSTR_PROVEEDORES ||--o{ MSTR_ARTICULOS : "id_proveedor"
    MSTR_ARTICULOS ||--o{ TRANS_VENTAS : "art_id"
    MSTR_TIENDAS ||--o{ TRANS_VENTAS : "id_tienda"
    CRM_MIEMBROS ||--o{ TRANS_VENTAS : "id_miembro"

    MSTR_ARTICULOS ||--o{ INV_STOCK_DIARIO : "art_id"
    MSTR_TIENDAS ||--o{ INV_STOCK_DIARIO : "id_tienda"

    TRANS_VENTAS ||--o{ POST_DEVOLUCIONES : "id_trans_origen"
    MSTR_ARTICULOS ||--o{ POST_DEVOLUCIONES : "art_id"
    MSTR_TIENDAS ||--o{ POST_DEVOLUCIONES : "id_tienda"

    MSTR_PROVEEDORES {
        int id_proveedor
        string razon_social
        string pais_origen
        int tiempo_repo_dias
        float calificacion_calidad
        boolean activo
    }

    MSTR_ARTICULOS {
        int art_id
        string cod_barra
        string desc_art
        string id_categ_n1
        string id_categ_n2
        string id_categ_n3
        int id_proveedor
        float precio_lista
        float peso_kg
        string unid_medida
        boolean activo
        date fec_alta
    }

    MSTR_TIENDAS {
        int id_tienda
        string nom_tienda
        string tipo_tienda
        string id_ciudad
        string id_pais
        int metros_cuadrados
        boolean activo
        date fec_apertura
    }

    CRM_MIEMBROS {
        int id_miembro
        date fec_registro
        string id_ciudad
        string genero
        string rango_edad
        string canal_pref
        boolean activo
        date fec_ultima_compra
    }

    TRANS_VENTAS {
        int id_trans
        int id_miembro
        int id_tienda
        int art_id
        date fec_trans
        string hra_trans
        int qty_vendida
        float precio_unitario_venta
        float descuento_aplicado
        string tipo_pago
        string canal_venta
    }

    INV_STOCK_DIARIO {
        int id_snapshot
        int art_id
        int id_tienda
        date fec_snapshot
        int stock_fisico
        int stock_transito
        int stock_reservado
        int stock_minimo_config
        int stock_maximo_config
    }

    POST_DEVOLUCIONES {
        int id_devolucion
        int id_trans_origen
        int art_id
        int id_tienda
        date fec_devolucion
        int qty_devuelta
        string motivo_cod
        string canal_devolucion
        string estado_devolucion
        float vr_reembolso
    }