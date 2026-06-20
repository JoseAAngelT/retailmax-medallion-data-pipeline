from pathlib import Path

import pandas as pd

BRONZE_TABLES = {
    "MSTR_PROVEEDORES": 800,
    "MSTR_ARTICULOS": 5000,
    "MSTR_TIENDAS": 150,
    "CRM_MIEMBROS": 50000,
    "TRANS_VENTAS": 1000000,
    "INV_STOCK_DIARIO": 750000,
    "POST_DEVOLUCIONES": 50000,
}

SILVER_TABLES = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES",
]

GOLD_TABLES = [
    "dim_productos",
    "dim_tiendas",
    "dim_clientes",
    "fact_ventas",
    "fact_inventario",
    "fact_devoluciones",
    "fact_rfm_clientes",
    "kpi_ventas_diarias",
    "kpi_top_articulos_categoria",
]


def _add_check(
    results: list[dict[str, str]],
    check_name: str,
    passed: bool,
    detail: str,
) -> None:
    """Agrega el resultado de una validación."""
    status = "PASS" if passed else "FAIL"

    results.append(
        {
            "check_name": check_name,
            "status": status,
            "detail": detail,
        }
    )


def _read_gold_table(gold_path: Path, table_name: str) -> pd.DataFrame:
    """Lee una tabla Parquet desde la capa Gold."""
    return pd.read_parquet(gold_path / f"{table_name}.parquet")


def _validate_bronze_files(
    bronze_path: Path,
    results: list[dict[str, str]],
) -> None:
    """Valida existencia y volumen mínimo de tablas Bronze."""
    for table_name, minimum_rows in BRONZE_TABLES.items():
        file_path = bronze_path / f"{table_name}.csv"
        file_exists = file_path.exists()

        _add_check(
            results,
            f"Existe archivo Bronze - {table_name}",
            file_exists,
            str(file_path),
        )

        if file_exists:
            row_count = len(pd.read_csv(file_path))
            _add_check(
                results,
                f"Volumen mínimo Bronze - {table_name}",
                row_count >= minimum_rows,
                f"registros={row_count:,}, mínimo={minimum_rows:,}",
            )


def _validate_silver_files(
    silver_path: Path,
    results: list[dict[str, str]],
) -> None:
    """Valida existencia de tablas Silver."""
    for table_name in SILVER_TABLES:
        file_path = silver_path / f"{table_name}.parquet"

        _add_check(
            results,
            f"Existe archivo Silver - {table_name}",
            file_path.exists(),
            str(file_path),
        )


def _validate_gold_files(
    gold_path: Path,
    results: list[dict[str, str]],
) -> None:
    """Valida existencia de tablas Gold."""
    for table_name in GOLD_TABLES:
        file_path = gold_path / f"{table_name}.parquet"

        _add_check(
            results,
            f"Existe archivo Gold - {table_name}",
            file_path.exists(),
            str(file_path),
        )


def _validate_gold_row_counts(
    gold_tables: dict[str, pd.DataFrame],
    results: list[dict[str, str]],
) -> None:
    """Valida conteos esperados de las tablas principales de Gold."""
    expected_counts = {
        "dim_productos": 5000,
        "dim_tiendas": 150,
        "dim_clientes": 50001,
        "fact_ventas": 1000000,
        "fact_inventario": 750000,
        "fact_devoluciones": 50000,
    }

    for table_name, expected_rows in expected_counts.items():
        row_count = len(gold_tables[table_name])

        _add_check(
            results,
            f"Conteo Gold - {table_name}",
            row_count == expected_rows,
            f"registros={row_count:,}, esperado={expected_rows:,}",
        )


def _validate_referential_integrity(
    gold_tables: dict[str, pd.DataFrame],
    results: list[dict[str, str]],
) -> None:
    """Valida integridad referencial entre hechos y dimensiones."""
    dim_clientes = gold_tables["dim_clientes"]
    dim_productos = gold_tables["dim_productos"]
    dim_tiendas = gold_tables["dim_tiendas"]
    fact_ventas = gold_tables["fact_ventas"]
    fact_inventario = gold_tables["fact_inventario"]
    fact_devoluciones = gold_tables["fact_devoluciones"]

    valid_customers = set(dim_clientes["id_miembro"])
    valid_products = set(dim_productos["art_id"])
    valid_stores = set(dim_tiendas["id_tienda"])
    valid_transactions = set(fact_ventas["id_trans"])

    _add_check(
        results,
        "Integridad referencial - fact_ventas.id_miembro",
        fact_ventas["id_miembro"].isin(valid_customers).all(),
        "Todos los clientes de fact_ventas existen en dim_clientes.",
    )

    _add_check(
        results,
        "Integridad referencial - fact_ventas.art_id",
        fact_ventas["art_id"].isin(valid_products).all(),
        "Todos los productos de fact_ventas existen en dim_productos.",
    )

    _add_check(
        results,
        "Integridad referencial - fact_ventas.id_tienda",
        fact_ventas["id_tienda"].isin(valid_stores).all(),
        "Todas las tiendas de fact_ventas existen en dim_tiendas.",
    )

    _add_check(
        results,
        "Integridad referencial - fact_inventario.art_id",
        fact_inventario["art_id"].isin(valid_products).all(),
        "Todos los productos de fact_inventario existen en dim_productos.",
    )

    _add_check(
        results,
        "Integridad referencial - fact_devoluciones.id_trans_origen",
        fact_devoluciones["id_trans_origen"].isin(valid_transactions).all(),
        "Todas las devoluciones referencian una venta existente.",
    )


