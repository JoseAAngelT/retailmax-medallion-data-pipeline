from src.generate_data import generate_bronze_data
from src.gold_transform import run_gold_transformations
from src.quality_checks import run_quality_checks
from src.silver_transform import run_silver_transformations
from src.utils import ensure_directories, load_config


def main() -> None:
    """Ejecuta el pipeline Medallion de RetailMax de extremo a extremo."""
    config = load_config()
    ensure_directories(config)

    print("Iniciando RetailMax Medallion Data Pipeline...")

    print("\nPaso 1: Generando datos sintéticos en capa Bronze...")
    generate_bronze_data(config)

    print("\nPaso 2: Transformando datos hacia capa Silver...")
    run_silver_transformations(config)

    print("\nPaso 3: Construyendo modelo dimensional en capa Gold...")
    run_gold_transformations(config)

    print("\nPaso 4: Ejecutando validaciones de calidad...")
    run_quality_checks(config)

    print("\nPipeline completado exitosamente.")


if __name__ == "__main__":
    main()
