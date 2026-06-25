# Changelog

## 2026-06-18

* Se inició el proyecto RetailMax con arquitectura Medallion.
* Se definió la estructura base del repositorio.
* Se agregó configuración del proyecto mediante `config.yaml`.
* Se implementó la generación de datos sintéticos con semilla fija.
* Se generaron las tablas fuente de la capa Bronze.

## 2026-06-19

* Se implementaron las transformaciones de Bronze a Silver.
* Se implementaron las transformaciones de Silver a Gold.
* Se crearon dimensiones, tablas de hechos y KPIs analíticos.
* Se agregaron reglas de negocio para ventas, inventario, devoluciones y clientes.
* Se agregaron validaciones de calidad del pipeline.
* Se generó evidencia de validaciones exitosas.

## 2026-06-20

* Se agregó carga de datos Bronze a PostgreSQL local.
* Se generó evidencia de conteos por tabla desde PostgreSQL.
* Se creó documentación técnica de arquitectura, modelo de datos, linaje y catálogo.
* Se documentaron anomalías controladas y errores esperados del pipeline.
* Se configuró Azure Blob Storage desde Azure Portal.
* Se cargaron evidencias y salidas Gold en Azure.
* Se agregó documentación de gobierno, seguridad e infraestructura.
* Se agregó una definición inicial de DAG para Apache Airflow.

## 2026-06-21

* Se agregó una versión mínima de Infraestructura como Código con Bicep.
* Se desplegó el template Bicep con Azure CLI en un Resource Group de prueba.
* Se agregó evidencia visual del despliegue Bicep.
* Se configuró Airflow local usando Docker Compose.
* Se agregó una imagen local de Airflow con las dependencias necesarias del pipeline.
* Se ejecutó correctamente el DAG `retailmax_medallion_pipeline` en Airflow local.
* Se agregaron evidencias del DAG ejecutado y del grafo de tareas.
* Se agregaron ejemplos de reporte diario, alerta de fallo y alerta por anomalía de volumen.
* Se agregó una muestra inicial de errores del pipeline en `pipeline_errors.csv`.
* Se agregó una salida Gold particionada como evidencia separada.
* Se ajustó `.gitignore` para excluir datos generados, cachés y logs locales.
* Se eliminó un archivo vacío no utilizado: `src/cloud.upload.py`.

## 2026-06-22

* Se creó una rama de mejoras `improvements/full-deliverables` para completar entregables pendientes y fortalecer el proyecto.
* Se revisó la implementación inicial de PostgreSQL para convertirla en una fuente relacional más integrada al flujo.
* Se implementó `src/bronze_ingestion.py` para ingestar tablas desde PostgreSQL hacia Bronze Parquet.
* Se agregaron columnas de auditoría en la ingesta Bronze: `ingestion_timestamp`, `source_system` y `batch_id`.
* Se generó evidencia de ingesta en `docs/evidence/bronze_ingestion_log.txt`.
* Se integró la carga PostgreSQL y la ingesta Bronze auditada al DAG de Airflow.
* Se corrigió la configuración de Airflow para usar rutas absolutas dentro del contenedor.
* Se agregó soporte de variables de entorno para PostgreSQL dentro de Docker Compose.
* Se validó la ingesta PostgreSQL -> Bronze Parquet desde Airflow.
* Se actualizaron evidencias del flujo Airflow con PostgreSQL e ingesta Bronze auditada.

## 2026-06-23

* Se implementó `src/error_handling.py` para generar una tabla real de errores del pipeline.
* Se generaron salidas de errores en `data/errors/pipeline_errors.parquet`, `docs/evidence/pipeline_errors.csv` y `docs/evidence/pipeline_errors_summary.txt`.
* Se integró la generación de errores al DAG de Airflow.
* Se actualizó `src/create_partitioned_outputs.py` para generar salidas Gold particionadas desde configuración.
* Se integró la salida particionada de `kpi_ventas_diarias` al pipeline principal de Airflow.
* Se generó evidencia actualizada en `docs/evidence/partitioned_outputs_summary.txt`.
* Se instaló y registró Great Expectations como dependencia del proyecto.
* Se implementó `src/great_expectations_checks.py` con validaciones formales estilo expectations sobre tablas Gold.
* Se generaron evidencias de validación formal en `docs/evidence/great_expectations_summary.csv` y `docs/evidence/great_expectations_summary.txt`.
* Se integraron las validaciones formales al DAG de Airflow.
* Se actualizó el `Dockerfile` de Airflow para incluir dependencias necesarias como Great Expectations.
* Se validó el flujo de calidad con 47 validaciones personalizadas y 14 validaciones formales exitosas.

## 2026-06-24

* Se implementó `src/execution_report.py` para generar un reporte operativo consolidado del pipeline.
* Se generó `docs/evidence/pipeline_execution_report.txt`.
* Se implementó `src/notifications.py` para generar una notificación operativa local del resultado del pipeline.
* Se generó `docs/evidence/pipeline_notification.txt`.
* Se implementó `src/pipeline_state.py` para registrar el inicio, cierre, duración, estado y volumen procesado por ejecución.
* Se generaron evidencias de historial en `docs/evidence/pipeline_run_history.csv` y `docs/evidence/pipeline_run_history_summary.txt`.
* Se integró el control de estado del pipeline al DAG de Airflow.
* Se agregó GitHub Actions en `.github/workflows/ci.yml`.
* Se configuró CI para ejecutar Ruff e imports principales del proyecto.
* Se implementaron pruebas unitarias con pytest para módulos críticos del pipeline.
* Se agregó `pytest.ini` para limitar la recolección de pruebas a la carpeta `tests/` y evitar logs locales de Airflow.
* Se agregaron pruebas para errores, validaciones formales, notificaciones, particionamiento, estado del pipeline y carga simulada a Azure.
* Se actualizó GitHub Actions para ejecutar pytest dentro del workflow de CI.
* Se validó localmente el proyecto con `ruff check .` y `python -m pytest`.

## 2026-06-25

* Se implementó `src/upload_to_azure.py` para subir salidas Gold y evidencias a Azure Blob Storage.
* Se agregaron los contenedores lógicos `gold` y `evidence` como destinos de carga.
* Se generó manifiesto de carga en `docs/evidence/azure_upload_manifest.csv`.
* Se generó resumen de carga en `docs/evidence/azure_upload_summary.txt`.
* Se integró la carga a Azure Blob Storage al DAG de Airflow usando `AZURE_STORAGE_CONNECTION_STRING` como variable de entorno.
* Se actualizó `orchestration/docker-compose.yaml` para pasar variables de entorno requeridas por PostgreSQL y Azure.
* Se validó la carga a Azure desde Airflow con salidas Gold y evidencias operativas.
* Se actualizaron evidencias del DAG completo, incluyendo flujo completo en Airflow, historial de ejecución, reporte operativo, notificación local y carga a Azure.
* Se actualizó `README.md` para reflejar el alcance final del pipeline, tecnologías, ejecución, evidencias, seguridad, pruebas y limitaciones actuales.
