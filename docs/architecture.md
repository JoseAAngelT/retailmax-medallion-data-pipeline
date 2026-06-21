# Architecture

Este proyecto usa una arquitectura Medallion para organizar el procesamiento de datos en capas Bronze, Silver y Gold.

## Flujo general

```mermaid
flowchart LR
    A[Generación de datos sintéticos<br/>generate_data.py] --> B[Bronze<br/>CSV]
    B --> P[PostgreSQL local<br/>Fuente relacional]
    B --> C[Silver<br/>Parquet limpio y estandarizado]
    C --> D[Gold<br/>Modelo analítico]
    D --> E[Quality Checks<br/>47 validaciones]
    D --> F[Azure Blob Storage<br/>Contenedor gold]
    E --> G[Azure Blob Storage<br/>Contenedor evidence]

    O[Airflow local<br/>Docker Compose] -. orquesta .-> B
    O -. orquesta .-> C
    O -. orquesta .-> D
    O -. orquesta .-> E

    I[Bicep + Azure CLI<br/>IaC mínima] -. aprovisiona .-> F
    I -. aprovisiona .-> G

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
```

## Componentes principales

| Componente         | Uso                                                           |
| ------------------ | ------------------------------------------------------------- |
| Python             | Generación, transformación y validación de datos.             |
| PostgreSQL local   | Simulación de una fuente relacional para las tablas Bronze.   |
| Bronze             | Datos fuente generados en CSV.                                |
| Silver             | Datos limpios, tipados y estandarizados en Parquet.           |
| Gold               | Modelo analítico con dimensiones, hechos y KPIs.              |
| Quality Checks     | Validaciones de integridad, reglas de negocio y consistencia. |
| Azure Blob Storage | Almacenamiento de evidencias y salidas analíticas.            |
| Bicep              | Infraestructura como Código mínima para recursos Azure.       |
| Airflow local      | Orquestación del flujo mediante Docker Compose.               |

## Orquestación

La ejecución principal puede realizarse de forma local con:

```powershell
python main.py
```

También se agregó una ejecución local con Apache Airflow usando Docker Compose. El DAG ejecuta el flujo:

```text
start → generate_bronze_data → run_silver_transformations → run_gold_transformations → run_quality_checks → end
```

Las evidencias de Airflow se encuentran en:

```text
docs/evidence/airflow_dag_success.png
docs/evidence/airflow_dag_graph_success.png
```

## Infraestructura cloud

Azure Blob Storage se usa como una versión simplificada de data lake para guardar:

* salidas Gold en formato Parquet;
* reportes de calidad;
* evidencias de ejecución;
* capturas de infraestructura.

Además, se agregó una versión mínima de IaC con Bicep para aprovisionar Storage Account, contenedores, Key Vault, Log Analytics y Action Group en un Resource Group de prueba.
