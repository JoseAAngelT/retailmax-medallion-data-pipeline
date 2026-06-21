# Gobierno y seguridad

Este documento resume las decisiones de gobierno, seguridad y privacidad consideradas para el proyecto RetailMax.

## Alcance actual

En esta versión se implementaron controles básicos:

* no se guardan contraseñas ni claves en el repositorio;
* la conexión a PostgreSQL usa variables de entorno;
* las capturas de Azure fueron editadas para ocultar información sensible;
* los contenedores de Azure Blob Storage se configuraron con acceso privado;
* el Storage Account tiene acceso anónimo deshabilitado;
* se usa TLS 1.2;
* se genera un hash SHA-256 para el identificador del cliente en Gold;
* se agregó una base de IaC con Bicep;
* se creó Key Vault como recurso base para gestión de secretos;
* se creó Log Analytics Workspace como base para monitoreo;
* se creó Action Group como base para alertas;
* se generaron ejemplos de reportes y alertas operativas.

## Roles propuestos

| Rol           | Acceso propuesto                              | Uso                                           |
| ------------- | --------------------------------------------- | --------------------------------------------- |
| Data Engineer | Lectura y escritura en Bronze, Silver y Gold. | Operar y mantener el pipeline.                |
| Analyst       | Solo lectura en Gold.                         | Consumir datos para análisis y reportes.      |
| Admin         | Control total sobre recursos del proyecto.    | Administración de infraestructura y permisos. |

## Principio de mínimo privilegio

En una versión productiva, cada componente debería usar una identidad separada:

| Componente                 | Identidad sugerida                 | Permisos                                             |
| -------------------------- | ---------------------------------- | ---------------------------------------------------- |
| Pipeline de ingesta        | Service principal de ingesta       | Escritura en Bronze.                                 |
| Pipeline de transformación | Service principal de procesamiento | Lectura en Bronze/Silver y escritura en Silver/Gold. |
| Usuarios analistas         | Grupo de analistas                 | Lectura solo en Gold.                                |

## Datos sensibles

| Campo             | Tabla                                                         | Tratamiento                                                            |
| ----------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `id_miembro`      | `CRM_MIEMBROS`, `TRANS_VENTAS`, `dim_clientes`, `fact_ventas` | Se conserva para integridad, pero se genera `id_miembro_hash` en Gold. |
| `id_miembro_hash` | `dim_clientes`                                                | Hash SHA-256 estable.                                                  |
| `genero`          | `dim_clientes`                                                | Se estandariza a `M`, `F` o `No informado`.                            |
| `rango_edad`      | `dim_clientes`                                                | Se imputa cuando viene nulo.                                           |

## Secretos

No se incluyen secretos en el código.

Para PostgreSQL local, las credenciales se configuran en la sesión de PowerShell:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

Para Airflow local, se usa un archivo `.env` ignorado por Git. Se incluye un archivo `.env.example` como plantilla sin secretos reales:

```text
orchestration/.env.example
```

En una versión productiva, las credenciales deberían almacenarse en Azure Key Vault. En este proyecto, Key Vault fue creado como recurso base mediante Bicep.

## Monitoreo y alertas

Actualmente, el pipeline genera evidencia local mediante:

```text
docs/evidence/quality_checks_summary.txt
docs/evidence/silver_quality_report.txt
docs/evidence/postgres_counts_summary.txt
docs/evidence/pipeline_errors.csv
```

También se generaron ejemplos de notificaciones operativas:

```text
docs/evidence/sample_success_report.txt
docs/evidence/sample_failure_alert.txt
docs/evidence/sample_volume_anomaly_alert.txt
```

El proyecto incluye un Action Group creado por Bicep como base para alertas en Azure. Las alertas reales por correo o Teams no se configuraron dentro del alcance actual.

## Orquestación

El DAG de Airflow fue ejecutado localmente con Docker Compose.

Evidencias:

```text
docs/evidence/airflow_dag_success.png
docs/evidence/airflow_dag_graph_success.png
```

Esta ejecución valida el flujo del pipeline, pero no representa un despliegue productivo de Airflow.

## Limitaciones actuales

No se implementaron roles reales en Azure ni evidencia de acceso denegado para un perfil Analyst.

No se configuraron alertas reales conectadas a correo, Teams o reglas de Azure Monitor. Se dejó una base con Action Group y ejemplos de alertas generadas como evidencia.

Key Vault y Log Analytics fueron creados como recursos base mediante Bicep, pero no se integraron todavía al pipeline principal.

Estas partes quedan documentadas como siguientes pasos porque el alcance principal de la entrega fue construir un pipeline funcional, validado y reproducible.
