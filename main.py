from src.generate_data import generate_bronze_data
from src.silver_transform import run_silver_transformations
from src.utils import ensure_directories, load_config


def main() -> None:
    """Ejecuta el pipeline Medallion para el proyecto RetailMax."""
    config = load_config()
    ensure_directories(config)

    print("Iniciando RetailMax Medallion Data Pipeline...")

    print("\nPaso 1: Generando datos sintéticos en capa Bronce...")
    generate_bronze_data(config)

    print("\nPaso 2: Transformando datos sintéticos hacia capa Silver...")
    run_silver_transformations(config)

    print("\nPipeline completado exitosamente.")


if __name__ == "__main__":
    main()
