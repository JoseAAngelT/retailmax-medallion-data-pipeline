from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from src.utils import save_csv

# Semillas para reproducibilidad.
SEED = 42
fake = Faker("es_MX")
Faker.seed(SEED)
np.random.seed(SEED)


# Catálogos sintéticos.
COUNTRIES = ["Colombia", "Mexico", "Chile", "Peru", "Ecuador"]
STORE_TYPES = ["hypermarket", "supermarket", "convenience_store", "ecommerce"]
SALES_CHANNELS = ["physical_store", "ecommerce", "marketplace"]
PAYMENT_TYPES = ["cash", "credit_card", "debit_card", "digital_wallet"]
GENDERS = ["M", "F", "No informado", None]
AGE_GROUPS = ["18-25", "26-35", "36-45", "46-60", "60+", None]

CATEGORY_LVL1 = [
    "Alimentos y bebidas",
    "Cuidado personal e higiene",
    "Hogar y limpieza",
    "Electronica y tecnologia",
    "Ropa y calzado",
    "Bebes y maternidad",
]

RETURN_REASONS = {
    "DAMAGED": "Producto dañado",
    "WRONG_ITEM": "Producto incorrecto",
    "LATE_DELIVERY": "Entrega tardía",
    "NO_LONGER_NEEDED": "Arrepentimiento del cliente",
    "QUALITY_ISSUE": "Problema de calidad",
    "OTHER": "Otro motivo",
}

