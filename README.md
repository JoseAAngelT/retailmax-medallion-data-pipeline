# RetailMax Medallion Data Pipeline

Proyecto de ingenieria de datos basado en un escenario de **Retail y Comercio Electronico**.

El objetivo fue construir un pipeline end-to-end con arquitectura Medallion, integrando generacion de datos sinteticos, procesamiento por capas, PostgreSQL como fuente relacional simulada, orquestacion con Airflow, validaciones de calidad, evidencias operativas, pruebas automatizadas y publicacion de salidas en Azure Blob Storage.

---

## 1. Descripcion general

El proyecto simula el flujo de datos de una compania retail llamada RetailMax. A partir de tablas fuente generadas de forma sintetica, el pipeline procesa informacion de proveedores, articulos, tiendas, clientes, ventas, inventario y devoluciones.

El flujo principal cubre:

* generacion de datos fuente;
* carga de datos Bronze a PostgreSQL local;
* ingesta desde PostgreSQL hacia Bronze Parquet con metadatos de auditoria;
* transformaciones Silver;
* modelo analitico Gold;
* salida Gold particionada;
* validaciones de calidad personalizadas;
* validaciones formales estilo Great Expectations;
* tabla de errores del pipeline;
* reporte operativo consolidado;
* notificacion local;
* historial de ejecuciones;
* carga de salidas Gold y evidencias a Azure Blob Storage;
* pruebas unitarias con pytest;
* validacion automatica con GitHub Actions.

---

## 2. Arquitectura general

El proyecto sigue una arquitectura Medallion:

```text
Source CSV
  -> PostgreSQL local
  -> Bronze Parquet con auditoria
  -> Silver
  -> Gold
  -> Gold particionado
  -> Quality Checks
  -> Great Expectations style checks
  -> Error Table
  -> Execution Report
  -> Notification
  -> Azure Blob Storage
```

El pipeline se puede ejecutar de dos formas:

```text
1. Localmente con Python.
2. Orquestado con Apache Airflow usando Docker Compose.
```

Documentacion relacionada:

```text
docs/architecture.md
docs/source_er_model.md
docs/data_model.md
docs/data_lineage.md
docs/data_catalog.md
docs/governance_security.md
```

---

## 3. Tecnologias utilizadas

| Tecnologia              | Uso                                                  |
| ----------------------- | ---------------------------------------------------- |
| Python                  | Desarrollo principal del pipeline.                   |
| Pandas / NumPy          | Transformacion, limpieza y generacion de datos.      |
| Faker                   | Generacion de datos sinteticos.                      |
| PyArrow                 | Lectura y escritura de archivos Parquet.             |
| YAML                    | Configuracion del proyecto.                          |
| PostgreSQL              | Fuente relacional local simulada.                    |
| SQLAlchemy / psycopg2   | Conexion y carga hacia PostgreSQL.                   |
| Apache Airflow          | Orquestacion del pipeline.                           |
| Docker / Docker Compose | Ejecucion local de Airflow.                          |
| Azure Blob Storage      | Publicacion de salidas Gold y evidencias.            |
| Azure Storage SDK       | Carga programatica de archivos a Blob Storage.       |
| Great Expectations      | Base para validaciones formales estilo expectations. |
| Pytest                  | Pruebas unitarias de modulos clave.                  |
| Ruff                    | Validacion estatica y estilo de codigo.              |
| GitHub Actions          | CI para Ruff, pytest e imports principales.          |
| Bicep                   | Base de Infraestructura como Codigo en Azure.        |
| Git / GitHub            | Versionamiento y entrega del proyecto.               |

---

## 4. Flujo del pipeline

El flujo final orquestado en Airflow es:

```text
start
  -> register_pipeline_start
  -> generate_bronze_data
  -> load_bronze_to_postgres
  -> ingest_postgres_to_bronze
  -> run_silver_transformations
  -> run_gold_transformations
  -> create_partitioned_gold_outputs
  -> run_quality_checks
  -> run_great_expectations_checks
  -> generate_pipeline_error_table
  -> generate_execution_report
  -> generate_pipeline_notification
  -> upload_outputs_to_azure
  -> register_pipeline_end
  -> end
```

El DAG incluye:

* dependencias explicitas entre tareas;
* ejecucion diaria a las 02:00;
* reintentos por tarea;
* backoff exponencial;
* timeout de ejecucion;
* control de estado por corrida;
* generacion automatica de evidencias.

Archivo principal del DAG:

```text
orchestration/dags/retailmax_medallion_dag.py
```

---

## 5. Capas del pipeline

### Bronze

Se generan las tablas fuente en CSV:

