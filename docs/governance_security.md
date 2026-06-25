# Gobierno y seguridad

Este documento resume las decisiones de gobierno, seguridad y privacidad consideradas para el proyecto RetailMax.

El objetivo de esta sección es dejar claro cómo se manejan credenciales, datos sensibles, accesos, evidencias, almacenamiento cloud y operación local del pipeline.

---

## 1. Alcance actual

En esta versión se implementaron controles básicos de seguridad y gobierno para un proyecto local end-to-end:

* no se guardan contraseñas, claves ni connection strings en el repositorio;
* PostgreSQL usa variables de entorno;
* Airflow local usa un archivo `.env` ignorado por Git;
* Azure Blob Storage usa `AZURE_STORAGE_CONNECTION_STRING` como variable de entorno;
* `orchestration/.env.example` se mantiene como plantilla sin secretos reales;
* `data/`, `.venv/`, logs y cachés locales están ignorados por Git;
* los contenedores de Azure Blob Storage se manejan como privados;
* el Storage Account tiene acceso anónimo deshabilitado;
* se usa TLS 1.2;
* se genera un hash SHA-256 para el identificador del cliente en Gold;
* se agregó una base de Infraestructura como Código con Bicep;
* se creó Key Vault como recurso base para gestión futura de secretos;
* se creó Log Analytics Workspace como base para monitoreo;
* se creó Action Group como base para alertas;
* se generan evidencias operativas del pipeline;
* se agregó CI con GitHub Actions;
* se agregaron pruebas unitarias con pytest.

---

## 2. Roles propuestos

| Rol           | Acceso propuesto                                        | Uso                                                     |
| ------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| Data Engineer | Lectura y escritura en Bronze, Silver, Gold y Evidence. | Operar, mantener y depurar el pipeline.                 |
| Analyst       | Solo lectura en Gold.                                   | Consumir datos para análisis y reportes.                |
| Admin         | Control total sobre recursos del proyecto.              | Administración de infraestructura, permisos y secretos. |

Estos roles son una propuesta de gobierno. En esta versión local no se implementaron roles reales de Azure RBAC por usuario.

---

## 3. Principio de mínimo privilegio

En una versión productiva, cada componente debería usar una identidad separada.

| Componente                 | Identidad sugerida                 | Permisos                                                  |
| -------------------------- | ---------------------------------- | --------------------------------------------------------- |
| Pipeline de ingesta        | Service principal de ingesta       | Lectura de fuentes y escritura en Bronze.                 |
| Pipeline de transformación | Service principal de procesamiento | Lectura en Bronze/Silver y escritura en Silver/Gold.      |
| Publicación cloud          | Service principal de publicación   | Escritura controlada en contenedores `gold` y `evidence`. |
| Usuarios analistas         | Grupo de analistas                 | Lectura solo en Gold.                                     |
| Administración             | Grupo de administradores           | Gestión de recursos, permisos y secretos.                 |

---

## 4. Datos sensibles

| Campo                 | Tabla                                                         | Tratamiento                                                                            |
| --------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `id_miembro`          | `CRM_MIEMBROS`, `TRANS_VENTAS`, `dim_clientes`, `fact_ventas` | Se conserva para integridad referencial del modelo.                                    |
| `id_miembro_hash`     | `dim_clientes`                                                | Hash SHA-256 estable para análisis sin exponer directamente el identificador original. |
| `genero`              | `dim_clientes`                                                | Se estandariza a `M`, `F` o `No informado`.                                            |
| `rango_edad`          | `dim_clientes`                                                | Se imputa cuando viene nulo.                                                           |
| Evidencias operativas | `docs/evidence/`                                              | No deben contener claves, tokens ni connection strings.                                |

---

## 5. Secretos y variables de entorno

No se incluyen secretos en el código fuente ni en la documentación versionada.

### PostgreSQL local

Para ejecutar scripts localmente desde PowerShell:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

### Airflow local con Docker

Para Airflow, las variables se definen en:

```text
orchestration/.env
```

Este archivo está ignorado por Git y no debe subirse al repositorio.

Ejemplo de variables esperadas:

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

### Azure Blob Storage

La carga a Azure se realiza con:

```text
AZURE_STORAGE_CONNECTION_STRING
```

Esta variable permite que el DAG suba salidas Gold y evidencias a Azure Blob Storage. No debe guardarse en:

```text
README.md
docs/
commits
capturas
issues
logs compartidos
.env.example
```

---

## 6. Archivos ignorados por Git

El proyecto evita versionar archivos generados o sensibles.

Archivos y carpetas ignoradas:

```text
.venv/
data/
orchestration/.env
orchestration/logs/
.ruff_cache/
.pytest_cache/
__pycache__/
```

