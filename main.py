from src.generate_data import generate_bronze_data
from src.utils import load_config, ensure_directories


def main() -> None:
    """Ejecuta el pipeline Medallion para el proyecto RetailMax."""
    config = load_config()
    ensure_directories(config)

    print("Iniciando RetailMax Medallion Data Pipeline...")

    print("\nPaso 1: Generando datos sintéticos en capa Bronce...")
    generate_bronze_data(config)

    print("\nPipeline completado exitosamente.")


if __name__ == "__main__":
    main()