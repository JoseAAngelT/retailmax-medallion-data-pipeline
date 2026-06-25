# Configuracion de Azure

Este documento resume los recursos de Azure usados en el proyecto RetailMax y la forma en que el pipeline publica salidas Gold y evidencias en Azure Blob Storage.

---

## 1. Recursos principales

| Recurso                 | Nombre                       | Region  | Uso                                           |
| ----------------------- | ---------------------------- | ------- | --------------------------------------------- |
| Resource Group          | `rg-retailmax-data-pipeline` | East US | Agrupar recursos principales del proyecto.    |
| Storage Account         | `retailmaxlakeja`            | East US | Almacenar salidas analiticas y evidencias.    |
| Container               | `bronze`                     | East US | Contenedor previsto para capa Bronze.         |
| Container               | `silver`                     | East US | Contenedor previsto para capa Silver.         |
| Container               | `gold`                       | East US | Salidas analiticas Gold en Parquet.           |
| Container               | `evidence`                   | East US | Evidencias operativas del proyecto.           |
| Key Vault               | definido por Bicep           | East US | Recurso base para gestion futura de secretos. |
| Log Analytics Workspace | definido por Bicep           | East US | Recurso base para monitoreo.                  |
| Action Group            | definido por Bicep           | East US | Recurso base para alertas.                    |

---

## 2. Configuracion del Storage Account

| Configuracion                        | Valor         |
| ------------------------------------ | ------------- |
| Tipo de cuenta                       | StorageV2     |
| Rendimiento                          | Standard      |
| Replicacion                          | LRS           |
| Nivel de acceso                      | Hot           |
| Acceso anonimo al blob               | Deshabilitado |
| Transferencia segura                 | Habilitada    |
| TLS minimo                           | 1.2           |
| Eliminacion temporal de blobs        | Habilitada    |
| Eliminacion temporal de contenedores | Habilitada    |

---

## 3. Contenedores usados

El proyecto contempla cuatro contenedores principales:

```text
bronze
silver
gold
evidence
```

Uso actual:

| Contenedor | Uso actual                                                       |
| ---------- | ---------------------------------------------------------------- |
| `bronze`   | Contenedor previsto para evolucionar la capa Bronze hacia cloud. |
| `silver`   | Contenedor previsto para evolucionar la capa Silver hacia cloud. |
| `gold`     | Recibe salidas Gold en formato Parquet desde el pipeline.        |
| `evidence` | Recibe evidencias, reportes, manifiestos, summaries y capturas.  |

En la version actual, la carga automatizada del pipeline publica principalmente:

```text
data/gold/*.parquet              -> gold
docs/evidence/*.txt/.csv/.png    -> evidence
```

---

## 4. Carga automatizada a Azure Blob Storage

La carga a Azure se implemento en:

```text
src/upload_to_azure.py
```

Este modulo:

* lee salidas Gold desde `data/gold/`;
* lee evidencias desde `docs/evidence/`;
* sube archivos Parquet al contenedor `gold`;
* sube archivos `.txt`, `.csv` y `.png` al contenedor `evidence`;
* genera un manifiesto de carga;
* genera un resumen operativo de la carga.

Evidencias generadas:

```text
docs/evidence/azure_upload_manifest.csv
docs/evidence/azure_upload_summary.txt
```

Ejemplo de resultados de la ultima ejecucion:

```text
total_files_uploaded: 40
gold_files_uploaded: 9
evidence_files_uploaded: 31
```

---

## 5. Integracion con Airflow

La carga a Azure esta integrada al DAG principal de Airflow mediante la tarea:

```text
upload_outputs_to_azure
```

Esta tarea se ejecuta despues de la notificacion local y antes del cierre de estado del pipeline:

```text
generate_pipeline_notification
  -> upload_outputs_to_azure
  -> register_pipeline_end
```

El DAG completo se encuentra en:

```text
orchestration/dags/retailmax_medallion_dag.py
```

---

## 6. Variable de conexion

La autenticacion con Azure Blob Storage se realiza mediante la variable de entorno:

```text
AZURE_STORAGE_CONNECTION_STRING
```

Para ejecucion local en PowerShell:

```powershell
$env:AZURE_STORAGE_CONNECTION_STRING="<connection-string>"
```

Para ejecucion con Airflow en Docker, se configura en:

```text
orchestration/.env
```

Ejemplo:

```env
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
```

El archivo `.env` no debe subirse al repositorio.

La referencia se pasa al contenedor desde:

```text
orchestration/docker-compose.yaml
```

mediante:

```yaml
AZURE_STORAGE_CONNECTION_STRING: ${AZURE_STORAGE_CONNECTION_STRING}
```

---

## 7. Seguridad

Controles aplicados:

* no se versiona `AZURE_STORAGE_CONNECTION_STRING`;
* no se escribe la connection string en README, documentacion, capturas ni commits;
* `orchestration/.env` esta ignorado por Git;
* `orchestration/.env.example` solo debe contener nombres de variables, no secretos reales;
* los contenedores se manejan como privados;
* el acceso anonimo al blob esta deshabilitado;
* se evita imprimir la connection string completa en consola;
* las evidencias generadas no deben contener claves ni tokens.

Validacion recomendada antes de commits:

```powershell
git status --ignored
```

Busqueda preventiva de secretos:

```powershell
Antes de cada commit se recomienda revisar que no existan secretos reales en archivos versionados.
```

---

## 8. Infraestructura como Codigo

Ademas de la configuracion inicial desde Azure Portal, se agrego una base de Infraestructura como Codigo con Bicep.

Archivos:

```text
infra/main.bicep
infra/parameters.dev.json
infra/README.md
```

Recursos contemplados:

* Storage Account;
* contenedores `bronze`, `silver`, `gold` y `evidence`;
* Key Vault;
* Log Analytics Workspace;
* Action Group.

Comando de despliegue de referencia:

```powershell
az deployment group create `
  --resource-group rg-retailmax-data-pipeline `
  --template-file infra/main.bicep `
  --parameters infra/parameters.dev.json
```

---

## 9. Evidencias

Evidencias relacionadas con Azure:

```text
docs/evidence/azure_upload_manifest.csv
docs/evidence/azure_upload_summary.txt
docs/evidence/azure_bicep_deployment_resources.png
```

---

## 10. Limitaciones actuales

* La publicacion a Azure se realiza con connection string local, no con Managed Identity.
* Key Vault fue creado como recurso base, pero no esta integrado al runtime del pipeline.
* Los contenedores `bronze` y `silver` estan contemplados, pero la carga automatizada actual publica Gold y evidencias.
* No se implementaron politicas RBAC reales por rol dentro del alcance actual.
* No se configuraron alertas reales en Azure Monitor.
* La infraestructura Bicep es una base funcional, no una plataforma productiva multiambiente.