Antes de cada commit se recomienda ejecutar:

```powershell
git status --ignored
```

y verificar que no aparezcan archivos sensibles en staged changes.

---

## 7. Azure Blob Storage

Azure Blob Storage se usa como destino cloud para salidas analíticas y evidencias.

Contenedores usados por el pipeline:

```text
gold
evidence
```

Uso de cada contenedor:

| Contenedor | Uso                                                       |
| ---------- | --------------------------------------------------------- |
| `gold`     | Salidas analíticas Gold en Parquet.                       |
| `evidence` | Evidencias operativas, reportes, manifiestos y resúmenes. |

Módulo responsable:

```text
src/upload_to_azure.py
```

Evidencias generadas:

```text
docs/evidence/azure_upload_manifest.csv
docs/evidence/azure_upload_summary.txt
```

El manifiesto permite auditar qué archivos fueron subidos, a qué contenedor y con qué estado.

---

## 8. Evidencias operativas

El pipeline genera evidencias locales para revisión y auditoría.

Evidencias principales:

```text
docs/evidence/postgres_counts_summary.txt
docs/evidence/bronze_ingestion_log.txt
docs/evidence/quality_checks_summary.txt
docs/evidence/great_expectations_summary.txt
docs/evidence/pipeline_errors_summary.txt
docs/evidence/pipeline_execution_report.txt
docs/evidence/pipeline_notification.txt
docs/evidence/pipeline_run_history_summary.txt
docs/evidence/azure_upload_summary.txt
docs/evidence/azure_upload_manifest.csv
```

Estas evidencias permiten revisar:

* conteos por tabla;
* ingesta desde PostgreSQL;
* validaciones de calidad;
* validaciones formales estilo Great Expectations;
* errores detectados;
* ejecución operativa;
* notificación local;
* historial de runs;
* carga a Azure Blob Storage.

---

## 9. Calidad y control

El proyecto incluye controles de calidad y operación:

| Control                                         | Archivo                            |
| ----------------------------------------------- | ---------------------------------- |
| Validaciones personalizadas                     | `src/quality_checks.py`            |
| Validaciones formales estilo Great Expectations | `src/great_expectations_checks.py` |
| Tabla de errores                                | `src/error_handling.py`            |
| Reporte operativo                               | `src/execution_report.py`          |
| Notificación local                              | `src/notifications.py`             |
| Historial de ejecuciones                        | `src/pipeline_state.py`            |
| Pruebas unitarias                               | `tests/`                           |
| CI                                              | `.github/workflows/ci.yml`         |

Resultados esperados:

```text
Quality checks: 47/47
Great Expectations style checks: 14/14
Pytest: 6 passed
Ruff: All checks passed
```

---

## 10. Orquestación

El DAG de Airflow fue ejecutado localmente con Docker Compose.

Archivo principal:

```text
orchestration/dags/retailmax_medallion_dag.py
```

Flujo general:

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

Esta ejecución valida el flujo del pipeline, pero no representa un despliegue productivo de Airflow.

---

## 11. Monitoreo y alertas

Actualmente se generan reportes y notificaciones locales en archivos de evidencia:

```text
docs/evidence/pipeline_execution_report.txt
docs/evidence/pipeline_notification.txt
docs/evidence/pipeline_run_history_summary.txt
```

También existe un Action Group creado por Bicep como base para alertas en Azure.

Las alertas reales por correo, Teams, Slack o Azure Monitor no se configuraron dentro del alcance actual. La notificación actual es local y puede evolucionar hacia un canal externo usando variables de entorno.

---

## 12. CI y pruebas

Se agregó GitHub Actions para validar el repositorio.

Workflow:

```text
.github/workflows/ci.yml
```

El workflow ejecuta:

```text
ruff check .
pytest
validación de imports principales
```

Las pruebas unitarias están en:

```text
tests/
```

Estas pruebas cubren módulos críticos sin conectarse a servicios reales, incluyendo una simulación de carga a Azure mediante mocks.

---

## 13. Limitaciones actuales

* No se implementaron roles reales en Azure ni evidencia de acceso denegado para un perfil Analyst.
* No se integró Azure Key Vault directamente al runtime del pipeline.
* No se configuraron alertas reales conectadas a correo, Teams, Slack o Azure Monitor.
* Airflow se ejecuta localmente con Docker Compose, no en un entorno administrado.
* El pipeline opera en modo batch/full refresh y no implementa incrementalidad por watermark.
* Great Expectations se usa como estilo de validación formal, pero no como Data Context completo.
* La infraestructura Bicep es una base funcional y no una plataforma productiva multiambiente.

Estas partes quedan documentadas como siguientes pasos porque el alcance principal fue construir un pipeline funcional, validado, reproducible y defendible.
