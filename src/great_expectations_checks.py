from datetime import datetime
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from src.utils import load_config

GOLD_TABLES = {
    "fact_ventas": "fact_ventas.parquet",
    "fact_inventario": "fact_inventario.parquet",
    "fact_devoluciones": "fact_devoluciones.parquet",
    "dim_clientes": "dim_clientes.parquet",
}


def _get_evidence_path(config: dict) -> Path:
    """Obtiene la ruta de evidencias del proyecto."""
    return Path(config.get("paths", {}).get("evidence", "docs/evidence"))


def _build_expectation_result(
    table_name: str,
    expectation: str,
    success: bool,
    unexpected_count: int | None,
    details: Any = None,
) -> dict:
    """Construye un resultado estándar para una expectativa."""
    return {
        "table_name": table_name,
        "expectation": expectation,
        "success": success,
        "unexpected_count": unexpected_count,
        "details": details,
    }


def _expect_column_values_to_not_be_null(
    df: pd.DataFrame,
    table_name: str,
    column_name: str,
) -> dict:
    """Valida que una columna no tenga valores nulos."""
    unexpected_count = int(df[column_name].isna().sum())

    return _build_expectation_result(
        table_name=table_name,
        expectation=f"expect_column_values_to_not_be_null:{column_name}",
        success=unexpected_count == 0,
        unexpected_count=unexpected_count,
    )


def _expect_column_values_to_be_unique(
    df: pd.DataFrame,
    table_name: str,
    column_name: str,
) -> dict:
    """Valida que una columna tenga valores únicos."""
    unexpected_count = int(df[column_name].duplicated().sum())

    return _build_expectation_result(
        table_name=table_name,
        expectation=f"expect_column_values_to_be_unique:{column_name}",
        success=unexpected_count == 0,
        unexpected_count=unexpected_count,
    )


def _expect_column_values_to_be_between(
    df: pd.DataFrame,
    table_name: str,
    column_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    mostly: float = 1.0,
) -> dict:
    """Valida que una columna numérica esté dentro de un rango."""
    valid_mask = pd.Series(True, index=df.index)

    if min_value is not None:
        valid_mask &= df[column_name] >= min_value

    if max_value is not None:
        valid_mask &= df[column_name] <= max_value

    non_null_mask = df[column_name].notna()
    evaluated_mask = non_null_mask

    total_evaluated = int(evaluated_mask.sum())
    unexpected_count = int((~valid_mask & evaluated_mask).sum())

    success_ratio = (
        1 if total_evaluated == 0 else 1 - (unexpected_count / total_evaluated)
    )

    return _build_expectation_result(
        table_name=table_name,
        expectation=(
            f"expect_column_values_to_be_between:{column_name}:{min_value}:{max_value}"
        ),
        success=success_ratio >= mostly,
        unexpected_count=unexpected_count,
        details=f"mostly={mostly}, success_ratio={success_ratio:.4f}",
    )


def _expect_column_values_to_be_in_set(
    df: pd.DataFrame,
    table_name: str,
    column_name: str,
    allowed_values: list,
) -> dict:
    """Valida que una columna tenga valores dentro de un conjunto permitido."""
    unexpected_mask = ~df[column_name].isin(allowed_values)
    unexpected_count = int(unexpected_mask.sum())
    sample_unexpected = df.loc[unexpected_mask, column_name].dropna().unique()[:5]

    return _build_expectation_result(
        table_name=table_name,
        expectation=f"expect_column_values_to_be_in_set:{column_name}",
        success=unexpected_count == 0,
        unexpected_count=unexpected_count,
        details=list(sample_unexpected),
    )


def _validate_fact_ventas(df: pd.DataFrame) -> list[dict]:
    """Valida reglas formales para fact_ventas."""
    table_name = "fact_ventas"

    return [
        _expect_column_values_to_not_be_null(df, table_name, "id_trans"),
        _expect_column_values_to_be_unique(df, table_name, "id_trans"),
        _expect_column_values_to_not_be_null(df, table_name, "fec_trans"),
        _expect_column_values_to_be_between(
            df,
            table_name,
            "vr_venta_neto",
            min_value=0,
        ),
        _expect_column_values_to_be_in_set(
            df,
            table_name,
            "canal_venta",
            ["physical_store", "marketplace", "ecommerce"],
        ),
    ]


