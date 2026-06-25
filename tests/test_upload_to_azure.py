import pandas as pd

from src import upload_to_azure


class FakeBlobClient:
    """Cliente falso para simular carga a Azure."""

    def upload_blob(self, file, overwrite):
        """Simula upload_blob sin conectarse a Azure."""
        assert overwrite is True
        assert file.read() is not None


class FakeBlobServiceClient:
    """Servicio falso para simular BlobServiceClient."""

    def get_blob_client(self, container, blob):
        """Devuelve un cliente falso de blob."""
        assert container in {"gold", "evidence"}
        assert blob
        return FakeBlobClient()


def test_upload_outputs_to_azure_generates_manifest(monkeypatch, tmp_path):
    """Valida la generacion de manifest sin conectarse a Azure."""
    gold_path = tmp_path / "gold"
    evidence_path = tmp_path / "evidence"

    gold_path.mkdir(parents=True)
    evidence_path.mkdir(parents=True)

    (gold_path / "fact_ventas.parquet").write_bytes(b"fake parquet content")
    (evidence_path / "quality_checks_summary.txt").write_text(
        "quality ok",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        upload_to_azure,
        "_get_blob_service_client",
        lambda: FakeBlobServiceClient(),
    )

    config = {
        "paths": {
            "gold": str(gold_path),
            "evidence": str(evidence_path),
        }
    }

    upload_to_azure.upload_outputs_to_azure(config)

    manifest_path = evidence_path / "azure_upload_manifest.csv"
    summary_path = evidence_path / "azure_upload_summary.txt"

    assert manifest_path.exists()
    assert summary_path.exists()

    manifest_df = pd.read_csv(manifest_path)

    assert len(manifest_df) == 2
    assert set(manifest_df["container_name"]) == {"gold", "evidence"}
    assert set(manifest_df["status"]) == {"uploaded"}
