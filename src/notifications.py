from datetime import datetime
from pathlib import Path

import pandas as pd

from src.utils import load_config


def _read_text_if_exists(file_path: Path) -> str:
    """Lee un archivo de texto si existe."""
    if not file_path.exists():
        return "Archivo no disponible."

    return file_path.read_text(encoding="utf-8")


def _get_great_expectations_status(evidence_path: Path) -> str:
    """Obtiene el estado resumido de las validaciones formales."""
    summary_file = evidence_path / "great_expectations_summary.csv"

    if not summary_file.exists():
        return "Great Expectations summary no disponible."

    summary_df = pd.read_csv(summary_file)
    total_expectations = len(summary_df)
    successful_expectations = int(summary_df["success"].sum())
    failed_expectations = total_expectations - successful_expectations

    return (
        f"{successful_expectations}/{total_expectations} successful "
        f"({failed_expectations} failed)"
    )


def _get_pipeline_error_status(evidence_path: Path) -> str:
    """Obtiene el estado resumido de la tabla de errores."""
    errors_file = evidence_path / "pipeline_errors.csv"

    if not errors_file.exists():
        return "Pipeline errors summary no disponible."

    errors_df = pd.read_csv(errors_file)
    severity_counts = errors_df["severity"].value_counts().to_dict()

    return ", ".join(
        f"{severity}: {count}" for severity, count in severity_counts.items()
    )


def generate_pipeline_notification(config: dict) -> None:
    """Genera una notificacion operativa local del pipeline."""
    evidence_path = Path(config.get("paths", {}).get("evidence", "docs/evidence"))
    notification_path = evidence_path / "pipeline_notification.txt"

    quality_summary = _read_text_if_exists(evidence_path / "quality_checks_summary.txt")

    lines = [
        "RetailMax - Pipeline notification",
        "=" * 50,
        f"notification_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "pipeline_status: success",
        "",
        "Operational summary:",
        "-" * 50,
        "Pipeline execution completed successfully.",
        f"Great Expectations: {_get_great_expectations_status(evidence_path)}",
        f"Pipeline errors: {_get_pipeline_error_status(evidence_path)}",
        "Execution report: docs/evidence/pipeline_execution_report.txt",
        "",
        "Quality checks reference:",
        "-" * 50,
        quality_summary.split("Detalle de validaciones:")[0].strip(),
        "",
        "Next action:",
        "-" * 50,
        (
            "This local notification can be extended to email, Microsoft Teams, "
            "Slack or another alerting channel using environment variables."
        ),
    ]

    notification_path.write_text("\n".join(lines), encoding="utf-8")

    print("Notificacion operativa generada correctamente.")
    print(f"Ruta generada: {notification_path}")


if __name__ == "__main__":
    project_config = load_config()
    generate_pipeline_notification(project_config)
