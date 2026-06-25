import pandas as pd

from src.error_handling import generate_pipeline_error_table


def test_generate_pipeline_error_table_without_errors(tmp_path):
    """Valida que se genere un registro informativo cuando no hay errores."""
    gold_path = tmp_path / "gold"
    errors_path = tmp_path / "errors"
    evidence_path = tmp_path / "evidence"

    gold_path.mkdir(parents=True)

    pd.DataFrame(
        {
            "id_miembro": [1, 2],
            "vr_venta_neto": [100.0, 250.0],
        }
    ).to_parquet(gold_path / "fact_ventas.parquet", index=False)

    pd.DataFrame(
        {
            "cobertura_dias": [5.0, 10.0],
        }
    ).to_parquet(gold_path / "fact_inventario.parquet", index=False)

    pd.DataFrame(
        {
            "tasa_devolucion_articulo": [0.1, 0.2],
        }
    ).to_parquet(gold_path / "fact_devoluciones.parquet", index=False)

    config = {
        "paths": {
            "gold": str(gold_path),
            "errors": str(errors_path),
            "evidence": str(evidence_path),
        }
    }

    generate_pipeline_error_table(config)

    output_file = errors_path / "pipeline_errors.parquet"
    csv_file = evidence_path / "pipeline_errors.csv"
    summary_file = evidence_path / "pipeline_errors_summary.txt"

    assert output_file.exists()
    assert csv_file.exists()
    assert summary_file.exists()

    errors_df = pd.read_parquet(output_file)

    assert len(errors_df) == 1
    assert errors_df.loc[0, "error_type"] == "NO_ERRORS_DETECTED"
    assert errors_df.loc[0, "severity"] == "info"
