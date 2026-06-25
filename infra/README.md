# Infraestructura

Este proyecto utiliza Azure como plataforma cloud para almacenar salidas analíticas y evidencias operativas del pipeline RetailMax.

La infraestructura inicial se creó desde Azure Portal para avanzar rápido con la prueba técnica. Después se agregó una base funcional de Infraestructura como Código usando Bicep y se desplegó con Azure CLI en un Resource Group de prueba.

---

## 1. Recursos principales usados

| Recurso                 | Nombre                       | Región  | Propósito                                       |
| ----------------------- | ---------------------------- | ------- | ----------------------------------------------- |
| Resource Group          | `rg-retailmax-data-pipeline` | East US | Agrupar los recursos principales del proyecto.  |
| Storage Account         | `retailmaxlakeja`            | East US | Almacenar salidas Gold y evidencias operativas. |
| Container               | `bronze`                     | East US | Contenedor previsto para capa Bronze.           |
| Container               | `silver`                     | East US | Contenedor previsto para capa Silver.           |
| Container               | `gold`                       | East US | Salidas analíticas Gold en Parquet.             |
| Container               | `evidence`                   | East US | Evidencias, reportes, manifests y capturas.     |
| Key Vault               | `kv-retailmax-ja-dev`        | East US | Recurso base para gestión futura de secretos.   |
| Log Analytics Workspace | `log-retailmax-dev`          | East US | Recurso base para monitoreo.                    |
| Action Group            | `ag-retailmax-dev`           | East US | Recurso base para alertas.                      |

---

## 2. Configuración aplicada al Storage Account

| Elemento                             | Valor         |
| ------------------------------------ | ------------- |
| Tipo de cuenta                       | StorageV2     |
| Rendimiento                          | Standard      |
| Replicación                          | LRS           |
| Nivel de acceso                      | Hot           |
| Acceso anónimo                       | Deshabilitado |
| TLS mínimo                           | 1.2           |
| Transferencia segura                 | Habilitada    |
| Eliminación temporal de blobs        | Habilitada    |
| Eliminación temporal de contenedores | Habilitada    |

---

## 3. Infraestructura como Código

Se agregó una base de IaC usando Bicep.

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

---

## 4. Despliegue con Azure CLI

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

---

## 5. Recursos creados por Bicep

El template Bicep fue desplegado correctamente en un Resource Group de prueba.

Recursos creados:

* Storage Account: `retailmaxlakejadev`
* Containers: `bronze`, `silver`, `gold`, `evidence`
* Key Vault: `kv-retailmax-ja-dev`
* Log Analytics Workspace: `log-retailmax-dev`
* Action Group: `ag-retailmax-dev`

Evidencia visual:

```text
docs/evidence/azure_bicep_deployment_resources.png
```

---

## 6. Integración con el pipeline

El pipeline publica salidas Gold y evidencias a Azure Blob Storage mediante:

```text
src/upload_to_azure.py
```

La tarea está integrada al DAG de Airflow como:

```text
upload_outputs_to_azure
```

Flujo relacionado:

```text
generate_pipeline_notification
  -> upload_outputs_to_azure
  -> register_pipeline_end
```

Archivos subidos:

```text
data/gold/*.parquet              -> container gold
docs/evidence/*.txt/.csv/.png    -> container evidence
```

Evidencias generadas por la carga:

```text
docs/evidence/azure_upload_manifest.csv
docs/evidence/azure_upload_summary.txt
```

---

## 7. Variables y secretos

No se incluyen claves, cadenas de conexión ni contraseñas en el repositorio.

La conexión a Azure Blob Storage se realiza mediante:

```text
AZURE_STORAGE_CONNECTION_STRING
```

Para ejecución local:

```powershell
$env:AZURE_STORAGE_CONNECTION_STRING="<connection-string>"
```

Para ejecución con Airflow local, se usa:

```text
orchestration/.env
```

Ejemplo:

```env
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
```

El archivo `orchestration/.env` está ignorado por Git y no debe subirse al repositorio.

La conexión a PostgreSQL local también se realiza mediante variables de entorno:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

En Airflow, `PGHOST` debe usar:

```env
PGHOST=host.docker.internal
```

---

## 8. Seguridad

Controles aplicados:

* no se versionan connection strings ni contraseñas;
* `orchestration/.env` está ignorado por Git;
* `.env.example` no contiene secretos reales;
* los contenedores se manejan como privados;
* el acceso anónimo está deshabilitado;
* se evita imprimir secretos completos en consola;
* `parameters.dev.json` usa valores de ejemplo para evitar exponer datos personales;
* las evidencias no deben contener claves, tokens ni connection strings.

Validación recomendada antes de commits:

```powershell
git status --ignored
```

Búsqueda preventiva de secretos:

```powershell
Select-String -Path README.md, docs\*.md, docs\evidence\*.txt, docs\evidence\*.csv, src\*.py, orchestration\*.yaml, orchestration\.env.example, infra\*.json, infra\*.bicep -Pattern "AccountKey=|DefaultEndpointsProtocol|AZURE_STORAGE_CONNECTION_STRING=.*core.windows.net|PGPASSWORD=*real-secret"
```

---

## 9. Evidencias

Evidencias relacionadas con infraestructura y Azure:

```text
docs/evidence/azure_bicep_deployment_resources.png
docs/evidence/azure_upload_manifest.csv
docs/evidence/azure_upload_summary.txt
```

También pueden existir capturas del Storage Account, contenedores o recursos desplegados. Cualquier captura debe ocultar información sensible.

---

## 10. Limitaciones actuales

Esta implementación de IaC es una base funcional para la prueba técnica. No representa una plataforma productiva completa.

Limitaciones actuales:

* no incluye ambientes separados `dev`, `test` y `prod`;
* no usa Managed Identity para la carga a Azure;
* no integra Key Vault directamente al runtime del pipeline;
* no configura alertas reales en Azure Monitor;
* no aplica políticas avanzadas de red o Private Endpoints;
* no implementa RBAC real por rol;
* no usa backend remoto de estado porque Bicep no lo requiere como Terraform;
* los contenedores `bronze` y `silver` están contemplados, pero la carga automatizada actual publica Gold y evidencias.
