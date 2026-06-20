from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import save_parquet

RETURN_REASONS = {
    "DAMAGED": "Producto dañado",
    "WRONG_ITEM": "Producto incorrecto",
    "LATE_DELIVERY": "Entrega tardía",
    "NO_LONGER_NEEDED": "Arrepentimiento del cliente",
    "QUALITY_ISSUE": "Problema de calidad",
    "OTHER": "Otro motivo",
}


def _read_bronze_table(bronze_path: Path, table_name: str) -> pd.DataFrame:
    """Lee una tabla CSV desde la capa Bronze."""
    file_path = bronze_path / f"{table_name}.csv"
    return pd.read_csv(file_path)


def _standardize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza columnas de texto eliminando espacios laterales."""
    text_columns = df.select_dtypes(include=["object"]).columns

    for column in text_columns:
        df[column] = df[column].apply(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    return df


def _convert_date_columns(
    df: pd.DataFrame,
    date_columns: list[str],
) -> pd.DataFrame:
    for column in date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    return df


def _to_numeric_series(
    df: pd.DataFrame,
    column: str,
    fill_value: float = 0,
) -> pd.Series:
    """Convierte una columna a númerica y remplaza nulos."""
    numeric_values = pd.Series(
        pd.to_numeric(df[column], errors="coerce"),
        index=df.index,
    )

    return numeric_values.fillna(fill_value)


def _age_range_to_midpoint(age_range: object) -> float:
    """Convierte un rango de edad a un valor numérico representativo"""
    mapping: dict[str, float] = {
        "18-25": 21.5,
        "26-35": 30.5,
        "36-45": 40.5,
        "46-60": 53.0,
        "60+": 65.0,
    }

    if not isinstance(age_range, str):
        return float("nan")

    return mapping.get(age_range, float("nan"))


def _midpoint_to_age_range(value: float) -> str:
    """Convierte una edad aproximada al rango de edad correspondiente."""
    if pd.isna(value):
        return "No informado"

    numeric_value = float(value)

    if numeric_value <= 25:
        return "18-25"
    if numeric_value <= 35:
        return "26-35"
    if numeric_value <= 45:
        return "36-45"
    if numeric_value <= 60:
        return "46-60"

    return "60+"


def transform_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza la tabla MSTR_PROVEEDORES."""
    df = _standardize_text_columns(df)

    df["pais_origen"] = df["pais_origen"].str.title()
    df["tiempo_repo_dias"] = _to_numeric_series(df, "tiempo_repo_dias")
    df["calificacion_calidad"] = _to_numeric_series(
        df,
        "calificacion_calidad",
    )
    df["activo"] = df["activo"].astype(bool)

    return df


