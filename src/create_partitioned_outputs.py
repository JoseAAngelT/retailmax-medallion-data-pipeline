from datetime import datetime
from pathlib import Path

import pandas as pd

from src.utils import load_config


def _get_gold_partitioned_path(config: dict) -> Path:
    """Obtiene la ruta de salida para Gold particionado."""
    return Path(
        config.get("paths", {}).get(
            "gold_partitioned",
            "data/gold_partitioned",
        )
    )


def _get_evidence_path(config: dict) -> Path:
    """Obtiene la ruta de evidencias del proyecto."""
    return Path(config.get("paths", {}).get("evidence", "docs/evidence"))


def create_partitioned_gold_outputs(config: dict) -> None:
    """Genera salidas Gold particionadas para consumo analítico."""
    gold_path = Path(config["paths"]["gold"])
    output_base_path = _get_gold_partitioned_path(config)
    evidence_path = _get_evidence_path(config)

    source_file = gold_path / "kpi_ventas_diarias.parquet"
    output_path = output_base_path / "kpi_ventas_diarias"

    if not source_file.exists():
        raise FileNotFoundError(f"No se encontró la tabla Gold: {source_file}")

    df = pd.read_parquet(source_file)

    df["fec_trans"] = pd.to_datetime(df["fec_trans"])
    df["year"] = df["fec_trans"].dt.year
    df["month"] = df["fec_trans"].dt.month

    output_path.mkdir(parents=True, exist_ok=True)

    df.to_parquet(
        output_path,
        partition_cols=["year", "month"],
        index=False,
    )

    partition_count = sum(1 for path in output_path.rglob("*.parquet"))
    row_count = len(df)

    summary_path = evidence_path / "partitioned_outputs_summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "RetailMax - Evidencia de salida Gold particionada",
        "=" * 50,
        f"execution_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"source_table: {source_file}",
        f"partitioned_table: {output_path}",
        "partition_columns: year, month",
        f"records_processed: {row_count}",
        f"parquet_files_generated: {partition_count}",
        "",
        "Descripcion:",
        (
            "La salida particionada se genera como parte del pipeline para "
            "optimizar el consumo analitico por periodo."
        ),
    ]

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print("Salida Gold particionada generada correctamente.")
    print(f"Registros procesados: {row_count:,}")
    print(f"Archivos Parquet generados: {partition_count}")
    print(f"Ruta generada: {output_path}")
    print(f"Resumen generado en: {summary_path}")


if __name__ == "__main__":
    project_config = load_config()
    create_partitioned_gold_outputs(project_config)
