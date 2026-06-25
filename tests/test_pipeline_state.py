import pandas as pd

from src.pipeline_state import register_pipeline_end, register_pipeline_start


def test_pipeline_state_registers_start_and_end(tmp_path):
    """Valida que el historial registre inicio y cierre de ejecucion."""
    config = {
        "paths": {
            "control": str(tmp_path / "control"),
            "evidence": str(tmp_path / "evidence"),
        }
    }

    run_id = register_pipeline_start(config)
    register_pipeline_end(config, run_id=run_id)

    history_path = tmp_path / "control" / "pipeline_run_history.parquet"
    summary_path = tmp_path / "evidence" / "pipeline_run_history_summary.txt"
    csv_path = tmp_path / "evidence" / "pipeline_run_history.csv"

    assert history_path.exists()
    assert summary_path.exists()
    assert csv_path.exists()

    history_df = pd.read_parquet(history_path)

    assert len(history_df) == 1
    assert history_df.loc[0, "run_id"] == run_id
    assert history_df.loc[0, "pipeline_status"] == "success"
    assert history_df.loc[0, "records_processed"] == 1_855_950
