# Architecture

Este proyecto usa una arquitectura Medallion para organizar el procesamiento de datos en capas Bronze, Silver y Gold.

```mermaid
flowchart LR
    A[Generación de datos sintéticos<br/>generate_data.py] --> B[Bronze<br/>CSV]
    B --> C[Silver<br/>Parquet limpio y estandarizado]
    C --> D[Gold<br/>Modelo analítico]
    D --> E[Quality Checks<br/>47 validaciones]
    D --> F[Azure Blob Storage<br/>Contenedor gold]
    E --> G[Azure Blob Storage<br/>Contenedor evidence]

    B -.-> B1[MSTR_PROVEEDORES]
    B -.-> B2[MSTR_ARTICULOS]
    B -.-> B3[MSTR_TIENDAS]
    B -.-> B4[CRM_MIEMBROS]
    B -.-> B5[TRANS_VENTAS]
    B -.-> B6[INV_STOCK_DIARIO]
    B -.-> B7[POST_DEVOLUCIONES]

    D -.-> D1[Dimensiones]
    D -.-> D2[Hechos]
    D -.-> D3[KPIs]