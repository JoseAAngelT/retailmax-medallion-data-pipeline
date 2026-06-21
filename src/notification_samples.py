from datetime import datetime
from pathlib import Path


def generate_notification_samples() -> None:
    """Genera ejemplos de reportes y alertas operativas del pipeline."""
    output_path = Path("docs/evidence")
    output_path.mkdir(parents=True, exist_ok=True)

    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    success_report = f"""RetailMax - Reporte diario de ejecución

Estado: SUCCESS
Fecha de ejecución: {execution_time}

Resumen:
- Bronze: 7 tablas procesadas
- Silver: 7 tablas procesadas
- Gold: 9 tablas generadas
- Validaciones de calidad: 47
- Validaciones fallidas: 0
- Alertas de calidad: 0

Resultado:
El pipeline terminó correctamente y las salidas Gold quedaron disponibles para análisis.
"""

    failure_alert = f"""RetailMax - Alerta de fallo del pipeline

Estado: FAILED
Fecha de fallo: {execution_time}
DAG: retailmax_medallion_pipeline
Tarea: run_quality_checks
Capa afectada: Gold

Mensaje:
Una o más validaciones de calidad fallaron durante la ejecución del pipeline.

Acción sugerida:
Revisar docs/evidence/quality_checks_summary.txt y validar la tabla afectada antes de publicar resultados.
"""

    volume_alert = f"""RetailMax - Alerta de anomalía de volumen

Estado: WARNING
Fecha de detección: {execution_time}
Capa afectada: Bronze
Tabla: TRANS_VENTAS

Mensaje:
El volumen procesado difiere más de 30% respecto al promedio esperado de las últimas ejecuciones.

Volumen actual: 1,000,000
Promedio esperado: 700,000
Diferencia estimada: 42.86%

Acción sugerida:
Validar si el incremento corresponde a una carga real o a una duplicidad en la fuente.
"""

    (output_path / "sample_success_report.txt").write_text(
        success_report,
        encoding="utf-8",
    )
    (output_path / "sample_failure_alert.txt").write_text(
        failure_alert,
        encoding="utf-8",
    )
    (output_path / "sample_volume_anomaly_alert.txt").write_text(
        volume_alert,
        encoding="utf-8",
    )

    print("Ejemplos de notificaciones generados correctamente.")
    print(f"Archivos generados en: {output_path}")


if __name__ == "__main__":
    generate_notification_samples()