```text
MSTR_PROVEEDORES
MSTR_ARTICULOS
MSTR_TIENDAS
CRM_MIEMBROS
TRANS_VENTAS
INV_STOCK_DIARIO
POST_DEVOLUCIONES
```

Estas tablas se cargan en PostgreSQL local para simular una fuente relacional.

Despues, el pipeline ejecuta una ingesta desde PostgreSQL hacia Bronze Parquet, agregando columnas de auditoria:

```text
ingestion_timestamp
source_system
batch_id
```

Salida principal:

```text
data/bronze_ingested/
```

Evidencia:

```text
docs/evidence/bronze_ingestion_log.txt
```

---

### Silver

La capa Silver limpia, tipa y estandariza los datos.

Incluye:

* conversion de fechas;
* conversion de columnas numericas;
* limpieza de textos;
* estandarizacion de campos categoricos;
* imputacion de rango de edad;
* validacion de clientes en ventas;
* asignacion de cliente anonimo;
* calculo de venta bruta y venta neta;
* normalizacion de motivos de devolucion.

Salida principal:

```text
data/silver/
```

---

### Gold

La capa Gold construye el modelo analitico final.

Tablas principales:

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

Tambien se genera una salida particionada de `kpi_ventas_diarias` por periodo:

```text
data/gold_partitioned/kpi_ventas_diarias/
```

Evidencia:

```text
docs/evidence/partitioned_outputs_summary.txt
```

---

## 6. Modelo analitico

| Tabla                         | Proposito                                               |
| ----------------------------- | ------------------------------------------------------- |
| `dim_productos`               | Analisis por producto, categoria y proveedor.           |
| `dim_tiendas`                 | Analisis por tienda, ciudad y pais.                     |
| `dim_clientes`                | Segmentacion de clientes con identificador anonimizado. |
| `fact_ventas`                 | Analisis de ventas, descuentos, canales y pagos.        |
| `fact_inventario`             | Seguimiento de stock, cobertura y riesgo de quiebre.    |
| `fact_devoluciones`           | Analisis de devoluciones por articulo, motivo y tienda. |
| `fact_rfm_clientes`           | Segmentacion RFM por recencia, frecuencia y valor.      |
| `kpi_ventas_diarias`          | Indicadores diarios de ventas.                          |
| `kpi_top_articulos_categoria` | Ranking de articulos por categoria.                     |

`dim_clientes` incluye un hash SHA-256 del identificador del cliente y un cliente anonimo con `id_miembro = 0` para mantener integridad referencial.

---

## 7. Volumenes procesados

### Tablas fuente Bronze

| Tabla               | Registros |
| ------------------- | --------: |
| `MSTR_PROVEEDORES`  |       800 |
| `MSTR_ARTICULOS`    |     5,000 |
| `MSTR_TIENDAS`      |       150 |
| `CRM_MIEMBROS`      |    50,000 |
| `TRANS_VENTAS`      | 1,000,000 |
| `INV_STOCK_DIARIO`  |   750,000 |
| `POST_DEVOLUCIONES` |    50,000 |

Total procesado en Bronze ingestion:

```text
1,855,950 registros
```

### Tablas Gold principales

| Tabla                         | Registros |
| ----------------------------- | --------: |
| `dim_productos`               |     5,000 |
| `dim_tiendas`                 |       150 |
| `dim_clientes`                |    50,001 |
| `fact_ventas`                 | 1,000,000 |
| `fact_inventario`             |   750,000 |
| `fact_devoluciones`           |    50,000 |
| `fact_rfm_clientes`           |    49,999 |
| `kpi_ventas_diarias`          |    34,110 |
| `kpi_top_articulos_categoria` |        60 |

---

## 8. Calidad de datos

El proyecto incluye dos capas de calidad.

### Validaciones personalizadas

Archivo:

```text
src/quality_checks.py
```

Validaciones principales:

* existencia de archivos Bronze, Silver y Gold;
* volumenes minimos;
* conteos esperados;
* integridad referencial entre hechos y dimensiones;
* existencia de cliente anonimo;
* venta neta no negativa;
* cobertura de inventario;
* reglas de alerta de quiebre;
* tasa de devolucion no negativa;
* scores RFM entre 1 y 5.

Resultado de la ultima ejecucion:

```text
Total de validaciones: 47
Validaciones exitosas: 47
Validaciones fallidas: 0
```

Evidencia:

```text
docs/evidence/quality_checks_summary.txt
```

### Validaciones estilo Great Expectations

Archivo:

```text
src/great_expectations_checks.py
```

