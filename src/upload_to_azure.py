import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from azure.storage.blob import BlobServiceClient

from src.utils import load_config

GOLD_CONTAINER = "gold"
EVIDENCE_CONTAINER = "evidence"

EVIDENCE_EXTENSIONS = {".txt", ".csv", ".png"}


def _get_blob_service_client() -> BlobServiceClient:
    """Construye el cliente de Azure Blob Storage desde variables de entorno."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not connection_string:
        raise ValueError(
            "La variable AZURE_STORAGE_CONNECTION_STRING no está configurada."
        )

    return BlobServiceClient.from_connection_string(connection_string)


def _upload_file(
    blob_service_client: BlobServiceClient,
    container_name: str,
    local_file_path: Path,
    blob_name: str,
) -> dict:
    """Sube un archivo local a Azure Blob Storage."""
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name,
    )

    with local_file_path.open("rb") as file:
        blob_client.upload_blob(file, overwrite=True)

    return {
        "upload_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "container_name": container_name,
        "blob_name": blob_name,
        "local_file_path": str(local_file_path),
        "file_size_mb": round(local_file_path.stat().st_size / (1024 * 1024), 4),
        "status": "uploaded",
    }


def _upload_gold_outputs(
    blob_service_client: BlobServiceClient,
    gold_path: Path,
) -> list[dict]:
    """Sube salidas Gold Parquet al contenedor gold."""
    uploaded_files = []

    if not gold_path.exists():
        return uploaded_files

    for file_path in sorted(gold_path.glob("*.parquet")):
        blob_name = file_path.name

        uploaded_files.append(
            _upload_file(
                blob_service_client=blob_service_client,
                container_name=GOLD_CONTAINER,
                local_file_path=file_path,
                blob_name=blob_name,
            )
        )

    return uploaded_files


def _upload_evidence_outputs(
    blob_service_client: BlobServiceClient,
    evidence_path: Path,
) -> list[dict]:
    """Sube evidencias operativas al contenedor evidence."""
    uploaded_files = []

    if not evidence_path.exists():
        return uploaded_files

    for file_path in sorted(evidence_path.iterdir()):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in EVIDENCE_EXTENSIONS:
            continue

        blob_name = file_path.name

        uploaded_files.append(
            _upload_file(
                blob_service_client=blob_service_client,
                container_name=EVIDENCE_CONTAINER,
                local_file_path=file_path,
                blob_name=blob_name,
            )
        )

    return uploaded_files


def upload_outputs_to_azure(config: dict) -> None:
    """Sube salidas Gold y evidencias del pipeline a Azure Blob Storage."""
    gold_path = Path(config["paths"]["gold"])
    evidence_path = Path(config.get("paths", {}).get("evidence", "docs/evidence"))

    blob_service_client = _get_blob_service_client()

    uploaded_files = []
    uploaded_files.extend(
        _upload_gold_outputs(
            blob_service_client=blob_service_client,
            gold_path=gold_path,
        )
    )
    uploaded_files.extend(
        _upload_evidence_outputs(
            blob_service_client=blob_service_client,
            evidence_path=evidence_path,
        )
    )

    manifest_path = evidence_path / "azure_upload_manifest.csv"
    summary_path = evidence_path / "azure_upload_summary.txt"

    manifest_df = pd.DataFrame(uploaded_files)
    manifest_df.to_csv(manifest_path, index=False)

    total_uploaded = len(uploaded_files)
    gold_uploaded = sum(
        1 for file in uploaded_files if file["container_name"] == GOLD_CONTAINER
    )
    evidence_uploaded = sum(
        1 for file in uploaded_files if file["container_name"] == EVIDENCE_CONTAINER
    )

    lines = [
        "RetailMax - Azure upload summary",
        "=" * 60,
        f"execution_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "storage_account: retailmaxlakeja",
        "",
        "Upload summary:",
        "-" * 60,
        f"total_files_uploaded: {total_uploaded}",
        f"gold_files_uploaded: {gold_uploaded}",
        f"evidence_files_uploaded: {evidence_uploaded}",
        "",
        "Containers:",
        "-" * 60,
        f"gold_container: {GOLD_CONTAINER}",
        f"evidence_container: {EVIDENCE_CONTAINER}",
        "",
        "Output files:",
        "-" * 60,
        f"manifest: {manifest_path}",
        f"summary: {summary_path}",
    ]

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print("Carga a Azure Blob Storage completada correctamente.")
    print(f"Archivos subidos: {total_uploaded}")
    print(f"Resumen generado en: {summary_path}")
    print(f"Manifiesto generado en: {manifest_path}")


if __name__ == "__main__":
    project_config = load_config()
    upload_outputs_to_azure(project_config)
