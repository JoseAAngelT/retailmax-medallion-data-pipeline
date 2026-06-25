import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from src.utils import load_config

SOURCE_TABLES = [
    "mstr_proveedores",
    "mstr_articulos",
    "mstr_tiendas",
    "crm_miembros",
    "trans_ventas",
    "inv_stock_diario",
    "post_devoluciones",
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


def _extract_table_from_postgres(table_name: str, engine: Any) -> pd.DataFrame:
    """Extrae una tabla completa desde PostgreSQL."""
    query = f"SELECT * FROM {table_name};"
    return pd.read_sql_query(query, engine)


def _add_audit_columns(
    df: pd.DataFrame,
    source_system: str,
    batch_id: str,
    ingestion_timestamp: str,
) -> pd.DataFrame:
    """Agrega columnas de auditoría a un DataFrame de Bronze."""
    result = df.copy()

    result["ingestion_timestamp"] = ingestion_timestamp
    result["source_system"] = source_system
    result["batch_id"] = batch_id

    return result


def _get_bronze_ingested_path(config: dict) -> Path:
    """Obtiene la ruta de salida para Bronze ingested."""
    return Path(config.get("paths", {}).get("bronze_ingested", "data/bronze_ingested"))


def _get_evidence_path(config: dict) -> Path:
    """Obtiene la ruta de evidencias del proyecto."""
    evidence_base_path = Path(config.get("paths", {}).get("evidence", "docs/evidence"))
    return evidence_base_path / "bronze_ingestion_log.txt"


def _write_bronze_parquet(
    df: pd.DataFrame,
    table_name: str,
    batch_id: str,
    ingestion_datetime: datetime,
    output_base_path: Path,
) -> Path:
    """Escribe una tabla Bronze en Parquet particionada por fecha de ingesta."""
    output_path = (
        output_base_path
        / table_name
        / f"year={ingestion_datetime.year}"
        / f"month={ingestion_datetime.month:02d}"
        / f"day={ingestion_datetime.day:02d}"
    )
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / f"{table_name}_{batch_id}.parquet"
    df.to_parquet(output_file, index=False)

    return output_file


def ingest_postgres_to_bronze(config: dict) -> None:
    """Ingesta tablas desde PostgreSQL hacia Bronze Parquet con auditoría."""
    start_time = time.time()
    connection_url = _get_postgres_connection_url()
    engine = create_engine(connection_url)

    batch_id = str(uuid.uuid4())
    ingestion_datetime = datetime.now()
    ingestion_timestamp = ingestion_datetime.strftime("%Y-%m-%d %H:%M:%S")

    output_base_path = _get_bronze_ingested_path(config)
    evidence_path = _get_evidence_path(config)

    log_lines = [
        "RetailMax - Bronze ingestion log",
        "=" * 50,
        f"batch_id: {batch_id}",
        "source_system: postgresql_local",
        f"ingestion_timestamp: {ingestion_timestamp}",
        "output_format: parquet",
        "partition_columns: year, month, day",
        "",
        "Tables processed:",
        "-" * 50,
    ]

    total_records = 0

    for table_name in SOURCE_TABLES:
        table_start_time = time.time()

        df = _extract_table_from_postgres(table_name, engine)
        df = _add_audit_columns(
            df=df,
            source_system="postgresql_local",
            batch_id=batch_id,
            ingestion_timestamp=ingestion_timestamp,
        )

        output_file = _write_bronze_parquet(
            df=df,
            table_name=table_name,
            batch_id=batch_id,
            ingestion_datetime=ingestion_datetime,
            output_base_path=output_base_path,
        )

        row_count = len(df)
        total_records += row_count
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        duration_seconds = round(time.time() - table_start_time, 2)

        log_lines.extend(
            [
                f"table: {table_name}",
                f"records_processed: {row_count}",
                f"output_file: {output_file}",
                f"file_size_mb: {file_size_mb:.2f}",
                f"duration_seconds: {duration_seconds}",
                "",
            ]
        )

    total_duration_seconds = round(time.time() - start_time, 2)

    log_lines.extend(
        [
            "Summary",
            "-" * 50,
            f"total_tables: {len(SOURCE_TABLES)}",
            f"total_records_processed: {total_records}",
            f"total_duration_seconds: {total_duration_seconds}",
        ]
    )

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("\n".join(log_lines), encoding="utf-8")

    print("Ingesta PostgreSQL hacia Bronze completada correctamente.")
    print(f"Batch ID: {batch_id}")
    print(f"Tablas procesadas: {len(SOURCE_TABLES)}")
    print(f"Registros procesados: {total_records:,}")
    print(f"Evidencia generada en: {evidence_path}")


if __name__ == "__main__":
    project_config = load_config()
    ingest_postgres_to_bronze(project_config)
