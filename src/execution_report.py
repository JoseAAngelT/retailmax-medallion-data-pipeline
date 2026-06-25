from datetime import datetime
from pathlib import Path

from src.utils import load_config


def _read_text_if_exists(file_path: Path) -> str:
    """Lee un archivo de texto si existe."""
    if not file_path.exists():
        return "Archivo no disponible."

    return file_path.read_text(encoding="utf-8")


def generate_execution_report(config: dict) -> None:
    """Genera un reporte operativo consolidado de la ejecucion del pipeline."""
    evidence_path = Path(config.get("paths", {}).get("evidence", "docs/evidence"))
    report_path = evidence_path / "pipeline_execution_report.txt"

    bronze_ingestion_log = evidence_path / "bronze_ingestion_log.txt"
    quality_summary = evidence_path / "quality_checks_summary.txt"
    great_expectations_summary = evidence_path / "great_expectations_summary.txt"
    pipeline_errors_summary = evidence_path / "pipeline_errors_summary.txt"
    partitioned_outputs_summary = evidence_path / "partitioned_outputs_summary.txt"
    postgres_counts_summary = evidence_path / "postgres_counts_summary.txt"

    lines = [
        "RetailMax - Pipeline execution report",
        "=" * 60,
        f"execution_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "pipeline_status: completed",
        "",
        "Resumen de componentes ejecutados:",
        "-" * 60,
        "- Bronze data generation",
        "- Bronze load to PostgreSQL",
        "- PostgreSQL to Bronze Parquet ingestion with audit metadata",
        "- Silver transformations",
        "- Gold transformations",
        "- Partitioned Gold outputs",
        "- Custom quality checks",
        "- Great Expectations style checks",
        "- Pipeline error table generation",
        "",
        "PostgreSQL load evidence:",
        "-" * 60,
        _read_text_if_exists(postgres_counts_summary),
        "",
        "Bronze ingestion evidence:",
        "-" * 60,
        _read_text_if_exists(bronze_ingestion_log),
        "",
        "Partitioned Gold output evidence:",
        "-" * 60,
        _read_text_if_exists(partitioned_outputs_summary),
        "",
        "Custom quality checks evidence:",
        "-" * 60,
        _read_text_if_exists(quality_summary),
        "",
        "Great Expectations evidence:",
        "-" * 60,
        _read_text_if_exists(great_expectations_summary),
        "",
        "Pipeline errors evidence:",
        "-" * 60,
        _read_text_if_exists(pipeline_errors_summary),
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("Reporte operativo del pipeline generado correctamente.")
    print(f"Ruta generada: {report_path}")


if __name__ == "__main__":
    project_config = load_config()
    generate_execution_report(project_config)
