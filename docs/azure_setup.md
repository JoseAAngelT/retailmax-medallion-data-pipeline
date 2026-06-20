# Azure Setup

Este proyecto utiliza Azure Blob Storage como capa de almacenamiento en la nube para el pipeline Medallion de RetailMax.

## Recursos creados

- Resource Group: `rg-retailmax-data-pipeline`
- Storage Account: `retailmaxlakeja`
- Región: `East US`
- Tipo de cuenta: `StorageV2`
- Replicación: `Locally-redundant storage (LRS)`
- Nivel de acceso: `Hot`
- Acceso anónimo a blobs: `Deshabilitado`
- Transferencia segura: `Habilitado`
- Versión mínima de TLS: `1.2`

## Contenedores creados

- `bronze`
- `silver`
- `gold`
- `evidence`

Todos los contenedores fueron configurados con acceso privado.

## Archivos cargados

### Contenedor `evidence`

- `quality_checks_summary.txt`

### Contenedor `gold`

- `dim_clientes.parquet`
- `dim_productos.parquet`
- `dim_tiendas.parquet`
- `fact_ventas.parquet`
- `fact_inventario.parquet`
- `fact_devoluciones.parquet`
- `fact_rfm_clientes.parquet`
- `kpi_ventas_diarias.parquet`
- `kpi_top_articulos_categoria.parquet`

## Decisión técnica

Azure Blob Storage se utilizó como una versión simplificada de data lake para almacenar evidencias y salidas analíticas del pipeline. Para este alcance, se priorizó una configuración simple, privada y de bajo costo usando `Standard` + `LRS`.

## Consideraciones

El procesamiento principal del pipeline se ejecuta localmente mediante:

```powershell
python main.py