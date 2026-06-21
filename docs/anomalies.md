# Anomalías consideradas

Este documento resume algunos casos anómalos que podrían aparecer en una fuente real de ventas.

El pipeline principal genera datos válidos para mantener una ejecución estable. Aun así, se documentan ejemplos de anomalías que deberían detectarse o tratarse en una versión productiva.

| Anomalía | Tabla | Descripción | Manejo esperado |
|---|---|---|---|
| Transacción duplicada | `TRANS_VENTAS` | Registro repetido con la misma información de venta. | Eliminar duplicados en Silver o registrarlo en una tabla de errores. |
| Cliente inválido | `TRANS_VENTAS` | Venta con `id_miembro` que no existe en `CRM_MIEMBROS`. | Asignar cliente anónimo o registrar el rechazo, según la regla definida. |
| Fecha fuera de rango | `TRANS_VENTAS` | Venta con fecha fuera del periodo esperado. | Detectarla en validaciones de calidad y registrar el motivo. |
| Venta neta negativa | `fact_ventas` | Resultado de una regla incorrecta de descuento o precio. | Bloquear la publicación de Gold hasta corregir la regla. |

## Evidencia

La muestra inicial de anomalías se encuentra en:

```text
docs/evidence/sample_anomalies.csv