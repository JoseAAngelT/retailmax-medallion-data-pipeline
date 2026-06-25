# Orquestacion con Apache Airflow

Este proyecto incluye una ejecucion local de Apache Airflow usando Docker Compose. Airflow se utiliza para orquestar el pipeline completo de RetailMax, desde la generacion de datos hasta la carga de salidas Gold y evidencias en Azure Blob Storage.

---

## 1. Archivos principales

```text
orchestration/docker-compose.yaml
orchestration/Dockerfile
orchestration/.env.example
orchestration/dags/retailmax_medallion_dag.py
```

---

## 2. Servicios definidos

El archivo `docker-compose.yaml` levanta los siguientes servicios:

```text
postgres
airflow-init
airflow-webserver
airflow-scheduler
```

Uso de cada servicio:

| Servicio            | Proposito                                                       |
| ------------------- | --------------------------------------------------------------- |
| `postgres`          | Base de datos interna de Airflow.                               |
| `airflow-init`      | Inicializa la base de datos de Airflow y crea el usuario local. |
| `airflow-webserver` | Interfaz web de Airflow.                                        |
| `airflow-scheduler` | Scheduler encargado de ejecutar las tareas del DAG.             |

---

## 3. Variables de entorno

El archivo real de variables locales debe crearse a partir de `.env.example`:

```powershell
copy .env.example .env
```

El archivo `.env` no debe subirse al repositorio.

Variables principales:

```env
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

PGHOST=host.docker.internal
PGPORT=5432
PGDATABASE=retailmax_source
PGUSER=postgres
PGPASSWORD=<your-postgres-password>

AZURE_STORAGE_CONNECTION_STRING=<connection-string>
```

Notas:

* `PGHOST=host.docker.internal` permite que Airflow dentro de Docker se conecte al PostgreSQL local de Windows.
* `PGPASSWORD` debe contener la contrasena local real de PostgreSQL.
* `AZURE_STORAGE_CONNECTION_STRING` permite subir salidas Gold y evidencias a Azure Blob Storage.
* Los secretos deben mantenerse solo en `.env` o en variables de entorno locales.

---

## 4. Dockerfile

El `Dockerfile` extiende la imagen oficial de Airflow e instala las dependencias necesarias para ejecutar el DAG:

```text
faker
pandas
numpy
pyarrow
pyyaml
psycopg2-binary
great-expectations
azure-storage-blob
```

Esto permite que Airflow ejecute los modulos del proyecto dentro del contenedor.

---

## 5. Flujo del DAG

DAG principal:

```text
retailmax_medallion_pipeline
```

Archivo:

```text
orchestration/dags/retailmax_medallion_dag.py
```

Flujo final:

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

---

## 6. Tareas del DAG

| Tarea                             | Descripcion                                                         |
| --------------------------------- | ------------------------------------------------------------------- |
| `register_pipeline_start`         | Registra el inicio de la ejecucion en el historial del pipeline.    |
| `generate_bronze_data`            | Genera los datos fuente Bronze en CSV.                              |
| `load_bronze_to_postgres`         | Carga las tablas Bronze a PostgreSQL local.                         |
| `ingest_postgres_to_bronze`       | Ingesta tablas desde PostgreSQL hacia Bronze Parquet con auditoria. |
| `run_silver_transformations`      | Limpia y estandariza los datos hacia Silver.                        |
| `run_gold_transformations`        | Construye dimensiones, hechos y KPIs Gold.                          |
| `create_partitioned_gold_outputs` | Genera salida Gold particionada de `kpi_ventas_diarias`.            |
| `run_quality_checks`              | Ejecuta validaciones personalizadas de calidad.                     |
| `run_great_expectations_checks`   | Ejecuta validaciones formales estilo Great Expectations.            |
| `generate_pipeline_error_table`   | Genera tabla de errores del pipeline.                               |
| `generate_execution_report`       | Genera reporte operativo consolidado.                               |
| `generate_pipeline_notification`  | Genera notificacion operativa local.                                |
| `upload_outputs_to_azure`         | Sube salidas Gold y evidencias a Azure Blob Storage.                |
| `register_pipeline_end`           | Registra el cierre exitoso de la ejecucion.                         |

---

## 7. Ejecucion local

Desde la carpeta `orchestration`:

```powershell
docker compose build
docker compose up -d
```

Para revisar servicios:

```powershell
docker compose ps
```

Para detener servicios:

```powershell
docker compose down
```

Para reiniciar Airflow despues de cambiar el DAG:

```powershell
docker compose restart airflow-scheduler airflow-webserver
```

---

## 8. Acceso a Airflow

Abrir Airflow en:

```text
http://localhost:8080
```

Credenciales locales de prueba:

```text
airflow / airflow
```

URL directa del DAG:

```text
http://localhost:8080/dags/retailmax_medallion_pipeline/grid
```

Vista Graph:

```text
http://localhost:8080/dags/retailmax_medallion_pipeline/graph
```

---

## 9. Validaciones utiles

Verificar que los servicios esten activos:

```powershell
docker compose ps
```

Verificar variables PostgreSQL dentro del scheduler:

```powershell
docker compose exec airflow-scheduler env | findstr PG
```

Verificar variable de Azure sin imprimir el secreto:

```powershell
docker compose exec airflow-scheduler python -c "import os; print('Azure variable configurada' if os.getenv('AZURE_STORAGE_CONNECTION_STRING') else 'Falta variable')"
```

Verificar Great Expectations dentro del contenedor:

```powershell
docker compose exec airflow-scheduler python -c "import great_expectations as gx; print(gx.__version__)"
```

Ver logs del scheduler:

```powershell
docker compose logs airflow-scheduler --tail=120
```

---

## 10. Evidencias generadas

El DAG actualiza evidencias en:

```text
docs/evidence/
```

Evidencias relevantes:

```text
bronze_ingestion_log.txt
postgres_counts_summary.txt
partitioned_outputs_summary.txt
quality_checks_summary.txt
great_expectations_summary.txt
pipeline_errors_summary.txt
pipeline_execution_report.txt
pipeline_notification.txt
pipeline_run_history_summary.txt
azure_upload_summary.txt
azure_upload_manifest.csv
```

Tambien se pueden guardar capturas de Airflow:

```text
docs/evidence/airflow_grid_full_pipeline_success.png
docs/evidence/airflow_graph_full_pipeline_flow.png
```

---

## 11. Consideraciones de seguridad

* No subir `orchestration/.env` al repositorio.
* No escribir connection strings en README, commits, capturas o issues.
* Usar `orchestration/.env.example` solo como plantilla sin secretos.
* Mantener `data/`, logs y caches ignorados por Git.
* Verificar `git status --ignored` antes de cada commit.
* Evitar imprimir `AZURE_STORAGE_CONNECTION_STRING` completa en consola.

---

## 12. Limitaciones

Esta configuracion esta orientada a ejecucion local y validacion tecnica. No representa un despliegue productivo de Airflow.

Limitaciones actuales:

* Airflow corre localmente con Docker Compose.
* No usa un executor distribuido.
* No esta desplegado en un entorno administrado.
* Las credenciales se manejan con variables de entorno locales.
* Las notificaciones se generan como archivos locales, no se envian a Teams, Slack o correo.
