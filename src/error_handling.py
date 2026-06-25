from datetime import datetime
from pathlib import Path

import pandas as pd

from src.utils import load_config


def _build_error_record(
    table_name: str,
    error_type: str,
    error_description: str,
    severity: str,
    records_affected: int,
) -> dict:
    """Construye un registro estándar para la tabla de errores."""
    return {
        "error_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "table_name": table_name,
        "error_type": error_type,
        "error_description": error_description,
        "severity": severity,
        "records_affected": records_affected,
    }


def generate_pipeline_error_table(config: dict) -> None:
    """Genera una tabla real de errores a partir de validaciones del pipeline."""
    gold_path = Path(config["paths"]["gold"])
    errors_path = Path(config.get("paths", {}).get("errors", "data/errors"))
    evidence_path = Path(config.get("paths", {}).get("evidence", "docs/evidence"))

    errors_path.mkdir(parents=True, exist_ok=True)
    evidence_path.mkdir(parents=True, exist_ok=True)

    error_records = []

    fact_ventas_path = gold_path / "fact_ventas.parquet"
    fact_inventario_path = gold_path / "fact_inventario.parquet"
    fact_devoluciones_path = gold_path / "fact_devoluciones.parquet"

    if fact_ventas_path.exists():
        fact_ventas = pd.read_parquet(fact_ventas_path)

        negative_sales = fact_ventas[fact_ventas["vr_venta_neto"] < 0]
        if not negative_sales.empty:
            error_records.append(
                _build_error_record(
                    table_name="fact_ventas",
                    error_type="NEGATIVE_NET_SALE",
                    error_description="Ventas con valor neto negativo.",
                    severity="high",
                    records_affected=len(negative_sales),
                )
            )

        missing_member = fact_ventas["id_miembro"].isna().sum()
        if missing_member > 0:
            error_records.append(
                _build_error_record(
                    table_name="fact_ventas",
                    error_type="MISSING_MEMBER_ID",
                    error_description="Ventas sin identificador de cliente.",
                    severity="medium",
                    records_affected=int(missing_member),
                )
            )
    else:
        error_records.append(
            _build_error_record(
                table_name="fact_ventas",
                error_type="MISSING_TABLE",
                error_description="No existe la tabla fact_ventas en Gold.",
                severity="critical",
                records_affected=0,
            )
        )

    if fact_inventario_path.exists():
        fact_inventario = pd.read_parquet(fact_inventario_path)

        invalid_coverage = fact_inventario[
            fact_inventario["cobertura_dias"].notna()
            & (fact_inventario["cobertura_dias"] < 0)
        ]
        if not invalid_coverage.empty:
            error_records.append(
                _build_error_record(
                    table_name="fact_inventario",
                    error_type="NEGATIVE_INVENTORY_COVERAGE",
                    error_description="Registros con cobertura de inventario negativa.",
                    severity="high",
                    records_affected=len(invalid_coverage),
                )
            )
    else:
        error_records.append(
            _build_error_record(
                table_name="fact_inventario",
                error_type="MISSING_TABLE",
                error_description="No existe la tabla fact_inventario en Gold.",
                severity="critical",
                records_affected=0,
            )
        )

    if fact_devoluciones_path.exists():
        fact_devoluciones = pd.read_parquet(fact_devoluciones_path)

        invalid_return_rate = fact_devoluciones[
            fact_devoluciones["tasa_devolucion_articulo"].notna()
            & (
                (fact_devoluciones["tasa_devolucion_articulo"] < 0)
                | (fact_devoluciones["tasa_devolucion_articulo"] > 1)
            )
        ]
        if not invalid_return_rate.empty:
            error_records.append(
                _build_error_record(
                    table_name="fact_devoluciones",
                    error_type="INVALID_RETURN_RATE",
                    error_description="Tasa de devolución fuera del rango 0 a 1.",
                    severity="high",
                    records_affected=len(invalid_return_rate),
                )
            )
    else:
        error_records.append(
            _build_error_record(
                table_name="fact_devoluciones",
                error_type="MISSING_TABLE",
                error_description="No existe la tabla fact_devoluciones en Gold.",
                severity="critical",
                records_affected=0,
            )
        )

    if not error_records:
        error_records.append(
            _build_error_record(
                table_name="pipeline",
                error_type="NO_ERRORS_DETECTED",
                error_description="No se detectaron errores críticos en las validaciones.",
                severity="info",
                records_affected=0,
            )
        )

    errors_df = pd.DataFrame(error_records)

    output_file = errors_path / "pipeline_errors.parquet"
    csv_output_file = evidence_path / "pipeline_errors.csv"
    summary_file = evidence_path / "pipeline_errors_summary.txt"

    errors_df.to_parquet(output_file, index=False)
    errors_df.to_csv(csv_output_file, index=False)

    summary_lines = [
        "RetailMax - Pipeline errors summary",
        "=" * 50,
        f"execution_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"total_error_records: {len(errors_df)}",
        "",
        "Errors by severity:",
        "-" * 50,
    ]

    severity_counts = errors_df["severity"].value_counts().to_dict()
    for severity, count in severity_counts.items():
        summary_lines.append(f"{severity}: {count}")

    summary_lines.extend(
        [
            "",
            "Output files:",
            "-" * 50,
            f"parquet: {output_file}",
            f"csv: {csv_output_file}",
        ]
    )

    summary_file.write_text("\n".join(summary_lines), encoding="utf-8")

    print("Tabla de errores del pipeline generada correctamente.")
    print(f"Errores registrados: {len(errors_df)}")
    print(f"Archivo Parquet: {output_file}")
    print(f"Evidencia CSV: {csv_output_file}")
    print(f"Resumen: {summary_file}")


if __name__ == "__main__":
    project_config = load_config()
    generate_pipeline_error_table(project_config)