Se agrego una capa de validaciones formales estilo expectations sobre tablas Gold. Debido a la version usada de Great Expectations, se implementaron validaciones declarativas con pandas y se registro la version instalada de la libreria.

Resultado:

```text
Great Expectations version: 1.18.1
Total expectations: 14
Successful expectations: 14
Failed expectations: 0
```

Evidencias:

```text
docs/evidence/great_expectations_summary.csv
docs/evidence/great_expectations_summary.txt
```

---

## 9. Errores, reportes y observabilidad

El pipeline genera una tabla de errores operativos:

```text
data/errors/pipeline_errors.parquet
docs/evidence/pipeline_errors.csv
docs/evidence/pipeline_errors_summary.txt
```

Cuando no se detectan errores criticos, se genera un registro informativo:

```text
NO_ERRORS_DETECTED
severity: info
```

Tambien se generan evidencias operativas:

```text
docs/evidence/pipeline_execution_report.txt
docs/evidence/pipeline_notification.txt
docs/evidence/pipeline_run_history.csv
docs/evidence/pipeline_run_history_summary.txt
```

Estas salidas permiten revisar:

* estado de ejecucion;
* total de ejecuciones registradas;
* duracion del ultimo run;
* volumenes procesados;
* estado de calidad;
* estado de errores;
* resumen operativo del pipeline.

---

## 10. PostgreSQL

PostgreSQL se usa como fuente relacional local simulada.

Script:

```text
src/load_to_postgres.py
```

La conexion usa variables de entorno:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

Para Airflow en Docker, `PGHOST` debe apuntar al host de Docker:

```env
PGHOST=host.docker.internal
```

Archivo local de variables:

```text
orchestration/.env
```

Este archivo no se sube al repositorio.

Evidencia:

```text
docs/evidence/postgres_counts_summary.txt
```

---

## 11. Azure Blob Storage

El pipeline sube salidas Gold y evidencias a Azure Blob Storage.

Script:

```text
src/upload_to_azure.py
```

Contenedores usados:

```text
gold
evidence
```

La carga usa la variable de entorno:

```text
AZURE_STORAGE_CONNECTION_STRING
```

Esta variable se configura localmente o en `orchestration/.env`, pero no se versiona.

Evidencias:

```text
docs/evidence/azure_upload_manifest.csv
docs/evidence/azure_upload_summary.txt
```

Ultima ejecucion registrada:

```text
total_files_uploaded: 40
gold_files_uploaded: 9
evidence_files_uploaded: 31
```

---

## 12. Infraestructura como Codigo

Se agrego una base de Infraestructura como Codigo con Bicep.

Archivos:

```text
infra/main.bicep
infra/parameters.dev.json
infra/README.md
```

Recursos contemplados:

* Storage Account;
* contenedores para capas de datos y evidencias;
* Key Vault;
* Log Analytics Workspace;
* Action Group.

Documentacion relacionada:

```text
docs/azure_setup.md
infra/README.md
```

---

## 13. Orquestacion con Airflow

Airflow se ejecuta localmente con Docker Compose.

Archivos:

```text
orchestration/docker-compose.yaml
orchestration/Dockerfile
orchestration/.env.example
orchestration/dags/retailmax_medallion_dag.py
```

Ejecucion:

```powershell
cd orchestration
copy .env.example .env
docker compose build
docker compose up -d
```

Abrir Airflow:

```text
http://localhost:8080
```

Credenciales locales:

```text
airflow / airflow
```

El archivo real `.env` debe contener las variables locales necesarias, por ejemplo:

```env
PGHOST=host.docker.internal
PGPORT=5432
PGDATABASE=retailmax_source
PGUSER=postgres
PGPASSWORD=<your-postgres-password>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
```

No se debe subir `orchestration/.env` al repositorio.

---

## 14. Pruebas y CI

El proyecto incluye pruebas unitarias con pytest.

Carpeta:

```text
tests/
```

Pruebas agregadas:

```text
test_error_handling.py
test_great_expectations_checks.py
test_notifications.py
test_partitioned_outputs.py
test_pipeline_state.py
test_upload_to_azure.py
```

Ejecucion local:

```powershell
python -m pytest
```

Resultado local:

```text
6 passed
```

Tambien se agrego CI con GitHub Actions:

```text
.github/workflows/ci.yml
```

El workflow valida:

* instalacion de dependencias base;
* Ruff;
* pytest;
* imports principales del proyecto.

---

## 15. Estructura del proyecto

