from pathlib import Path

import pandas as pd

from src.utils import load_config

SILVER_TABLES = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES",
]


def build_silver_quality_report(config: dict) -> None:
    """Genera un reporte básico de calidad para la capa Silver."""
    silver_path = Path(config["paths"]["silver"])
    output_path = Path("docs/evidence/silver_quality_report.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "RetailMax - Reporte de calidad Silver",
        "=" * 45,
        "",
    ]

    for table_name in SILVER_TABLES:
        file_path = silver_path / f"{table_name}.parquet"
        df = pd.read_parquet(file_path)

        total_rows = len(df)
        duplicate_rows = int(df.duplicated().sum())
        rows_with_nulls = int(df.isna().any(axis=1).sum())
        conforming_rows = total_rows - duplicate_rows
        conforming_percentage = (
            conforming_rows / total_rows * 100 if total_rows > 0 else 0
        )

        lines.extend(
            [
                f"Tabla: {table_name}",
                "-" * 45,
                f"Registros totales: {total_rows:,}",
                f"Duplicados exactos: {duplicate_rows:,}",
                f"Registros con al menos un nulo: {rows_with_nulls:,}",
                f"Registros conformes: {conforming_rows:,}",
                f"Porcentaje conforme: {conforming_percentage:.2f}%",
                "",
                "Porcentaje de nulos por columna:",
            ]
        )

        null_percentages = df.isna().mean().sort_values(ascending=False) * 100

        for column, null_percentage in null_percentages.items():
            lines.append(f"- {column}: {null_percentage:.2f}%")

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    print("Reporte de calidad Silver generado correctamente.")
    print(f"Resumen generado en: {output_path}")


if __name__ == "__main__":
    project_config = load_config()
    build_silver_quality_report(project_config)