def _random_dates(size: int, start_date: str, end_date: str) -> list:
    """Genera una lista de fechas aleatorias en formato YYYY-MM-DD."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta_days = (end - start).days
    
    return [
        (start + timedelta(days=int(np.random.randint(0, delta_days)))).date() 
        for _ in range(size)
    ]


def _random_times(size: int) -> list:
    """Genera una lista de horas aleatorias en formato HH:MM:SS."""
    return [
        f"{np.random.randint(8, 22):02d}:{np.random.randint(0, 60):02d}:00"
        for _ in range(size)
    ]


def generate_proveedores(n: int) -> pd.DataFrame:
    """Genera datos sintéticos para la tabla MSTR_PROVEEDORES."""
    data = {
        "id_proveedor": range(1, n + 1),
        "razon_social": [fake.company() for _ in range(n)],
        "pais_origen": np.random.choice(COUNTRIES, n),
        "tiempo_repo_dias": np.random.randint(1, 15, n),
        "calificacion_calidad": np.round(np.random.uniform(2.5, 5.0, n), 2),
        "activo": np.random.choice([True, False], n, p=[0.95, 0.05]),
    }

    return pd.DataFrame(data)


def generate_articulos(n: int, proveedores: pd.DataFrame) -> pd.DataFrame:
    """Genera datos sintéticos para la tabla MSTR_ARTICULOS."""
    category_lvl1 = np.random.choice(CATEGORY_LVL1, n)

    data = {
        "art_id": range(1, n + 1),
        "cod_barra": [fake.ean13() for _ in range(n)],
        "desc_art": [f"{fake.word().capitalize()} {fake.word()}" for _ in range(n)],
        "id_categ_n1": category_lvl1,
        "id_categ_n2": [
            f"{category} - Subcategoria {np.random.randint(1, 6)}"
            for category in category_lvl1
        ],
        "id_categ_n3": [
            f"Linea {np.random.randint(1, 11)}" for _ in range(n)
        ],
        "id_proveedor": np.random.choice(proveedores["id_proveedor"], n),
        "precio_lista": np.round(np.random.uniform(10, 5000, n), 2),
        "peso_kg": np.round(np.random.uniform(0.1, 20, n), 2),
        "unidad_medida": np.random.choice([True, False], n, p=[0.97, 0.03]),
        "activo": np.random.choice([True, False], n, p=[0.97, 0.03]),
        "fec_alta": _random_dates(n, "2021-01-01", "2024-12-31"),
    }

    return pd.DataFrame(data)


def generate_tiendas(n: int) -> pd.DataFrame:
    """Genera datos sintéticos para la tabla MSTR_TIENDAS."""
    data = {
        "id_tienda": range(1, n + 1),
        "nom_tienda": [f"RetailMax {fake.city()}" for _ in range(n)],
        "tipo_tienda": np.random.choice(STORE_TYPES, n),
        "id_ciudad": [fake.city() for _ in range(n)],
        "id_pais": np.random.choice(COUNTRIES, n),
        "metros_cuadrados": np.random.randint(100, 10000, n),
        "activo": np.random.choice([True, False], n, p=[0.95, 0.05]),
        "fec_apertura": _random_dates(n, "2010-01-01", "2024-12-31"),
        }
    
    return pd.DataFrame(data)


def generate_miembros(n: int, tiendas: pd.DataFrame,) -> pd.DataFrame:
    """Genera datos sintéticos para la tabla CRM_MIEMBROS."""
    data = {
        "id_miembro": range(1, n + 1),
        "fec_registro": _random_dates(n, "2020-01-01", "2025-05-31"),
        "id_ciudad": np.random.choice(tiendas["id_ciudad"], n),
        "genero": np.random.choice(GENDERS, n, p=[0.46, 0.46, 0.06, 0.02]),
        "rango_edad": np.random.choice(AGE_GROUPS, n, p=[0.18, 0.25, 0.22, 0.18, 0.12, 0.05]),
        "canal_pref": np.random.choice(SALES_CHANNELS, n),
        "activo": np.random.choice([True, False], n, p=[0.92, 0.08]),
        "fec_ultima_compra": _random_dates(n, "2024-01-01", "2025-06-15"),
    }

    return pd.DataFrame(data)


def _generate_member_ids_for_sales(ventas_count: int, miembros: pd.DataFrame, anonymous_rate: float = 0.03,) -> list:
    """Genera una lista de IDs de cliente para ventas, incluyendo un porcentaje de ventas anónimas."""
    member_ids = miembros["id_miembro"].to_numpy()
    selected_members = np.random.choice(member_ids, ventas_count).astype(object)

    # Se simula un porcentaje de ventas anónimas reemplazando algunos IDs de miembros con None.
    anonymous_mask = np.random.random(ventas_count) < anonymous_rate
    selected_members[anonymous_mask] = None

    return selected_members.tolist()


def generate_ventas(n: int, miembros: pd.DataFrame, tiendas: pd.DataFrame, articulos: pd.DataFrame,) -> pd.DataFrame:
    """Genera datos sintéticos para la tabla TRANS_VENTAS."""
    qty = np.random.randint(1, 8, n)
    unit_price = np.round(np.random.uniform(10, 5000, n), 2)
    gross_amount = qty * unit_price
    discount = np.round(gross_amount * np.random.uniform(0, 0.25, n), 2)
    
    data = {
        "id_trans": range(1, n + 1),
        "id_mimebro": _generate_member_ids_for_sales(n, miembros),
        "id_tienda": np.random.choice(tiendas["id_tienda"], n),
        "art_id": np.random.choice(articulos["art_id"], n),
        "fec_trans": _random_dates(n, "2025-01-01", "2025-06-15"),
        "hra_trans": _random_times(n),
        "qty_vendida": qty,
        "precio_unitario_venta": unit_price,
        "descuento_aplicado": discount,
        "tipo_pago": np.random.choice(PAYMENT_TYPES, n),
        "canal_venta": np.random.choice(SALES_CHANNELS, n),
    }

    return pd.DataFrame(data)

def generate_stock(n: int, articulos: pd.DataFrame, tiendas: pd.DataFrame,) -> pd.DataFrame:
    """Genera datos sintéticos para la tabla INV_STOCK_DIARIO."""
    stock_minimo = np.random.randint(5, 80, n)
    stock_maximo = stock_minimo + np.random.randint(50, 500, n)

    data = {
        "id_snapshot": range(1, n + 1),
        "art_id": np.random.choice(articulos["art_id"], n),
        "id_tienda": np.random.choice(tiendas["id_tienda"], n),
        "fec_snapshot": _random_dates(n, "2025-05-01", "2025-06-15"),
        "stock_fisico": np.random.randint(0, 500, n),
        "stock_transito": np.random.randint(0, 200, n),
        "stock_reservado": np.random.randint(0, 100, n),
        "stock_minimo_config": stock_minimo,
        "stock_maximo_config": stock_maximo,                     
    }

    return pd.DataFrame(data)


def generate_devoluciones(n: int, ventas: pd.DataFrame,) -> pd.DataFrame:
    """Genera datos sinteticos para la tabla POST_DEVOLUCIONES."""
    sampled_sales = ventas.sample(n=n, replace=True, random_state=SEED,).reset_index(drop=True)

    data = {
        "id_devolucion": range(1, n + 1),
        "id_trans_origen": sampled_sales["id_trans"],
        "art_id": sampled_sales["art_id"],
        "id_tienda": sampled_sales["id_tienda"],
        "fec_devolucion": _random_dates(n, "2025-01-05", "2025-06-20"),
        "qty_devuelta": np.random.randint(1, 3, n),
        "motivo_cod": np.random.choice(list(RETURN_REASONS.keys()), n),
        "canal_devolucion": np.random.choice(SALES_CHANNELS, n),
        "estado_devolucion": np.random.choice(["approved", "rejected", "pending"], n, p=[0.75, 0.15, 0.10],),
        "vr_reembolso": np.round(np.random.uniform(10, 3000, n), 2),
    }

    return pd.DataFrame(data)


def generate_bronze_data(config: dict) -> None:
    """Genera todas las tablas fuente de la capa Bronze."""
    bronze_path = Path(config["paths"]["bronze"])
    volumes = config["synthetic_data"]

    # Generación de catálogos y entidades base.
    proveedores = generate_proveedores(volumes["proveedores"])
    articulos = generate_articulos(volumes["articulos"], proveedores)
    tiendas = generate_tiendas(volumes["tiendas"])
    miembros = generate_miembros(volumes["miembros"], tiendas)

    # Generación de tablas transaccionales dependientes de las entidades base.
    ventas = generate_ventas(
        volumes["ventas"],
        miembros,
        tiendas,
        articulos,
    )
    stock = generate_stock(volumes["stock"], articulos, tiendas)
    devoluciones = generate_devoluciones(volumes["devoluciones"], ventas)

    save_csv(proveedores, bronze_path / "MSTR_PROVEEDORES.csv")
    save_csv(articulos, bronze_path / "MSTR_ARTICULOS.csv")
    save_csv(tiendas, bronze_path / "MSTR_TIENDAS.csv")
    save_csv(miembros, bronze_path / "CRM_MIEMBROS.csv")
    save_csv(ventas, bronze_path / "TRANS_VENTAS.csv")
    save_csv(stock, bronze_path / "INV_STOCK_DIARIO.csv")
    save_csv(devoluciones, bronze_path / "POST_DEVOLUCIONES.csv")

    print("Datos Bronze generados correctamente.")
    print(f"MSTR_PROVEEDORES: {len(proveedores):,} registros")
    print(f"MSTR_ARTICULOS: {len(articulos):,} registros")
    print(f"MSTR_TIENDAS: {len(tiendas):,} registros")
    print(f"CRM_MIEMBROS: {len(miembros):,} registros")
    print(f"TRANS_VENTAS: {len(ventas):,} registros")
    print(f"INV_STOCK_DIARIO: {len(stock):,} registros")
    print(f"POST_DEVOLUCIONES: {len(devoluciones):,} registros")