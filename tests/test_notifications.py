import pandas as pd

from src.notifications import generate_pipeline_notification


def test_generate_pipeline_notification(tmp_path):
    """Valida que se genere la notificacion operativa local."""
    evidence_path = tmp_path / "evidence"
    evidence_path.mkdir(parents=True)

    pd.DataFrame(
        {
            "table_name": ["fact_ventas", "dim_clientes"],
            "expectation": ["check_1", "check_2"],
            "success": [True, True],
            "unexpected_count": [0, 0],
        }
    ).to_csv(evidence_path / "great_expectations_summary.csv", index=False)

    pd.DataFrame(
        {
            "severity": ["info"],
            "error_type": ["NO_ERRORS_DETECTED"],
        }
    ).to_csv(evidence_path / "pipeline_errors.csv", index=False)

    quality_text = "\n".join(
        [
            "RetailMax Medallion Data Pipeline - Resumen de calidad",
            "Total de validaciones: 47",
            "Validaciones exitosas: 47",
            "Validaciones fallidas: 0",
            "",
            "Detalle de validaciones:",
        ]
    )
    (evidence_path / "quality_checks_summary.txt").write_text(
        quality_text,
        encoding="utf-8",
    )

    config = {
        "paths": {
            "evidence": str(evidence_path),
        }
    }

    generate_pipeline_notification(config)

    notification_path = evidence_path / "pipeline_notification.txt"

    assert notification_path.exists()

    notification_text = notification_path.read_text(encoding="utf-8")

    assert "pipeline_status: success" in notification_text
    assert "Great Expectations: 2/2 successful (0 failed)" in notification_text
    assert "Pipeline errors: info: 1" in notification_text
