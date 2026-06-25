import pandas as pd

from src.great_expectations_checks import run_great_expectations_checks


def test_run_great_expectations_checks_success(tmp_path):
    """Valida que las expectativas formales pasen con datos correctos."""
    gold_path = tmp_path / "gold"
    evidence_path = tmp_path / "evidence"

    gold_path.mkdir(parents=True)

    pd.DataFrame(
        {
            "id_trans": [1, 2],
            "fec_trans": ["2026-01-01", "2026-01-02"],
            "vr_venta_neto": [100.0, 200.0],
            "canal_venta": ["physical_store", "ecommerce"],
        }
    ).to_parquet(gold_path / "fact_ventas.parquet", index=False)

    pd.DataFrame(
        {
            "id_snapshot": [1, 2],
            "stock_fisico": [10, 20],
            "cobertura_dias": [5.0, 10.0],
        }
    ).to_parquet(gold_path / "fact_inventario.parquet", index=False)

    pd.DataFrame(
        {
            "id_devolucion": [1, 2],
            "qty_devuelta": [1, 2],
            "tasa_devolucion_articulo": [0.1, 0.2],
        }
    ).to_parquet(gold_path / "fact_devoluciones.parquet", index=False)

    pd.DataFrame(
        {
            "id_miembro": [1, 2],
            "id_miembro_hash": ["hash_1", "hash_2"],
            "genero": ["M", "No informado"],
        }
    ).to_parquet(gold_path / "dim_clientes.parquet", index=False)

    config = {
        "paths": {
            "gold": str(gold_path),
            "evidence": str(evidence_path),
        }
    }

    run_great_expectations_checks(config)

    summary_path = evidence_path / "great_expectations_summary.txt"
    csv_path = evidence_path / "great_expectations_summary.csv"

    assert summary_path.exists()
    assert csv_path.exists()

    summary_text = summary_path.read_text(encoding="utf-8")

    assert "total_expectations: 14" in summary_text
    assert "successful_expectations: 14" in summary_text
    assert "failed_expectations: 0" in summary_text
