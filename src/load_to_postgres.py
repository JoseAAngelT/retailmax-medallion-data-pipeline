import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from src.utils import load_config

SOURCE_TABLES = [
    "MSTR_PROVEEDORES",
    "MSTR_ARTICULOS",
    "MSTR_TIENDAS",
    "CRM_MIEMBROS",
    "TRANS_VENTAS",
    "INV_STOCK_DIARIO",
    "POST_DEVOLUCIONES",
]


def _get_postgres_connection_url() -> URL:
    """Construye la conexión a PostgreSQL desde variables de entorno."""
    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))
    database = os.getenv("PGDATABASE", "retailmax_source")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD")

    if password is None:
        raise ValueError("La variable de entorno PGPASSWORD no está configurada.")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def _validate_bronze_files(bronze_path: Path) -> None:
    """Valida que existan todos los archivos CSV de Bronze antes de cargar."""
    missing_files = [
        str(bronze_path / f"{table_name}.csv")
        for table_name in SOURCE_TABLES
        if not (bronze_path / f"{table_name}.csv").exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "No se encontraron los siguientes archivos Bronze:\n"
            + "\n".join(missing_files)
        )


def load_bronze_to_postgres(config: dict) -> None:
    """Carga las tablas Bronze CSV a PostgreSQL y genera evidencia de conteos."""
    bronze_path = Path(config["paths"]["bronze"])
    _validate_bronze_files(bronze_path)

    connection_url = _get_postgres_connection_url()
    engine = create_engine(connection_url)

    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    counts: list[dict[str, int | str]] = []

    with engine.begin() as connection:
        for source_table_name in SOURCE_TABLES:
            file_path = bronze_path / f"{source_table_name}.csv"
            sql_table_name = source_table_name.lower()

            df = pd.read_csv(file_path)

            df.to_sql(
                sql_table_name,
                connection,
                if_exists="replace",
                index=False,
            )

            count_query = f"SELECT COUNT(*) AS total FROM {sql_table_name};"
            result = pd.read_sql_query(count_query, connection)
            row_count = int(result["total"].iloc[0])

            counts.append(
                {
                    "source_table": source_table_name,
                    "postgres_table": sql_table_name,
                    "row_count": row_count,
                }
            )

    summary_path = Path("docs/evidence/postgres_counts_summary.txt")
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "RetailMax - Evidencia de carga PostgreSQL",
        "=" * 50,
        f"execution_time: {execution_time}",
        "database: retailmax_source",
        "load_mode: replace",
        "",
        "Resultados SELECT COUNT(*) por tabla:",
        "-" * 50,
    ]

    for result in counts:
        lines.append(
            f"{result['postgres_table']}: {result['row_count']:,} "
            f"(source: {result['source_table']})"
        )

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print("Carga PostgreSQL completada correctamente.")
    print(f"Tablas cargadas: {len(SOURCE_TABLES)}")
    print(f"Resumen generado en: {summary_path}")


if __name__ == "__main__":
    project_config = load_config()
    load_bronze_to_postgres(project_config)
