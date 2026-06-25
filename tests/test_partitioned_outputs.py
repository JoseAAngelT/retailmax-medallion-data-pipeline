import pandas as pd

from src.create_partitioned_outputs import create_partitioned_gold_outputs


def test_create_partitioned_gold_outputs(tmp_path):
    """Valida que se genere una salida Gold particionada por year y month."""
    gold_path = tmp_path / "gold"
    partitioned_path = tmp_path / "gold_partitioned"
    evidence_path = tmp_path / "evidence"

    gold_path.mkdir(parents=True)

    pd.DataFrame(
        {
            "fec_trans": ["2026-01-01", "2026-02-01"],
            "ventas_netas": [100.0, 200.0],
        }
    ).to_parquet(gold_path / "kpi_ventas_diarias.parquet", index=False)

    config = {
        "paths": {
            "gold": str(gold_path),
            "gold_partitioned": str(partitioned_path),
            "evidence": str(evidence_path),
        }
    }

    create_partitioned_gold_outputs(config)

    output_path = partitioned_path / "kpi_ventas_diarias"
    summary_path = evidence_path / "partitioned_outputs_summary.txt"

    assert output_path.exists()
    assert summary_path.exists()
    assert len(list(output_path.rglob("*.parquet"))) > 0

    summary_text = summary_path.read_text(encoding="utf-8")

    assert "partition_columns: year, month" in summary_text
    assert "records_processed: 2" in summary_text
