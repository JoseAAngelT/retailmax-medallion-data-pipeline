# RetailMax Medallion Data Pipeline

Proyecto desarrollado para el caso de **Retail y Comercio Electrónico**.

El objetivo fue construir un pipeline de datos con arquitectura Medallion, generando datos sintéticos, aplicando transformaciones por capas y creando salidas analíticas para ventas, inventario, devoluciones y clientes.

El pipeline se ejecuta de forma local con Python y guarda evidencia de resultados en Azure Blob Storage.

---

## 1. Escenario elegido

Se trabajó con el escenario de **Retail y Comercio Electrónico**.

Este caso fue seleccionado porque permite cubrir varios conceptos importantes de ingeniería de datos:

* generación de datos sintéticos;
* procesamiento por capas Bronze, Silver y Gold;
* limpieza y transformación de datos;
* construcción de dimensiones y tablas de hechos;
* validación de calidad;
* almacenamiento de resultados en nube.

---

## 2. Tecnologías utilizadas

| Tecnología         | Uso                                                     |
| ------------------ | ------------------------------------------------------- |
| Python             | Desarrollo del pipeline                                 |
| Pandas             | Transformación y modelado de datos                      |
| NumPy              | Generación de datos sintéticos                          |
| Faker              | Generación de datos ficticios                           |
| PyArrow            | Escritura de archivos Parquet                           |
| YAML               | Configuración del proyecto                              |
| PostgreSQL         | Base de datos relacional local usada como fuente origen |
| SQLAlchemy         | Conexión y carga de datos desde Python hacia PostgreSQL |
| psycopg2           | Driver de conexión entre Python y PostgreSQL            |
| Azure Blob Storage | Almacenamiento cloud de evidencias y salidas Gold       |
| Apache Airflow     | Definición del DAG de orquestación                      |
| Git                | Control de versiones                                    |

---

## 3. Arquitectura

El proyecto sigue una arquitectura Medallion:

```text
PostgreSQL / Bronze → Silver → Gold → Quality Checks → Azure
```

Además de generar archivos Bronze en CSV, las tablas fuente se cargan en PostgreSQL local para simular una base relacional origen.

### Bronze

En esta capa se generan las tablas fuente en formato CSV, respetando los nombres y volúmenes mínimos del caso.

Tablas generadas:

```text
MSTR_PROVEEDORES
MSTR_ARTICULOS
MSTR_TIENDAS
CRM_MIEMBROS
TRANS_VENTAS
INV_STOCK_DIARIO
POST_DEVOLUCIONES
```

### Silver

En Silver se limpian y estandarizan los datos.
Las salidas se guardan en formato Parquet.

Principales transformaciones:

* conversión de fechas;
* conversión de columnas numéricas;
* limpieza de textos;
* estandarización de género;
* imputación de rango de edad con la mediana por canal preferido;
* cálculo de antigüedad del cliente;
* validación de clientes en ventas;
* asignación de cliente anónimo;
* cálculo de venta bruta, venta neta e indicador de descuento;
* mapeo de motivos de devolución.

### Gold

En Gold se construye el modelo analítico final.

Tablas generadas:

```text
dim_productos
dim_tiendas
dim_clientes
fact_ventas
fact_inventario
fact_devoluciones
fact_rfm_clientes
kpi_ventas_diarias
kpi_top_articulos_categoria
```

---

## 4. Modelo Gold

### `dim_productos`

Integra información de artículos y proveedores.
Incluye categorías, proveedor, precio de lista y margen estimado.

Como las fuentes no incluyen costo unitario, el margen se calcula usando un supuesto por categoría.

### `dim_tiendas`

Contiene información de tiendas, tipo de tienda, ciudad, país y zona de distribución asignada.

### `dim_clientes`

Contiene información de miembros/clientes.
Incluye género estandarizado, rango de edad imputado, canal preferido, antigüedad y un hash SHA-256 del identificador del cliente.

También se agrega un cliente anónimo con `id_miembro = 0` para mantener la integridad cuando una venta no tiene cliente válido.

### `fact_ventas`

Contiene las ventas procesadas.
Incluye validación de cliente, venta bruta, venta neta e indicador de descuento.

### `fact_inventario`

Contiene información de inventario y calcula:

* consumo promedio de los últimos 14 días;
* cobertura de inventario en días;
* diferencia contra stock mínimo;
* alerta de quiebre cuando la cobertura es menor a 7 días y existe consumo reciente.

### `fact_devoluciones`

Relaciona devoluciones con la venta original.
Incluye motivo de devolución, precio original, categoría del producto y tasa de devolución por artículo.

### `fact_rfm_clientes`

Calcula una segmentación RFM para clientes activos usando:

