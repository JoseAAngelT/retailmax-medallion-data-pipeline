from pathlib import Path

import yaml


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Carga la configuración del proyecto desde un archivo YAML."""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ensure_directories(config: dict) -> None:
    """Crea los directorios requeridos del proyecto si no existen."""
    for layer in ["bronze", "silver", "gold"]:
        Path(config["paths"][layer]).mkdir(parents=True, exist_ok=True)


def save_csv(df, path: str) -> None:
    """Guarda un DataFrame como CSV sin índice."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def save_parquet(df, path: str) -> None:
    """Guarda un DataFrame como Parquet sin índice."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)