```text
retailmax-medallion-data-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml
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
│   ├── bronze_ingestion.py
│   ├── create_partitioned_outputs.py
│   ├── error_handling.py
│   ├── execution_report.py
│   ├── generate_data.py
│   ├── gold_transform.py
│   ├── great_expectations_checks.py
│   ├── load_to_postgres.py
│   ├── notifications.py
│   ├── pipeline_state.py
│   ├── quality_checks.py
│   ├── silver_transform.py
│   ├── upload_to_azure.py
│   └── utils.py
├── tests/
├── main.py
├── pytest.ini
├── requirements.txt
├── CHANGELOG.md
├── README.md
└── .gitignore
```

La carpeta `data/` no se sube al repositorio porque contiene archivos generados.

---

## 16. Como ejecutar localmente

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

Ejecutar pipeline Python principal:

```powershell
python main.py
```

Ejecutar pruebas:

```powershell
python -m pytest
```

Validar estilo:

```powershell
ruff check .
```

Ejecutar Airflow:

```powershell
cd orchestration
docker compose build
docker compose up -d
```

---

## 17. Evidencias principales

Las evidencias se encuentran en:

```text
docs/evidence/
```

Archivos principales:

```text
postgres_counts_summary.txt
bronze_ingestion_log.txt
quality_checks_summary.txt
great_expectations_summary.txt
great_expectations_summary.csv
pipeline_errors_summary.txt
pipeline_errors.csv
partitioned_outputs_summary.txt
pipeline_execution_report.txt
pipeline_notification.txt
pipeline_run_history_summary.txt
pipeline_run_history.csv
azure_upload_summary.txt
azure_upload_manifest.csv
```

Tambien se incluyen capturas de Airflow, Azure y despliegues cuando aplican.

---

## 18. Seguridad y gobierno

Controles aplicados:

* no se versionan contrasenas ni connection strings;
* `orchestration/.env` esta ignorado por Git;
* `data/`, logs, caches y `.venv/` estan ignorados;
* PostgreSQL usa variables de entorno;
* Azure Storage usa `AZURE_STORAGE_CONNECTION_STRING`;
* se evita imprimir secretos completos en consola;
* se genera `id_miembro_hash` con SHA-256 en Gold;
* se documentan recursos base de seguridad en Azure como Key Vault;
* las evidencias operativas no contienen claves ni tokens.

Documentacion relacionada:

```text
docs/governance_security.md
docs/data_catalog.md
CHANGELOG.md
```

---

## 19. Alcance y limitaciones

Este proyecto se desarrollo como una prueba tecnica end-to-end. Se priorizo construir una solucion funcional, reproducible y defendible, cubriendo las fases principales de un pipeline de datos moderno.

### Alcance implementado

* Generacion de datos sinteticos con volumen configurable.
* Carga de Bronze CSV a PostgreSQL local.
* Ingesta PostgreSQL a Bronze Parquet con auditoria.
* Procesamiento Medallion: Bronze, Silver y Gold.
* Modelo dimensional con dimensiones, hechos y KPIs.
* Salida Gold particionada.
* Validaciones personalizadas de calidad.
* Validaciones formales estilo Great Expectations.
* Tabla de errores del pipeline.
* Reporte operativo consolidado.
* Notificacion local.
* Historial de ejecuciones.
* Carga de salidas Gold y evidencias a Azure Blob Storage.
* Orquestacion local con Airflow y Docker Compose.
* CI con GitHub Actions.
* Pruebas unitarias con pytest.
* Base de Infraestructura como Codigo con Bicep.
* Documentacion tecnica y evidencias.

### Limitaciones actuales

* El pipeline opera en modo batch/full refresh; no implementa incrementalidad real por watermark.
* Airflow se ejecuta localmente con Docker Compose, no en un entorno administrado.
* Las notificaciones se generan como archivo local; no se conectaron a correo, Teams o Slack.
* Los secretos se manejan con variables de entorno locales; no se integro Key Vault directamente al runtime.
* Great Expectations se uso como base de versionamiento y estilo de validaciones, pero no se implemento un Data Context completo.
* La infraestructura Bicep es una base funcional, no una plataforma productiva multiambiente.
* No se implemento una fuente real de sesiones o visitas, por lo que no se calcula una tasa de conversion real.

---

## 20. Proximos pasos

Mejoras posibles:

* implementar cargas incrementales con watermark;
* integrar Azure Key Vault al runtime;
* enviar notificaciones reales a Teams, Slack o correo;
* desplegar Airflow en un entorno administrado;
* formalizar un Data Context completo de Great Expectations;
* separar ambientes dev, test y prod;
* agregar dashboards en Power BI;
* agregar una fuente de trafico web para calcular conversion real;
* ampliar pruebas de integracion;
* automatizar despliegue de infraestructura desde CI/CD.
