# Infraestructura

Este proyecto utiliza Azure como plataforma cloud.

La infraestructura inicial se creó desde Azure Portal para avanzar rápido con la prueba. Después se agregó una versión mínima de Infraestructura como Código usando Bicep y se desplegó con Azure CLI en un Resource Group de prueba.

## Recursos principales usados en la prueba

| Recurso         | Nombre                       | Región  | Propósito                                      |
| --------------- | ---------------------------- | ------- | ---------------------------------------------- |
| Resource Group  | `rg-retailmax-data-pipeline` | East US | Agrupar los recursos principales del proyecto. |
| Storage Account | `retailmaxlakeja`            | East US | Almacenar evidencias y salidas analíticas.     |
| Container       | `bronze`                     | East US | Capa de datos crudos.                          |
| Container       | `silver`                     | East US | Capa de datos limpios.                         |
| Container       | `gold`                       | East US | Capa analítica final.                          |
| Container       | `evidence`                   | East US | Evidencias de ejecución y calidad.             |

## Configuración aplicada

| Elemento             | Valor         |
| -------------------- | ------------- |
| Tipo de cuenta       | StorageV2     |
| Rendimiento          | Standard      |
| Replicación          | LRS           |
| Nivel de acceso      | Hot           |
| Acceso anónimo       | Deshabilitado |
| TLS mínimo           | 1.2           |
| Transferencia segura | Habilitada    |

## Infraestructura como Código

Se agregó una versión mínima de IaC usando Bicep.

Archivos:

```text
infra/main.bicep
infra/parameters.dev.json
```

El template define:

* Storage Account;
* contenedores `bronze`, `silver`, `gold` y `evidence`;
* Key Vault;
* Log Analytics Workspace;
* Action Group para alertas básicas.

## Despliegue con Azure CLI

Crear Resource Group:

```powershell
az group create `
  --name rg-retailmax-data-pipeline-dev `
  --location eastus
```

Desplegar Bicep:

```powershell
az deployment group create `
  --resource-group rg-retailmax-data-pipeline-dev `
  --template-file infra/main.bicep `
  --parameters infra/parameters.dev.json
```

## Evidencia de despliegue

El template Bicep fue desplegado correctamente en un Resource Group de prueba.

Recursos creados por Bicep:

* Storage Account: `retailmaxlakejadev`
* Containers: `bronze`, `silver`, `gold`, `evidence`
* Key Vault: `kv-retailmax-ja-dev`
* Log Analytics Workspace: `log-retailmax-dev`
* Action Group: `ag-retailmax-dev`

La evidencia visual se encuentra en:

```text
docs/evidence/azure_bicep_deployment_resources.png
```

## Seguridad

No se incluyen claves, cadenas de conexión ni contraseñas en el repositorio.

La conexión a PostgreSQL local se realiza mediante variables de entorno:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

El archivo `parameters.dev.json` usa un correo de ejemplo para evitar exponer correos personales en GitHub.

## Nota

Esta implementación de IaC es una base funcional para la prueba técnica. No incluye una configuración productiva completa con ambientes separados, backend remoto de estado, políticas avanzadas o gestión completa de secretos.
