# RetailMax Medallion Data Pipeline

Proyecto de ingeniería de datos basado en un escenario de **Retail y Comercio Electrónico**.

El objetivo fue construir un pipeline de datos end-to-end con arquitectura Medallion, generando datos sintéticos, transformándolos por capas y creando salidas analíticas para ventas, inventario, devoluciones y clientes.

El pipeline se ejecuta localmente con Python, usa PostgreSQL como fuente relacional simulada, almacena evidencias en Azure Blob Storage y cuenta con una ejecución local de Airflow usando Docker.

---

## 1. Escenario

Se trabajó con el escenario de **Retail y Comercio Electrónico** porque permite cubrir conceptos importantes de ingeniería de datos:

* generación de datos sintéticos;
* procesamiento por capas Bronze, Silver y Gold;
* carga en una base relacional;
* limpieza y transformación de datos;
* modelo dimensional;
* validaciones de calidad;
* almacenamiento cloud;
* orquestación del pipeline;
* base de Infraestructura como Código.

---

## 2. Tecnologías utilizadas

| Tecnología              | Uso                                          |
| ----------------------- | -------------------------------------------- |
| Python                  | Desarrollo principal del pipeline.           |
| Pandas / NumPy          | Transformación y generación de datos.        |
| Faker                   | Generación de datos sintéticos.              |
| PyArrow                 | Escritura de archivos Parquet.               |
| YAML                    | Configuración del proyecto.                  |
| PostgreSQL              | Fuente relacional local simulada.            |
| SQLAlchemy / psycopg2   | Conexión y carga hacia PostgreSQL.           |
| Azure Blob Storage      | Almacenamiento de evidencias y salidas Gold. |
| Bicep                   | Infraestructura como Código mínima en Azure. |
| Azure CLI               | Despliegue de recursos Azure.                |
| Docker / Docker Compose | Ejecución local de Airflow.                  |
| Apache Airflow          | Orquestación del pipeline.                   |
| Git / GitHub            | Control de versiones y entrega del proyecto. |

---

## 3. Arquitectura

El proyecto sigue una arquitectura Medallion:

```text
Bronze → Silver → Gold → Quality Checks
```

Además:

* las tablas Bronze se cargan en PostgreSQL local para simular una fuente relacional;
* las salidas Gold y evidencias se cargan en Azure Blob Storage;
* el DAG de Airflow se ejecutó localmente con Docker Compose;
* se agregó una base de IaC con Bicep para recursos Azure.

Documentación relacionada:

```text
docs/architecture.md
docs/source_er_model.md
docs/data_model.md
docs/data_lineage.md
```

---

## 4. Capas del pipeline

### Bronze

Genera las tablas fuente en CSV:

```text
MSTR_PROVEEDORES
MSTR_ARTICULOS
MSTR_TIENDAS
CRM_MIEMBROS
TRANS_VENTAS
INV_STOCK_DIARIO
POST_DEVOLUCIONES
```

### Silver

Limpia, tipa y estandariza los datos.

Incluye:

* conversión de fechas y columnas numéricas;
* limpieza de textos;
* estandarización de género;
* imputación de rango de edad;
* validación de clientes en ventas;
* asignación de cliente anónimo;
* cálculo de venta bruta y venta neta;
* mapeo de motivos de devolución.

### Gold

Construye el modelo analítico final:

```text
dim_productos
dim_tiendas
dim_clientes
fact_ventas
fact_inventario
fact_devoluciones
fact_rfm_clientes
kpi_ventas_diarias
kpi_top_articulos_categoria
```

También se generó una muestra de salida particionada para:

```text
data/gold_partitioned/kpi_ventas_diarias/
```

La evidencia está en:

```text
docs/evidence/partitioned_outputs_summary.txt
```

---

## 5. Modelo analítico

La capa Gold contiene dimensiones, hechos y KPIs.

| Tabla                         | Propósito                                                  |
| ----------------------------- | ---------------------------------------------------------- |
| `dim_productos`               | Análisis por producto, categoría y proveedor.              |
| `dim_tiendas`                 | Análisis por tienda, ciudad, país y zona.                  |
| `dim_clientes`                | Segmentación de clientes con identificador anonimizado.    |
| `fact_ventas`                 | Análisis de ventas, descuentos y canales.                  |
| `fact_inventario`             | Seguimiento de stock, cobertura y riesgo de quiebre.       |
| `fact_devoluciones`           | Análisis de devoluciones por artículo y motivo.            |
| `fact_rfm_clientes`           | Segmentación de clientes por recencia, frecuencia y valor. |
| `kpi_ventas_diarias`          | KPIs diarios para análisis ejecutivo.                      |
| `kpi_top_articulos_categoria` | Ranking de artículos por categoría.                        |

`dim_clientes` incluye un hash SHA-256 del identificador del cliente y un cliente anónimo con `id_miembro = 0` para mantener integridad referencial.

---

## 6. Volúmenes generados

