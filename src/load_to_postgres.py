import os
from pathlib import Path

import pandas as pd
from sqlalchemy import URL, create_engine

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


def load_bronze_to_postgres(config: dict) -> None:
    """Carga las tablas Bronze CSV a PostgreSQL y genera evidencia de conteos."""
    bronze_path = Path(config["paths"]["bronze"])
    connection_url = _get_postgres_connection_url()
    engine = create_engine(connection_url)

    counts: list[dict[str, int]] = []

    with engine.begin() as connection:
        for table_name in SOURCE_TABLES:
            file_path = bronze_path / f"{table_name}.csv"
            df = pd.read_csv(file_path)

            # PostgreSQL maneja mejor nombres de tabla en minúsculas.
            sql_table_name = table_name.lower()

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
                    "table_name": sql_table_name,
                    "row_count": row_count,
                }
            )

    summary_path = Path("docs/evidence/postgres_counts_summary.txt")
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "RetailMax - Evidencia de carga PostgreSQL",
        "=" * 50,
        "Base de datos: retailmax_source",
        "",
        "Resultados SELECT COUNT(*) por tabla:",
        "-" * 50,
    ]

    for result in counts:
        lines.append(f"{result['table_name']}: {result['row_count']:,}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print("Carga PostgreSQL completada correctamente.")
    print(f"Resumen generado en: {summary_path}")


if __name__ == "__main__":
    project_config = load_config()
    load_bronze_to_postgres(project_config)