* recencia;
* frecuencia;
* valor monetario;
* scores de 1 a 5;
* segmento RFM final.

### KPIs

Se generan dos salidas adicionales para análisis ejecutivo:

```text
kpi_ventas_diarias
kpi_top_articulos_categoria
```

Estas tablas permiten analizar ventas netas, unidades, ticket promedio, descuentos y top de productos por categoría.

---

## 5. Volúmenes generados

| Tabla Bronze        | Registros |
| ------------------- | --------: |
| `MSTR_PROVEEDORES`  |       800 |
| `MSTR_ARTICULOS`    |     5,000 |
| `MSTR_TIENDAS`      |       150 |
| `CRM_MIEMBROS`      |    50,000 |
| `TRANS_VENTAS`      | 1,000,000 |
| `INV_STOCK_DIARIO`  |   750,000 |
| `POST_DEVOLUCIONES` |    50,000 |

Resultados principales en Gold:

| Tabla Gold                    | Registros |
| ----------------------------- | --------: |
| `dim_productos`               |     5,000 |
| `dim_tiendas`                 |       150 |
| `dim_clientes`                |    50,001 |
| `fact_ventas`                 | 1,000,000 |
| `fact_inventario`             |   750,000 |
| `fact_devoluciones`           |    50,000 |
| `fact_rfm_clientes`           |    49,999 |
| `kpi_ventas_diarias`          |    14,850 |
| `kpi_top_articulos_categoria` |        60 |

`dim_clientes` tiene 50,001 registros porque incluye el cliente anónimo.

---

## 6. Validaciones de calidad

El pipeline incluye validaciones en `src/quality_checks.py`.

Se validan:

* existencia de archivos Bronze, Silver y Gold;
* volúmenes mínimos;
* conteos esperados;
* integridad entre hechos y dimensiones;
* existencia del cliente anónimo;
* venta neta no negativa;
* cobertura de inventario;
* alerta de quiebre solo con consumo positivo;
* tasa de devolución no negativa;
* scores RFM entre 1 y 5.

Resultado de la última ejecución:

```text
Total validaciones: 47
Validaciones exitosas: 47
Validaciones fallidas: 0
```

El resumen se genera en:

```text
docs/evidence/quality_checks_summary.txt
```

También se genera un reporte básico de calidad de la capa Silver con conteos, duplicados exactos y porcentaje de nulos por columna:

```text
docs/evidence/silver_quality_report.txt
```

---

## 7. Azure

Se creó una cuenta de Azure Blob Storage para almacenar evidencias y salidas analíticas del proyecto.

Recursos creados:

```text
Resource Group: rg-retailmax-data-pipeline
Storage Account: retailmaxlakeja
Región: East US
Replicación: LRS
Nivel de acceso: Hot
Acceso anónimo: Deshabilitado
```

Contenedores:

```text
bronze
silver
gold
evidence
```

En Azure se cargaron:

* el resumen de validaciones en `evidence`;
* los archivos Parquet de Gold en `gold`.

La configuración está documentada en:

```text
docs/azure_setup.md
```

Las capturas de evidencia están en:

```text
docs/evidence/
```

---

## 8. Estructura del proyecto

```text
retailmax-medallion-data-pipeline/
├── config/
│   └── config.yaml
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── docs/
│   ├── anomalies.md
│   ├── architecture.md
│   ├── azure_setup.md
│   ├── data_catalog.md
│   ├── data_lineage.md
│   ├── data_model.md
│   ├── governance_security.md
│   ├── source_er_model.md
│   └── evidence/
├── infra/
│   └── README.md
├── orchestration/
│   ├── README.md
│   └── dags/
│       └── retailmax_medallion_dag.py
├── src/
│   ├── generate_data.py
│   ├── silver_transform.py
│   ├── gold_transform.py
│   ├── quality_checks.py
│   ├── silver_quality_report.py
│   ├── load_to_postgres.py
│   └── utils.py
├── main.py
├── requirements.txt
├── CHANGELOG.md
├── README.md
└── .gitignore
```

La carpeta `data/` no se sube al repositorio porque contiene archivos generados y pesados.

---

## 9. Configuración

Los parámetros principales están en:

```text
config/config.yaml
```

Ahí se definen:

* rutas de Bronze, Silver y Gold;
* volúmenes de datos sintéticos;
* reglas de negocio para inventario y RFM.

---

## 10. Base relacional PostgreSQL

Además de generar archivos CSV en Bronze, las tablas fuente se cargan en una base PostgreSQL local para simular una fuente relacional.

Script utilizado:

```text
src/load_to_postgres.py
```

El script carga las tablas Bronze en PostgreSQL y genera evidencia de conteos por tabla usando consultas `SELECT COUNT(*)`.

La evidencia se encuentra en:

