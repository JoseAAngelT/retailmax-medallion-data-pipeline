# Gobierno y seguridad

Este documento resume las decisiones de gobierno, seguridad y privacidad consideradas para el proyecto RetailMax.

## Alcance actual

En esta versión se implementaron controles básicos:

- no se guardan contraseñas ni claves en el repositorio;
- la conexión a PostgreSQL usa variables de entorno;
- las capturas de Azure fueron editadas para ocultar información sensible;
- los contenedores de Azure Blob Storage se configuraron con acceso privado;
- el Storage Account tiene acceso anónimo deshabilitado;
- se usa TLS 1.2;
- se genera un hash SHA-256 para el identificador del cliente en Gold.

## Roles propuestos

| Rol | Acceso propuesto | Uso |
|---|---|---|
| Data Engineer | Lectura y escritura en Bronze, Silver y Gold. | Operar y mantener el pipeline. |
| Analyst | Solo lectura en Gold. | Consumir datos para análisis y reportes. |
| Admin | Control total sobre recursos del proyecto. | Administración de infraestructura y permisos. |

## Principio de mínimo privilegio

En una versión productiva, cada componente debería usar una identidad separada:

| Componente | Identidad sugerida | Permisos |
|---|---|---|
| Pipeline de ingesta | Service principal de ingesta | Escritura en Bronze. |
| Pipeline de transformación | Service principal de procesamiento | Lectura en Bronze/Silver y escritura en Silver/Gold. |
| Usuarios analistas | Grupo de analistas | Lectura solo en Gold. |

## Datos sensibles

| Campo | Tabla | Tratamiento |
|---|---|---|
| `id_miembro` | `CRM_MIEMBROS`, `TRANS_VENTAS`, `dim_clientes`, `fact_ventas` | Se conserva para integridad, pero se genera `id_miembro_hash` en Gold. |
| `id_miembro_hash` | `dim_clientes` | Hash SHA-256 estable. |
| `genero` | `dim_clientes` | Se estandariza a `M`, `F` o `No informado`. |
| `rango_edad` | `dim_clientes` | Se imputa cuando viene nulo. |

## Secretos

No se incluyen secretos en el código.

Para PostgreSQL local, las credenciales se configuran en la sesión de PowerShell:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"