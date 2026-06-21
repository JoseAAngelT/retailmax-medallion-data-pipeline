# Infraestructura

Este proyecto utiliza Azure como plataforma cloud.

Para esta versión, los recursos se crearon desde Azure Portal por simplicidad y tiempo. La configuración quedó documentada para dejar claro qué recursos se usaron y cómo se podrían llevar a Infraestructura como Código en una mejora posterior.

## Recursos creados

| Recurso | Nombre | Región | Propósito |
|---|---|---|---|
| Resource Group | `rg-retailmax-data-pipeline` | East US | Agrupar los recursos del proyecto. |
| Storage Account | `retailmaxlakeja` | East US | Almacenar evidencias y salidas analíticas. |
| Container | `bronze` | East US | Capa de datos crudos. |
| Container | `silver` | East US | Capa de datos limpios. |
| Container | `gold` | East US | Capa analítica final. |
| Container | `evidence` | East US | Evidencias de ejecución y calidad. |

## Configuración aplicada

| Elemento | Valor |
|---|---|
| Tipo de cuenta | StorageV2 |
| Rendimiento | Standard |
| Replicación | LRS |
| Nivel de acceso | Hot |
| Acceso anónimo | Deshabilitado |
| TLS mínimo | 1.2 |
| Transferencia segura | Habilitada |

## Seguridad

No se incluyen claves, cadenas de conexión ni contraseñas en el repositorio.

La conexión a PostgreSQL local se realiza mediante variables de entorno:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"

## Evidencia de despliegue

El template Bicep fue desplegado correctamente en el Resource Group `rg-retailmax-data-pipeline-dev`.

Recursos creados:

- Storage Account: `retailmaxlakejadev`
- Containers: `bronze`, `silver`, `gold`, `evidence`
- Key Vault: `kv-retailmax-ja-dev`
- Log Analytics Workspace: `log-retailmax-dev`
- Action Group: `ag-retailmax-dev`

La evidencia visual se encuentra en `docs/evidence/`.

Nota: el archivo `parameters.dev.json` usa un correo de ejemplo para no exponer correos personales en el repositorio.