| Tabla Bronze        | Registros |
| ------------------- | --------: |
| `MSTR_PROVEEDORES`  |       800 |
| `MSTR_ARTICULOS`    |     5,000 |
| `MSTR_TIENDAS`      |       150 |
| `CRM_MIEMBROS`      |    50,000 |
| `TRANS_VENTAS`      | 1,000,000 |
| `INV_STOCK_DIARIO`  |   750,000 |
| `POST_DEVOLUCIONES` |    50,000 |

| Tabla Gold                    | Registros |
| ----------------------------- | --------: |
| `dim_productos`               |     5,000 |
| `dim_tiendas`                 |       150 |
| `dim_clientes`                |    50,001 |
| `fact_ventas`                 | 1,000,000 |
| `fact_inventario`             |   750,000 |
| `fact_devoluciones`           |    50,000 |
| `fact_rfm_clientes`           |    49,999 |
| `kpi_ventas_diarias`          |    14,850 |
| `kpi_top_articulos_categoria` |        60 |

---

## 7. Calidad de datos

El pipeline incluye validaciones personalizadas en:

```text
src/quality_checks.py
```

Se validan:

* existencia de archivos Bronze, Silver y Gold;
* volúmenes mínimos;
* conteos esperados;
* integridad entre hechos y dimensiones;
* existencia del cliente anónimo;
* venta neta no negativa;
* cobertura de inventario;
* alerta de quiebre;
* tasa de devolución;
* scores RFM.

Resultado de la última ejecución:

```text
Total validaciones: 47
Validaciones exitosas: 47
Validaciones fallidas: 0
```

Evidencias:

```text
docs/evidence/quality_checks_summary.txt
docs/evidence/silver_quality_report.txt
docs/evidence/pipeline_errors.csv
```

---

## 8. PostgreSQL

Las tablas Bronze se cargan en PostgreSQL local para simular una fuente relacional.

Script:

```text
src/load_to_postgres.py
```

La conexión usa variables de entorno:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

Evidencia:

```text
docs/evidence/postgres_counts_summary.txt
```

---

## 9. Azure e Infraestructura como Código

Se usó Azure Blob Storage como almacenamiento cloud para evidencias y salidas analíticas.

Recursos principales:

```text
Resource Group: rg-retailmax-data-pipeline
Storage Account: retailmaxlakeja
Containers: bronze, silver, gold, evidence
```

También se agregó una base de IaC con Bicep:

```text
infra/main.bicep
infra/parameters.dev.json
```

El template Bicep fue desplegado con Azure CLI en un Resource Group de prueba y creó:

* Storage Account;
* contenedores `bronze`, `silver`, `gold` y `evidence`;
* Key Vault;
* Log Analytics Workspace;
* Action Group.

Documentación:

```text
docs/azure_setup.md
infra/README.md
```

Evidencia:

```text
docs/evidence/azure_bicep_deployment_resources.png
```

---

## 10. Orquestación

La ejecución principal puede realizarse con:

```powershell
python main.py
```

También se configuró Airflow local con Docker Compose.

Archivos principales:

```text
orchestration/docker-compose.yaml
orchestration/Dockerfile
orchestration/.env.example
orchestration/dags/retailmax_medallion_dag.py
```

Flujo del DAG:

```text
start → generate_bronze_data → run_silver_transformations → run_gold_transformations → run_quality_checks → end
```

El DAG incluye:

* ejecución diaria a las 02:00;
* dependencias explícitas;
* 3 reintentos por tarea;
* backoff exponencial;
* timeout por tarea.

Evidencias:

```text
docs/evidence/airflow_dag_success.png
docs/evidence/airflow_dag_graph_success.png
```

---

## 11. Gobierno y seguridad

Controles aplicados:

* no se guardan contraseñas ni claves en el repositorio;
* PostgreSQL usa variables de entorno;
* Azure Blob Storage tiene acceso privado;
* las capturas de Azure fueron editadas para ocultar información sensible;
* `data/`, `.venv/`, cachés y logs locales están ignorados por Git;
* se genera `id_miembro_hash` con SHA-256 en Gold;
* Key Vault, Log Analytics y Action Group fueron creados como recursos base por Bicep.

Documentación:

```text
docs/governance_security.md
docs/data_catalog.md
CHANGELOG.md
```

---

## 12. Estructura del proyecto

```text
retailmax-medallion-data-pipeline/
├── config/
│   └── config.yaml
├── docs/
│   ├── architecture.md
│   ├── azure_setup.md
│   ├── data_catalog.md
│   ├── data_lineage.md
│   ├── data_model.md
│   ├── governance_security.md
│   ├── source_er_model.md
│   └── evidence/
├── infra/
│   ├── main.bicep
│   ├── parameters.dev.json
│   └── README.md
├── orchestration/
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── .env.example
│   ├── README.md
│   └── dags/
├── src/
│   ├── generate_data.py
│   ├── silver_transform.py
│   ├── gold_transform.py
│   ├── quality_checks.py
│   ├── load_to_postgres.py
│   ├── silver_quality_report.py
│   ├── notification_samples.py
│   ├── pipeline_error_report.py
│   ├── create_partitioned_outputs.py
│   └── utils.py
├── main.py
├── requirements.txt
├── CHANGELOG.md
├── README.md
└── .gitignore
```