def _validate_business_rules(
    gold_tables: dict[str, pd.DataFrame],
    results: list[dict[str, str]],
) -> None:
    """Valida reglas de negocio principales implementadas en Gold."""
    dim_clientes = gold_tables["dim_clientes"]
    fact_ventas = gold_tables["fact_ventas"]
    fact_inventario = gold_tables["fact_inventario"]
    fact_devoluciones = gold_tables["fact_devoluciones"]
    fact_rfm_clientes = gold_tables["fact_rfm_clientes"]

    _add_check(
        results,
        "Existe cliente anónimo",
        0 in set(dim_clientes["id_miembro"]),
        "dim_clientes contiene el registro id_miembro=0.",
    )

    _add_check(
        results,
        "Venta neta no negativa",
        (fact_ventas["vr_venta_neto"] >= 0).all(),
        "Todos los valores de vr_venta_neto son mayores o iguales a cero.",
    )

    _add_check(
        results,
        "Cobertura de inventario disponible",
        fact_inventario["cobertura_dias"].notna().all(),
        "Todos los registros de inventario tienen cobertura_dias.",
    )

    stock_alert_condition = pd.Series(
        pd.to_numeric(
            fact_inventario.loc[
                fact_inventario["alerta_quiebre"],
                "promedio_consumo_14dias",
            ],
            errors="coerce",
        )
    )

    stock_alert_condition_is_valid = bool(stock_alert_condition.gt(0).all())

    _add_check(
        results,
        "Alerta de quiebre requiere consumo positivo",
        stock_alert_condition_is_valid,
        "Todos los registros con alerta_quiebre tienen consumo 14 días > 0.",
    )

    _add_check(
        results,
        "Tasa de devolución no negativa",
        (fact_devoluciones["tasa_devolucion_articulo"] >= 0).all(),
        "Todos los valores de tasa_devolucion_articulo son >= 0.",
    )

    rfm_scores_are_valid = (
        fact_rfm_clientes["r_score"].between(1, 5).all()
        and fact_rfm_clientes["f_score"].between(1, 5).all()
        and fact_rfm_clientes["m_score"].between(1, 5).all()
    )

    _add_check(
        results,
        "Scores RFM entre 1 y 5",
        rfm_scores_are_valid,
        "r_score, f_score y m_score están dentro del rango esperado.",
    )


def _write_quality_summary(
    results: list[dict[str, str]],
    output_path: Path,
) -> None:
    """Escribe un resumen de validaciones en formato TXT."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_checks = len(results)
    failed_checks = [result for result in results if result["status"] == "FAIL"]
    passed_checks = total_checks - len(failed_checks)

    lines = [
        "RetailMax Medallion Data Pipeline - Resumen de calidad",
        "=" * 65,
        f"Total de validaciones: {total_checks}",
        f"Validaciones exitosas: {passed_checks}",
        f"Validaciones fallidas: {len(failed_checks)}",
        "",
        "Detalle de validaciones:",
        "-" * 65,
    ]

    for result in results:
        lines.append(
            f"[{result['status']}] {result['check_name']} - {result['detail']}"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_quality_checks(config: dict) -> None:
    """Ejecuta validaciones de calidad sobre Bronze, Silver y Gold."""
    bronze_path = Path(config["paths"]["bronze"])
    silver_path = Path(config["paths"]["silver"])
    gold_path = Path(config["paths"]["gold"])

    results: list[dict[str, str]] = []

    _validate_bronze_files(bronze_path, results)
    _validate_silver_files(silver_path, results)
    _validate_gold_files(gold_path, results)

    gold_tables = {
        table_name: _read_gold_table(gold_path, table_name)
        for table_name in GOLD_TABLES
    }

    _validate_gold_row_counts(gold_tables, results)
    _validate_referential_integrity(gold_tables, results)
    _validate_business_rules(gold_tables, results)

    summary_path = Path("docs/evidence/quality_checks_summary.txt")
    _write_quality_summary(results, summary_path)

    failed_checks = [result for result in results if result["status"] == "FAIL"]

    print("Validaciones de calidad ejecutadas.")
    print(f"Total validaciones: {len(results)}")
    print(f"Validaciones exitosas: {len(results) - len(failed_checks)}")
    print(f"Validaciones fallidas: {len(failed_checks)}")
    print(f"Resumen generado en: {summary_path}")

    if failed_checks:
        failed_names = [result["check_name"] for result in failed_checks]
        raise ValueError(
            "Una o más validaciones de calidad fallaron: " + ", ".join(failed_names)
        )
