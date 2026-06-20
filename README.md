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

| Tecnología         | Uso                                               |
| ------------------ | ------------------------------------------------- |
| Python             | Desarrollo del pipeline                           |
| Pandas             | Transformación y modelado de datos                |
| NumPy              | Generación de datos sintéticos                    |
| Faker              | Generación de datos ficticios                     |
| PyArrow            | Escritura de archivos Parquet                     |
| YAML               | Configuración del proyecto                        |
| Azure Blob Storage | Almacenamiento cloud de evidencias y salidas Gold |
| Git                | Control de versiones                              |

---

## 3. Arquitectura

El proyecto sigue una arquitectura Medallion:

```text
Bronze → Silver → Gold → Quality Checks
```

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
│   ├── azure_setup.md
│   └── evidence/
├── src/
│   ├── generate_data.py
│   ├── silver_transform.py
│   ├── gold_transform.py
│   ├── quality_checks.py
│   ├── cloud_upload.py
│   └── utils.py
├── main.py
├── requirements.txt
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

## 10. Cómo ejecutar

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

El pipeline ejecuta:

```text
Bronze → Silver → Gold → Quality Checks
```

Salida esperada:

```text
Pipeline completado exitosamente.
Validaciones exitosas: 47
Validaciones fallidas: 0
```

---

## 11. Supuestos y limitaciones

Los datos son sintéticos y se generan con una semilla fija para reproducibilidad.

El margen de producto se estima por categoría porque las fuentes no incluyen costo unitario.

La tasa de conversión real no se calcula porque el caso no incluye una fuente de visitas, sesiones web o tráfico en tienda. Como alternativa, se calculan métricas disponibles desde ventas, como transacciones, ventas netas, ticket promedio y canal de venta.

La orquestación se realiza localmente con `main.py`. En un escenario productivo, esta parte podría migrarse a Azure Data Factory.

La infraestructura de Azure se creó desde el portal. Como mejora futura, podría definirse con Bicep o Terraform.

---

## 12. Próximos pasos

Algunas mejoras posibles:

* automatizar la carga a Azure Blob Storage desde Python;
* orquestar el pipeline con Azure Data Factory;
* definir infraestructura como código;
* incorporar una fuente de visitas para calcular conversión real;
* crear un dashboard en Power BI;
* agregar pruebas unitarias;
* particionar archivos Parquet por fecha o dominio.
