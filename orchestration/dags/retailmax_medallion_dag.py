import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path("/opt/airflow/project")
sys.path.append(str(PROJECT_ROOT))

from src.bronze_ingestion import ingest_postgres_to_bronze  # noqa: E402
from src.create_partitioned_outputs import create_partitioned_gold_outputs  # noqa: E402
from src.error_handling import generate_pipeline_error_table  # noqa: E402
from src.execution_report import generate_execution_report  # noqa: E402
from src.generate_data import generate_bronze_data  # noqa: E402
from src.gold_transform import run_gold_transformations  # noqa: E402
from src.great_expectations_checks import run_great_expectations_checks  # noqa: E402
from src.load_to_postgres import load_bronze_to_postgres  # noqa: E402
from src.notifications import generate_pipeline_notification  # noqa: E402
from src.pipeline_state import (  # noqa: E402
    register_pipeline_end,
    register_pipeline_start,
)
from src.quality_checks import run_quality_checks  # noqa: E402
from src.silver_transform import run_silver_transformations  # noqa: E402
from src.upload_to_azure import upload_outputs_to_azure  # noqa: E402
from src.utils import ensure_directories, load_config  # noqa: E402

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=60),
}


def _load_project_config() -> dict:
    """Carga la configuración del proyecto usando rutas absolutas en Airflow."""
    config = load_config(str(PROJECT_ROOT / "config" / "config.yaml"))

    for layer in ["bronze", "silver", "gold"]:
        config["paths"][layer] = str(PROJECT_ROOT / config["paths"][layer])

    config["paths"]["bronze_ingested"] = str(PROJECT_ROOT / "data/bronze_ingested")
    config["paths"]["gold_partitioned"] = str(PROJECT_ROOT / "data/gold_partitioned")
    config["paths"]["errors"] = str(PROJECT_ROOT / "data/errors")
    config["paths"]["control"] = str(PROJECT_ROOT / "data/control")
    config["paths"]["evidence"] = str(PROJECT_ROOT / "docs/evidence")

    ensure_directories(config)
    return config


def run_pipeline_start_layer() -> None:
    """Registra el inicio de la ejecucion del pipeline."""
    config = _load_project_config()
    register_pipeline_start(config)


def run_pipeline_end_layer() -> None:
    """Registra el cierre exitoso de la ejecucion del pipeline."""
    config = _load_project_config()
    register_pipeline_end(config, pipeline_status="success")


def run_bronze_layer() -> None:
    """Ejecuta la generación de datos Bronze."""
    config = _load_project_config()
    generate_bronze_data(config)


def run_postgres_load_layer() -> None:
    """Carga las tablas Bronze CSV a PostgreSQL local."""
    config = _load_project_config()
    load_bronze_to_postgres(config)


def run_bronze_ingestion_layer() -> None:
    """Ingesta tablas desde PostgreSQL hacia Bronze Parquet con auditoría."""
    config = _load_project_config()
    ingest_postgres_to_bronze(config)


def run_silver_layer() -> None:
    """Ejecuta las transformaciones hacia Silver."""
    config = _load_project_config()
    run_silver_transformations(config)


def run_gold_layer() -> None:
    """Ejecuta las transformaciones hacia Gold."""
    config = _load_project_config()
    run_gold_transformations(config)


def run_partitioned_gold_layer() -> None:
    """Genera salidas Gold particionadas."""
    config = _load_project_config()
    create_partitioned_gold_outputs(config)


def run_quality_layer() -> None:
    """Ejecuta las validaciones de calidad."""
    config = _load_project_config()
    run_quality_checks(config)


def run_great_expectations_layer() -> None:
    """Ejecuta validaciones formales tipo Great Expectations."""
    config = _load_project_config()
    run_great_expectations_checks(config)


def run_error_handling_layer() -> None:
    """Genera la tabla de errores del pipeline."""
    config = _load_project_config()
    generate_pipeline_error_table(config)


def run_execution_report_layer() -> None:
    """Genera el reporte operativo consolidado del pipeline."""
    config = _load_project_config()
    generate_execution_report(config)


def run_notification_layer() -> None:
    """Genera una notificacion operativa local del pipeline."""
    config = _load_project_config()
    generate_pipeline_notification(config)


def run_azure_upload_layer() -> None:
    """Sube salidas Gold y evidencias a Azure Blob Storage."""
    config = _load_project_config()
    upload_outputs_to_azure(config)


with DAG(
    dag_id="retailmax_medallion_pipeline",
    description=(
        "Pipeline Medallion RetailMax con generación Bronze, "
        "carga PostgreSQL, ingesta Bronze Parquet, Silver, Gold y calidad."
    ),
    default_args=default_args,
    start_date=datetime(2026, 6, 20),
    schedule="0 2 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["retailmax", "medallion", "data-engineering"],
) as dag:
    start = EmptyOperator(task_id="start")

    bronze = PythonOperator(
        task_id="generate_bronze_data",
        python_callable=run_bronze_layer,
    )

    postgres_load = PythonOperator(
        task_id="load_bronze_to_postgres",
        python_callable=run_postgres_load_layer,
    )

    bronze_ingestion = PythonOperator(
        task_id="ingest_postgres_to_bronze",
        python_callable=run_bronze_ingestion_layer,
    )

    silver = PythonOperator(
        task_id="run_silver_transformations",
        python_callable=run_silver_layer,
    )

    gold = PythonOperator(
        task_id="run_gold_transformations",
        python_callable=run_gold_layer,
    )

    partitioned_gold = PythonOperator(
        task_id="create_partitioned_gold_outputs",
        python_callable=run_partitioned_gold_layer,
    )

    quality_checks = PythonOperator(
        task_id="run_quality_checks",
        python_callable=run_quality_layer,
    )

    great_expectations_checks = PythonOperator(
        task_id="run_great_expectations_checks",
        python_callable=run_great_expectations_layer,
    )

    error_handling = PythonOperator(
        task_id="generate_pipeline_error_table",
        python_callable=run_error_handling_layer,
    )

    execution_report = PythonOperator(
        task_id="generate_execution_report",
        python_callable=run_execution_report_layer,
    )

    notification = PythonOperator(
        task_id="generate_pipeline_notification",
        python_callable=run_notification_layer,
    )

    pipeline_start = PythonOperator(
        task_id="register_pipeline_start",
        python_callable=run_pipeline_start_layer,
    )

    pipeline_end = PythonOperator(
        task_id="register_pipeline_end",
        python_callable=run_pipeline_end_layer,
    )

    azure_upload = PythonOperator(
        task_id="upload_outputs_to_azure",
        python_callable=run_azure_upload_layer,
    )

    end = EmptyOperator(task_id="end")

    (
        start
        >> pipeline_start
        >> bronze
        >> postgres_load
        >> bronze_ingestion
        >> silver
        >> gold
        >> partitioned_gold
        >> quality_checks
        >> great_expectations_checks
        >> error_handling
        >> execution_report
        >> notification
        >> azure_upload
        >> pipeline_end
        >> end
    )
