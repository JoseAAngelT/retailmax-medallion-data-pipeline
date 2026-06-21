from datetime import datetime
from pathlib import Path

import pandas as pd


def generate_pipeline_error_report() -> None:
    """Genera una muestra de errores controlados del pipeline."""
    output_path = Path("docs/evidence/pipeline_errors.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    errors = [
        {
            "error_id": 1,
            "execution_time": execution_time,
            "layer": "Silver",
            "table_name": "TRANS_VENTAS",
            "record_id": "sample-1001",
            "error_type": "INVALID_CUSTOMER",
            "description": "id_miembro no existe en CRM_MIEMBROS.",
            "expected_handling": "Asignar cliente anónimo o registrar rechazo.",
        },
        {
            "error_id": 2,
            "execution_time": execution_time,
            "layer": "Silver",
            "table_name": "TRANS_VENTAS",
            "record_id": "sample-1002",
            "error_type": "DUPLICATED_TRANSACTION",
            "description": "Transacción duplicada exacta.",
            "expected_handling": "Eliminar duplicados o registrar en tabla de errores.",
        },
        {
            "error_id": 3,
            "execution_time": execution_time,
            "layer": "Bronze",
            "table_name": "TRANS_VENTAS",
            "record_id": "sample-1003",
            "error_type": "OUT_OF_RANGE_DATE",
            "description": "Fecha fuera del periodo esperado.",
            "expected_handling": "Detectar en validaciones y revisar la fuente.",
        },
        {
            "error_id": 4,
            "execution_time": execution_time,
            "layer": "Gold",
            "table_name": "fact_ventas",
            "record_id": "sample-1004",
            "error_type": "NEGATIVE_NET_SALE",
            "description": "Venta neta menor a cero.",
            "expected_handling": "Bloquear publicación de Gold hasta corregir la regla.",
        },
    ]

    error_report = pd.DataFrame(errors)
    error_report.to_csv(output_path, index=False, encoding="utf-8")

    print("Reporte de errores del pipeline generado correctamente.")
    print(f"Archivo generado en: {output_path}")


if __name__ == "__main__":
    generate_pipeline_error_report()