```text
docs/evidence/postgres_counts_summary.txt
```

La conexión no guarda contraseñas en el código. Se usan variables de entorno:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="retailmax_source"
$env:PGUSER="postgres"
$env:PGPASSWORD="<password>"
```

---

## 11. Documentación técnica

El proyecto incluye documentación adicional en la carpeta `docs/`.

| Archivo                       | Descripción                                     |
| ----------------------------- | ----------------------------------------------- |
| `docs/architecture.md`        | Diagrama general de arquitectura Medallion.     |
| `docs/source_er_model.md`     | Diagrama ER de las tablas fuente.               |
| `docs/data_model.md`          | Modelo analítico de la capa Gold.               |
| `docs/data_lineage.md`        | Linaje de campos calculados en Gold.            |
| `docs/data_catalog.md`        | Catálogo básico de tablas y campos sensibles.   |
| `docs/anomalies.md`           | Anomalías consideradas y manejo esperado.       |
| `docs/governance_security.md` | Consideraciones de gobierno y seguridad.        |
| `docs/azure_setup.md`         | Recursos creados en Azure y evidencia asociada. |

---

## 12. Orquestación

La ejecución principal del proyecto sigue siendo local mediante:

```powershell
python main.py
```

Además, se agregó una definición de DAG para Apache Airflow en:

```text
orchestration/dags/retailmax_medallion_dag.py
```

El DAG define el flujo:

```text
Bronze → Silver → Gold → Quality Checks
```

Incluye:

* ejecución diaria a las 02:00;
* dependencias explícitas entre tareas;
* 3 reintentos por tarea;
* backoff exponencial;
* límite de ejecución por tarea.

El DAG se incluye como propuesta de orquestación para un entorno Airflow. No reemplaza la ejecución local, que se mantiene para facilitar la reproducción del proyecto.

---

## 13. Gobierno y seguridad

Se consideraron controles básicos de seguridad y gobierno:

* no se guardan contraseñas ni claves en el repositorio;
* PostgreSQL usa variables de entorno;
* Azure Blob Storage tiene acceso anónimo deshabilitado;
* los contenedores fueron creados con acceso privado;
* se usa hash SHA-256 para anonimizar el identificador de cliente en Gold;
* se documentan roles propuestos para Data Engineer, Analyst y Admin.

La documentación completa está en:

```text
docs/governance_security.md
```

---

## 14. Cómo ejecutar

Crear entorno virtual:

```powershell
python -m venv .venv
```

Activar entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Ejecutar pipeline completo:

```powershell
python main.py
```

Ejecutar reporte de calidad Silver:

```powershell
python -m src.silver_quality_report
```

Cargar datos Bronze a PostgreSQL:

```powershell
python -m src.load_to_postgres
```

Salida esperada del pipeline principal:

```text
Pipeline completado exitosamente.
Validaciones exitosas: 47
Validaciones fallidas: 0
```

---

## 15. Evidencias

Las evidencias se guardan en:

```text
docs/evidence/
```

Incluyen:

* resumen de validaciones de calidad;
* reporte de calidad Silver;
* conteos de tablas cargadas en PostgreSQL;
* muestra de anomalías consideradas;
* capturas de Azure Resource Group;
* capturas de Azure Storage Account;
* capturas de contenedores Azure;
* capturas de archivos Gold cargados;
* capturas de evidencia cargada en Azure.

---

## 16. Supuestos y limitaciones

Los datos son sintéticos y se generan con una semilla fija para reproducibilidad.

El margen de producto se estima por categoría porque las fuentes no incluyen costo unitario.

La tasa de conversión real no se calcula porque el caso no incluye una fuente de visitas, sesiones web o tráfico en tienda. Como alternativa, se calculan métricas disponibles desde ventas, como transacciones, ventas netas, ticket promedio y canal de venta.

La orquestación con Airflow se incluye como definición de DAG, pero no se ejecutó en un entorno Airflow dentro del alcance actual.

La infraestructura de Azure se creó desde el portal. Se documentó en `/infra`, pero no se implementó IaC completo con Bicep o Terraform.

No se configuraron roles reales en Azure ni evidencia de acceso denegado para un perfil Analista. Esa parte queda documentada como diseño propuesto.

---

## 17. Próximos pasos

Algunas mejoras posibles:

* ejecutar el DAG en un entorno Airflow real;
* automatizar la carga a Azure Blob Storage desde Python;
* definir infraestructura como código con Bicep o Terraform;
* agregar Azure Key Vault para secretos;
* agregar Log Analytics y alertas;
* incorporar una fuente de visitas para calcular conversión real;
* crear un dashboard en Power BI;
* agregar pruebas unitarias;
* particionar archivos Parquet por fecha o dominio.
