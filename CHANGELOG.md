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

* Se agregó una versión mínima de IaC con Bicep.
* Se desplegó el template Bicep con Azure CLI en un Resource Group de prueba.
* Se agregó evidencia visual del despliegue Bicep.
* Se configuró Airflow local usando Docker Compose.
* Se agregó una imagen local de Airflow con las dependencias necesarias del pipeline.
* Se ejecutó correctamente el DAG `retailmax_medallion_pipeline` en Airflow local.
* Se agregaron evidencias del DAG ejecutado y del grafo de tareas.
* Se agregaron ejemplos de reporte diario, alerta de fallo y alerta por anomalía de volumen.
* Se agregó una muestra de errores del pipeline en `pipeline_errors.csv`.
* Se agregó una salida Gold particionada como evidencia separada.
* Se ajustó `.gitignore` para excluir datos generados, cachés y logs locales.
* Se eliminó un archivo vacío no utilizado: `src/cloud.upload.py`.
