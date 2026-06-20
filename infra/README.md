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