def _validate_fact_inventario(df: pd.DataFrame) -> list[dict]:
    """Valida reglas formales para fact_inventario."""
    table_name = "fact_inventario"

    return [
        _expect_column_values_to_not_be_null(df, table_name, "id_snapshot"),
        _expect_column_values_to_be_between(
            df,
            table_name,
            "stock_fisico",
            min_value=0,
        ),
        _expect_column_values_to_be_between(
            df,
            table_name,
            "cobertura_dias",
            min_value=0,
            mostly=0.95,
        ),
    ]


def _validate_fact_devoluciones(df: pd.DataFrame) -> list[dict]:
    """Valida reglas formales para fact_devoluciones."""
    table_name = "fact_devoluciones"

    return [
        _expect_column_values_to_not_be_null(df, table_name, "id_devolucion"),
        _expect_column_values_to_be_between(
            df,
            table_name,
            "qty_devuelta",
            min_value=1,
        ),
        _expect_column_values_to_be_between(
            df,
            table_name,
            "tasa_devolucion_articulo",
            min_value=0,
            max_value=1,
        ),
    ]


def _validate_dim_clientes(df: pd.DataFrame) -> list[dict]:
    """Valida reglas formales para dim_clientes."""
    table_name = "dim_clientes"

    return [
        _expect_column_values_to_not_be_null(df, table_name, "id_miembro"),
        _expect_column_values_to_not_be_null(df, table_name, "id_miembro_hash"),
        _expect_column_values_to_be_in_set(
            df,
            table_name,
            "genero",
            ["M", "F", "No informado"],
        ),
    ]


def _run_table_expectations(table_name: str, df: pd.DataFrame) -> list[dict]:
    """Ejecuta expectativas según la tabla Gold recibida."""
    if table_name == "fact_ventas":
        return _validate_fact_ventas(df)

    if table_name == "fact_inventario":
        return _validate_fact_inventario(df)

    if table_name == "fact_devoluciones":
        return _validate_fact_devoluciones(df)

    if table_name == "dim_clientes":
        return _validate_dim_clientes(df)

    return []


def run_great_expectations_checks(config: dict) -> None:
    """Ejecuta validaciones formales tipo Great Expectations sobre Gold."""
    gold_path = Path(config["paths"]["gold"])
    evidence_path = _get_evidence_path(config)
    evidence_path.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    for table_name, file_name in GOLD_TABLES.items():
        table_path = gold_path / file_name

        if not table_path.exists():
            summary_rows.append(
                _build_expectation_result(
                    table_name=table_name,
                    expectation="expect_table_to_exist",
                    success=False,
                    unexpected_count=None,
                    details=f"No existe {table_path}",
                )
            )
            continue

        df = pd.read_parquet(table_path)
        summary_rows.extend(_run_table_expectations(table_name, df))

    summary_df = pd.DataFrame(summary_rows)

    csv_path = evidence_path / "great_expectations_summary.csv"
    txt_path = evidence_path / "great_expectations_summary.txt"

    summary_df.to_csv(csv_path, index=False)

    total_expectations = len(summary_df)
    successful_expectations = int(summary_df["success"].sum())
    failed_expectations = total_expectations - successful_expectations

    lines = [
        "RetailMax - Great Expectations style summary",
        "=" * 50,
        f"execution_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"great_expectations_version: {gx.__version__}",
        f"total_expectations: {total_expectations}",
        f"successful_expectations: {successful_expectations}",
        f"failed_expectations: {failed_expectations}",
        "",
        "Results by table:",
        "-" * 50,
    ]

    for table_name in summary_df["table_name"].unique():
        table_results = summary_df[summary_df["table_name"] == table_name]
        table_success = int(table_results["success"].sum())
        table_total = len(table_results)
        lines.append(f"{table_name}: {table_success}/{table_total} successful")

    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print("Validaciones formales tipo Great Expectations ejecutadas correctamente.")
    print(f"Version Great Expectations instalada: {gx.__version__}")
    print(f"Expectativas evaluadas: {total_expectations}")
    print(f"Exitosas: {successful_expectations}")
    print(f"Fallidas: {failed_expectations}")
    print(f"Resumen CSV: {csv_path}")
    print(f"Resumen TXT: {txt_path}")

    if failed_expectations > 0:
        raise ValueError(
            "Se detectaron validaciones formales fallidas. "
            f"Revisar evidencia en {csv_path}."
        )


if __name__ == "__main__":
    project_config = load_config()
    run_great_expectations_checks(project_config)
