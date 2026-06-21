# Configuración de Azure

Este documento resume los recursos de Azure usados en el proyecto RetailMax.

## Recursos creados desde Azure Portal

Para la primera versión del proyecto, los recursos se crearon desde Azure Portal.

| Recurso | Nombre | Región | Uso |
|---|---|---|---|
| Resource Group | `rg-retailmax-data-pipeline` | East US | Agrupar recursos principales del proyecto. |
| Storage Account | `retailmaxlakeja` | East US | Almacenar evidencias y salidas analíticas. |
| Container | `bronze` | East US | Capa Bronze. |
| Container | `silver` | East US | Capa Silver. |
| Container | `gold` | East US | Capa Gold. |
| Container | `evidence` | East US | Evidencias del proyecto. |

## Configuración del Storage Account

| Configuración | Valor |
|---|---|
| Tipo de cuenta | StorageV2 |
| Rendimiento | Standard |
| Replicación | LRS |
| Nivel de acceso | Hot |
| Acceso anónimo al blob | Deshabilitado |
| Transferencia segura | Habilitada |
| TLS mínimo | 1.2 |
| Eliminación temporal de blobs | Habilitada |
| Eliminación temporal de contenedores | Habilitada |

## Evidencias cargadas

En el contenedor `evidence` se cargaron archivos de evidencia como:

- resumen de validaciones de calidad;
- reporte de calidad Silver;
- conteos de PostgreSQL;
- evidencias de Airflow;
- evidencias de IaC;
- ejemplos de alertas y reportes operativos.

En el contenedor `gold` se cargaron salidas analíticas en formato Parquet.

## Infraestructura como Código

Además de la creación inicial desde Azure Portal, se agregó una versión mínima de Infraestructura como Código usando Bicep.

Archivos:

```text
infra/main.bicep
infra/parameters.dev.json