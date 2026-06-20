import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.generate_data import generate_bronze_data
from src.gold_transform import run_gold_transformations
from src.quality_checks import run_quality_checks
from src.silver_transform import run_silver_transformations
from src.utils import ensure_directories, load_config

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=60),
}


def _load_project_config() -> dict:
    """Carga la configuración del proyecto."""
    config = load_config(str(PROJECT_ROOT / "config" / "config.yaml"))
    ensure_directories(config)
    return config


def run_bronze_layer() -> None:
    """Ejecuta la generación de datos Bronze."""
    config = _load_project_config()
    generate_bronze_data(config)


def run_silver_layer() -> None:
    """Ejecuta las transformaciones hacia Silver."""
    config = _load_project_config()
    run_silver_transformations(config)


def run_gold_layer() -> None:
    """Ejecuta las transformaciones hacia Gold."""
    config = _load_project_config()
    run_gold_transformations(config)


def run_quality_layer() -> None:
    """Ejecuta las validaciones de calidad."""
    config = _load_project_config()
    run_quality_checks(config)


with DAG(
    dag_id="retailmax_medallion_pipeline",
    description="Pipeline Medallion RetailMax: Bronze, Silver, Gold y calidad.",
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

    silver = PythonOperator(
        task_id="run_silver_transformations",
        python_callable=run_silver_layer,
    )

    gold = PythonOperator(
        task_id="run_gold_transformations",
        python_callable=run_gold_layer,
    )

    quality_checks = PythonOperator(
        task_id="run_quality_checks",
        python_callable=run_quality_layer,
    )

    end = EmptyOperator(task_id="end")

    start >> bronze >> silver >> gold >> quality_checks >> end