La carpeta `data/` no se sube al repositorio porque contiene archivos generados.

---

## 13. Cómo ejecutar

Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Ejecutar pipeline completo:

```powershell
python main.py
```

Ejecutar scripts auxiliares:

```powershell
python -m src.silver_quality_report
python -m src.load_to_postgres
python -m src.notification_samples
python -m src.pipeline_error_report
python -m src.create_partitioned_outputs
```

Ejecutar Airflow local:

```powershell
cd orchestration
copy .env.example .env
docker compose build
docker compose up airflow-init
docker compose up -d
```

Abrir:

```text
http://localhost:8080
```

Credenciales locales:

```text
airflow / airflow
```

---

## 14. Evidencias

Las evidencias se encuentran en:

```text
docs/evidence/
```

Incluyen:

* validaciones de calidad;
* reporte Silver;
* conteos de PostgreSQL;
* errores controlados del pipeline;
* muestra de anomalías;
* reportes y alertas operativas simuladas;
* evidencia de salida particionada;
* capturas de Azure;
* evidencia de despliegue Bicep;
* evidencia de ejecución Airflow.

---

## 15. Alcance y limitaciones

Este proyecto se desarrolló como una prueba técnica end-to-end en un periodo corto de trabajo. Se priorizó construir una solución funcional, reproducible y defendible, cubriendo las partes principales del flujo de datos: generación, carga relacional, procesamiento Medallion, calidad, documentación, nube y orquestación local.

Algunos componentes se implementaron como una base funcional o evidencia separada, en lugar de una solución productiva completa. Esto permitió mantener el proyecto estable y demostrar el entendimiento general del flujo sin agregar complejidad innecesaria al cierre de la entrega.

### Alcance implementado

* Generación de datos sintéticos con semilla fija y parámetros configurables.
* Carga de tablas Bronze a PostgreSQL local.
* Pipeline Medallion con capas Bronze, Silver y Gold.
* Modelo analítico con dimensiones, hechos y KPIs.
* Validaciones de calidad personalizadas.
* Reporte de calidad para la capa Silver.
* Muestra de errores controlados del pipeline.
* Salida Gold particionada como evidencia separada.
* Carga de evidencias y salidas Gold en Azure Blob Storage.
* Infraestructura mínima con Bicep desplegada mediante Azure CLI.
* Airflow ejecutado localmente con Docker Compose.
* Documentación de arquitectura, modelo de datos, linaje, catálogo, anomalías, gobierno y seguridad.
* CHANGELOG con el avance del proyecto.

### Limitaciones actuales

* La ingesta principal no se ejecuta desde PostgreSQL hacia Azure como proceso incremental completo. En esta versión, PostgreSQL se usa como fuente relacional simulada y el pipeline principal trabaja con las salidas locales generadas.
* No se implementó ingesta incremental real. El pipeline está diseñado para ser reproducible y sobrescribir salidas, evitando duplicados en ejecuciones repetidas.
* La tabla de errores del pipeline se dejó como muestra controlada en `docs/evidence/pipeline_errors.csv`, no como tabla integrada a cada etapa del flujo.
* El particionamiento Gold se implementó como evidencia separada para `kpi_ventas_diarias`, sin modificar el pipeline principal.
* Airflow se ejecutó localmente con Docker Compose. No se desplegó en un entorno administrado o productivo.
* Las alertas y reportes operativos se dejaron como ejemplos generados en archivos de evidencia. No se conectaron a correo, Teams o Azure Monitor.
* Bicep se implementó como base funcional de Infraestructura como Código. No incluye ambientes dev/prod separados, backend remoto de estado ni una integración completa con secretos.
* Key Vault, Log Analytics y Action Group fueron creados como recursos base, pero no se integraron completamente al pipeline.
* No se implementaron roles reales en Azure ni evidencia de acceso denegado para un perfil Analyst.
* No se agregó una fuente de visitas o sesiones, por lo que no se calcula tasa de conversión real.

Estas limitaciones quedan documentadas como siguientes pasos. Algunas se dejaron fuera por tiempo y porque varias herramientas, como Airflow, Bicep y componentes de monitoreo en Azure, se estaban aplicando por primera vez dentro de un proyecto end-to-end. Aun así, se intentó avanzar en cada fase para dejar evidencia práctica, una base reproducible y puntos claros de mejora.

---

## 16. Próximos pasos

Mejoras posibles:

* integrar Key Vault con el pipeline;
* configurar alertas reales con Azure Monitor;
* implementar roles reales y evidencia de acceso denegado;
* convertir la ingesta PostgreSQL → Bronze cloud en incremental;
* agregar metadatos de auditoría en Bronze;
* ejecutar Airflow en un entorno administrado;
* automatizar la carga a Azure desde el pipeline;
* agregar pruebas unitarias o Great Expectations;
* crear un dashboard en Power BI;
* incorporar una fuente de tráfico para calcular conversión real.