def transform_articulos(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza la tabla MSTR_ARTICULOS."""
    df = _standardize_text_columns(df)
    df = _convert_date_columns(df, ["fec_alta"])

    df["precio_lista"] = _to_numeric_series(df, "precio_lista")
    df["peso_kg"] = _to_numeric_series(df, "peso_kg")
    df["activo"] = df["activo"].astype(bool)

    return df


def transform_tiendas(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza la tabla MSTR_TIENDAS."""
    df = _standardize_text_columns(df)
    df = _convert_date_columns(df, ["fec_apertura"])

    store_type_map = {
        "hypermarket": "Hipermercado",
        "supermarket": "Supermercado",
        "convenience_store": "Tienda de conveniencia",
        "ecommerce": "E-commerce",
    }

    distribution_zone_map = {
        "Colombia": "Bogotá",
        "México": "CDMX",
        "Chile": "Santiago",
        "Peru": "Lima",
        "Ecuador": "Quito",
    }

    df["tipo_tienda"] = df["tipo_tienda"].map(store_type_map)
    df["tipo_tienda"] = df["tipo_tienda"].fillna("No clasificado")
    df["id_pais"] = df["id_pais"].str.title()

    # Transformación clave: zona de distribución asignada.
    df["zona_distribucion_asignada"] = df["id_pais"].map(distribution_zone_map)
    df["zona_distribucion_asignada"] = df["zona_distribucion_asignada"].fillna(
        "Zona no clasificada"
    )

    df["activo"] = df["activo"].astype(bool)

    return df


def transform_miembros(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza la tabla CRM _MIEMBROS."""
    df = _standardize_text_columns(df)
    df = _convert_date_columns(df, ["fec_registro", "fec_ultima_compra"])

    # Transformación clave: estandarizar género a M, F o No informado.
    df["genero"] = df["genero"].fillna("No informado")
    df["genero"] = df["genero"].replace(
        {
            "m": "M",
            "f": "F",
            "": "No informado",
        }
    )
    df["genero"] = np.where(
        df["genero"].isin(["M", "F"]),
        df["genero"],
        "No informado",
    )

    # Transformación clave: se imputa rango_edad nulo usando el valor más frecuente por canal.
    rango_edad_num = pd.Series(
        df["rango_edad"].apply(_age_range_to_midpoint),
        index=df.index,
    )

    median_by_channel = rango_edad_num.groupby(df["canal_pref"]).transform("median")
    global_median = rango_edad_num.median()

    rango_edad_num = rango_edad_num.fillna(median_by_channel)
    rango_edad_num = rango_edad_num.fillna(global_median)

    df["rango_edad"] = rango_edad_num.apply(_midpoint_to_age_range)

    # Transformación clave: Calcular antiguedad en dias desde fec_registro.
    reference_date = df["fec_ultima_compra"].max()
    df["antiguedad_dias"] = (reference_date - df["fec_registro"]).dt.days.clip(lower=0)

    df["activo"] = df["activo"].astype(bool)

    return df


def transform_ventas(
    df: pd.DataFrame,
    miembros: pd.DataFrame,
) -> pd.DataFrame:
    """Limpia y valida la tabla TRANS_VENTAS."""
    df = _standardize_text_columns(df)
    df = _convert_date_columns(df, ["fec_trans"])

    numeric_columns = [
        "qty_vendida",
        "precio_unitario_venta",
        "descuento_aplicado",
    ]

    for column in numeric_columns:
        df[column] = _to_numeric_series(df, column)

    valid_members = set(miembros["id_miembro"].dropna().astype(int))

    # Transformación clave: validar id_miembro contra dim_clientes o asignar cliente anonimo.
    df["id_miembro"] = _to_numeric_series(df, "id_miembro")
    df["id_miembro"] = np.where(
        df["id_miembro"].isin(valid_members),
        df["id_miembro"],
        0,
    )
    df["id_miembro"] = df["id_miembro"].astype(int)

    df["venta_bruta"] = df["qty_vendida"] * df["precio_unitario_venta"]
    df["vr_venta_neto"] = df["venta_bruta"] - df["descuento_aplicado"]
    df["vr_venta_neto"] = df["vr_venta_neto"].clip(lower=0)
    df["ind_venta_descuento"] = df["descuento_aplicado"] > 0

    return df


def transform_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y estandariza la tabla INV_STOCK_DIARIO."""
    df = _standardize_text_columns(df)
    df = _convert_date_columns(df, ["fec_snapshot"])

    stock_columns = [
        "stock_fisico",
        "stock_transito",
        "stock_reservado",
        "stock_minimo_config",
        "stock_maximo_config",
    ]

    for column in stock_columns:
        df[column] = _to_numeric_series(df, column).clip(lower=0)

    return df


def transform_devoluciones(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y enriquece la tabla POST_DEVOLUCIONES."""
    df = _standardize_text_columns(df)
    df = _convert_date_columns(df, ["fec_devolucion"])

    df["motivo_desc"] = df["motivo_cod"].map(RETURN_REASONS)
    df["motivo_desc"] = df["motivo_desc"].fillna("Motivo no clasificado")

    df["qty_devuelta"] = _to_numeric_series(
        df,
        "qty_devuelta",
    ).clip(lower=0)
    df["vr_reembolso"] = _to_numeric_series(
        df,
        "vr_reembolso",
    ).clip(lower=0)

    return df


def run_silver_transformations(config: dict) -> None:
    """Ejecuta las transformaciones de Bronze hacia Silver"""
    bronze_path = Path(config["paths"]["bronze"])
    silver_path = Path(config["paths"]["silver"])

    proveedores = _read_bronze_table(bronze_path, "MSTR_PROVEEDORES")
    articulos = _read_bronze_table(bronze_path, "MSTR_ARTICULOS")
    tiendas = _read_bronze_table(bronze_path, "MSTR_TIENDAS")
    miembros = _read_bronze_table(bronze_path, "CRM_MIEMBROS")
    ventas = _read_bronze_table(bronze_path, "TRANS_VENTAS")
    stock = _read_bronze_table(bronze_path, "INV_STOCK_DIARIO")
    devoluciones = _read_bronze_table(bronze_path, "POST_DEVOLUCIONES")

    proveedores = transform_proveedores(proveedores)
    articulos = transform_articulos(articulos)
    tiendas = transform_tiendas(tiendas)
    miembros = transform_miembros(miembros)
    ventas = transform_ventas(ventas, miembros)
    stock = transform_stock(stock)
    devoluciones = transform_devoluciones(devoluciones)

    save_parquet(proveedores, silver_path / "MSTR_PROVEEDORES.parquet")
    save_parquet(articulos, silver_path / "MSTR_ARTICULOS.parquet")
    save_parquet(tiendas, silver_path / "MSTR_TIENDAS.parquet")
    save_parquet(miembros, silver_path / "CRM_MIEMBROS.parquet")
    save_parquet(ventas, silver_path / "TRANS_VENTAS.parquet")
    save_parquet(stock, silver_path / "INV_STOCK_DIARIO.parquet")
    save_parquet(devoluciones, silver_path / "POST_DEVOLUCIONES.parquet")

    print("Datos Silver generados correctamente.")
    print(f"MSTR_PROVEEDORES: {len(proveedores):,} registros")
    print(f"MSTR_ARTICULOS: {len(articulos):,} registros")
    print(f"MSTR_TIENDAS: {len(tiendas):,} registros")
    print(f"CRM_MIEMBROS: {len(miembros):,} registros")
    print(f"TRANS_VENTAS: {len(ventas):,} registros")
    print(f"INV_STOCK_DIARIO: {len(stock):,} registros")
    print(f"POST_DEVOLUCIONES: {len(devoluciones):,} registros")
