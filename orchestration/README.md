# Orquestación

Este proyecto incluye una ejecución local de Apache Airflow usando Docker Compose.

## Archivos principales

```text
orchestration/docker-compose.yaml
orchestration/Dockerfile
orchestration/.env.example
orchestration/dags/retailmax_medallion_dag.py
```

## Flujo del DAG

```text
start → generate_bronze_data → run_silver_transformations → run_gold_transformations → run_quality_checks → end
```

## Ejecutar Airflow localmente

Desde la carpeta `orchestration`:

```powershell
copy .env.example .env
docker compose build
docker compose up airflow-init
docker compose up -d
```

Abrir Airflow en:

```text
http://localhost:8080
```

Credenciales locales de prueba:

```text
airflow / airflow
```

## Evidencia

El DAG fue ejecutado correctamente en Airflow local.

Evidencias:

```text
docs/evidence/airflow_dag_success.png
docs/evidence/airflow_dag_graph_success.png
```

## Apagar servicios

```powershell
docker compose down
```

## Nota

Esta configuración es local y se usó para validar la definición del DAG. No representa un despliegue productivo de Airflow.
