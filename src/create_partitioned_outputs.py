from pathlib import Path

import pandas as pd

from src.utils import load_config


def create_partitioned_gold_outputs(config: dict) -> None:
    """Genera una salida Gold particionada por año y mes."""
    gold_path = Path(config["paths"]["gold"])
    source_file = gold_path / "kpi_ventas_diarias.parquet"
    output_path = Path("data/gold_partitioned/kpi_ventas_diarias")

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

    summary_path = Path("docs/evidence/partitioned_outputs_summary.txt")
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    partition_count = sum(1 for path in output_path.rglob("*.parquet"))

    lines = [
        "RetailMax - Evidencia de salida particionada",
        "=" * 50,
        "",
        "Tabla origen: data/gold/kpi_ventas_diarias.parquet",
        "Tabla particionada: data/gold_partitioned/kpi_ventas_diarias",
        "Columnas de partición: year, month",
        f"Archivos Parquet generados: {partition_count}",
        "",
        "Nota:",
        "La salida particionada se genera como evidencia separada para no modificar el pipeline principal.",
    ]

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print("Salida particionada generada correctamente.")
    print(f"Ruta generada: {output_path}")
    print(f"Resumen generado en: {summary_path}")


if __name__ == "__main__":
    project_config = load_config()
    create_partitioned_gold_outputs(project_config)
