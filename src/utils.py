from pathlib import Path

import pandas as pd
import yaml


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Carga la configuración del proyecto desde un archivo YAML."""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ensure_directories(config: dict) -> None:
    """Crea los directorios requeridos para las capas Medallion."""
    for layer in ["bronze", "silver", "gold"]:
        Path(config["paths"][layer]).mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Guarda un DataFrame en formato CSV sin incluir el índice."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def save_parquet(df: pd.DataFrame, path: str | Path) -> None:
    """Guarda un DataFrame en formato Parquet sin incluir el índice."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
