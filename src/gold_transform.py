from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from src.utils import save_parquet

CATEGORY_MARGIN_MAP = {
    "Alimentos y bebidas": 0.18,
    "Cuidado personal e higiene": 0.25,
    "Hogar y limpieza": 0.22,
    "Electronica y tecnologia": 0.15,
    "Ropa y calzado": 0.35,
    "Bebes y maternidad": 0.20,
}


RFM_SEGMENT_MAP = {
    "R5-F5-M5": "Champions",
    "R5-F4-M5": "Champions",
    "R4-F5-M5": "Champions",
    "R5-F5-M4": "Champions",
}


def _read_silver_table(silver_path: Path, table_name: str) -> pd.DataFrame:
    """Lee una tabla Parquet desde la capa Silver."""
    file_path = silver_path / f"{table_name}.parquet"
    return pd.read_parquet(file_path)


def _safe_qcut(series: pd.Series, ascending: bool = True) -> pd.Series:
    """Asigna scores de 1 a 5 usando quantiles de forma tolerante a duplicados."""
    ranked_series = series.rank(method="first", ascending=ascending)

    try:
        scores = pd.qcut(
            ranked_series,
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates="drop",
        )
        return scores.astype(int)
    except ValueError:
        return pd.Series(3, index=series.index)


def build_dim_productos(
    articulos: pd.DataFrame,
    proveedores: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la dimensión de productos desde articulos y proveedores."""
    dim_productos = articulos.merge(
        proveedores[
            [
                "id_proveedor",
                "razon_social",
                "pais_origen",
                "tiempo_repo_dias",
                "calificacion_calidad",
            ]
        ],
        on="id_proveedor",
        how="left",
    )

    dim_productos["margen_estimado_pct"] = dim_productos["id_categ_n1"].map(
        CATEGORY_MARGIN_MAP
    )
    dim_productos["margen_estimado_pct"] = dim_productos["margen_estimado_pct"].fillna(
        0.20
    )

    dim_productos["margen_estimado_valor"] = (
        dim_productos["precio_lista"] * dim_productos["margen_estimado_pct"]
    )

    dim_productos = dim_productos.rename(
        columns={
            "id_categ_n1": "categoria_n1",
            "id_categ_n2": "categoria_n2",
            "id_categ_n3": "categoria_n3",
            "razon_social": "proveedor",
        }
    )

    selected_columns = [
        "art_id",
        "cod_barra",
        "desc_art",
        "categoria_n1",
        "categoria_n2",
        "categoria_n3",
        "id_proveedor",
        "proveedor",
        "pais_origen",
        "tiempo_repo_dias",
        "calificacion_calidad",
        "precio_lista",
        "margen_estimado_pct",
        "margen_estimado_valor",
        "peso_kg",
        "unid_medida",
        "activo",
        "fec_alta",
    ]

    dim_productos = cast(
        pd.DataFrame,
        dim_productos.loc[:, selected_columns],
    )

    return dim_productos


def build_dim_tiendas(tiendas: pd.DataFrame) -> pd.DataFrame:
    """Construye la dimensión de tiendas."""
    dim_tiendas = tiendas.copy()

    selected_columns = [
        "id_tienda",
        "nom_tienda",
        "tipo_tienda",
        "id_ciudad",
        "id_pais",
        "zona_distribucion_asignada",
        "metros_cuadrados",
        "activo",
        "fec_apertura",
    ]

    dim_tiendas = cast(
        pd.DataFrame,
        dim_tiendas.loc[:, selected_columns],
    )

    return dim_tiendas


def build_dim_clientes(miembros: pd.DataFrame) -> pd.DataFrame:
    """Constuye la dimension de clientes e incluye cliente anónimo."""
    dim_clientes = miembros.copy()

    dim_clientes["id_miembro_hash"] = dim_clientes["id_miembro"].astype(str).apply(hash)

    selected_columns = [
        "id_miembro",
        "id_miembro_hash",
        "fec_registro",
        "id_ciudad",
        "genero",
        "rango_edad",
        "canal_pref",
        "activo",
        "fec_ultima_compra",
        "antiguedad_dias",
    ]

    dim_clientes = dim_clientes[selected_columns]

    anonymous_customer = pd.DataFrame(
        [
            {
                "id_miembro": 0,
                "id_miembro_hash": 0,
                "fec_registro": pd.NaT,
                "id_ciudad": "No informado",
                "genero": "No informado",
                "rango_edad": "No informado",
                "canal_pref": "No informado",
                "activo": True,
                "fec_ultima_compra": pd.NaT,
                "antiguedad_dias": 0,
            }
        ]
    )

    return pd.concat([anonymous_customer, dim_clientes], ignore_index=True)


def build_fact_ventas(
    ventas: pd.DataFrame,
    dim_clientes: pd.DataFrame,
    dim_productos: pd.DataFrame,
    dim_tiendas: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla de hechos de ventas."""
    valid_customer_ids = set(dim_clientes["id_miembro"])
    valid_product_ids = set(dim_productos["art_id"])
    valid_store_ids = set(dim_tiendas["id_tienda"])

    fact_ventas = ventas.copy()

    fact_ventas["id_miembro"] = np.where(
        fact_ventas["id_miembro"].isin(valid_customer_ids),
        fact_ventas["id_miembro"],
        0,
    )

    fact_ventas = fact_ventas[
        fact_ventas["art_id"].isin(valid_product_ids)
        & fact_ventas["id_tienda"].isin(valid_store_ids)
    ]

    selected_columns = [
        "id_trans",
        "id_miembro",
        "id_tienda",
        "art_id",
        "fec_trans",
        "hra_trans",
        "qty_vendida",
        "precio_unitario_venta",
        "descuento_aplicado",
        "venta_bruta",
        "vr_venta_neto",
        "ind_venta_descuento",
        "tipo_pago",
        "canal_venta",
    ]

    return fact_ventas[selected_columns]


def _calculate_avg_consumption_14d(fact_ventas: pd.DataFrame) -> pd.DataFrame:
    """Calcula el consumo promedio diario de los últimos 14 días por artículo y tienda."""
    max_sale_date = fact_ventas["fec_trans"].max()
    start_date = max_sale_date - pd.Timedelta(days=14)

    recent_sales = fact_ventas[
        (fact_ventas["fec_trans"] > start_date)
        & (fact_ventas["fec_trans"] <= max_sale_date)
    ]

    consumption = recent_sales.groupby(["art_id", "id_tienda"], as_index=False).agg(
        total_qty_14d=("qty_vendida", "sum")
    )

    consumption["promedio_consumo_14dias"] = consumption["total_qty_14d"] / 14

    return consumption[["art_id", "id_tienda", "promedio_consumo_14dias"]]


def build_fact_inventario(
    stock: pd.DataFrame,
    fact_ventas: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla de hechos de inventario con alerta de quiebre."""
    fact_inventario = stock.copy()
    avg_consumption = _calculate_avg_consumption_14d(fact_ventas)

    fact_inventario = fact_inventario.merge(
        avg_consumption, on=["art_id", "id_tienda"], how="left"
    )

    fact_inventario["promedio_consumo_14dias"] = fact_inventario[
        "promedio_consumo_14dias"
    ].fillna(0)

    fact_inventario["cobertura_dias"] = np.where(
        fact_inventario["promedio_consumo_14dias"] > 0,
        fact_inventario["stock_fisico"] / fact_inventario["promedio_consumo_14dias"],
        np.inf,
    )

    fact_inventario["diferencia_stock_minimo"] = (
        fact_inventario["stock_fisico"] - fact_inventario["stock_minimo_config"]
    )

    fact_inventario["alerta_quiebre"] = (fact_inventario["cobertura_dias"] < 7) & (
        fact_inventario["promedio_consumo_14dias"] > 0
    )

    selected_columns = [
        "id_snapshot",
        "art_id",
        "id_tienda",
        "fec_snapshot",
        "stock_fisico",
        "stock_transito",
        "stock_reservado",
        "stock_minimo_config",
        "stock_maximo_config",
        "promedio_consumo_14dias",
        "cobertura_dias",
        "diferencia_stock_minimo",
        "alerta_quiebre",
    ]

    fact_inventario = cast(pd.DataFrame, fact_inventario.loc[:, selected_columns])

    return fact_inventario


def build_fact_devoluciones(
    devoluciones: pd.DataFrame,
    fact_ventas: pd.DataFrame,
    dim_productos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla de hechos de devoluciones."""
    ventas_lookup_columns = [
        "id_trans",
        "precio_unitario_venta",
        "qty_vendida",
        "vr_venta_neto",
        "canal_venta",
    ]

    ventas_lookup = cast(
        pd.DataFrame,
        fact_ventas.loc[:, ventas_lookup_columns],
    )

    ventas_lookup = ventas_lookup.rename(columns={"id_trans": "id_trans_origen"})

    product_lookup = dim_productos[
        ["art_id", "categoria_n1", "categoria_n2", "categoria_n3"]
    ]

    fact_devoluciones = devoluciones.merge(
        ventas_lookup,
        on="id_trans_origen",
        how="left",
    )

    fact_devoluciones = fact_devoluciones.merge(
        product_lookup,
        on="art_id",
        how="left",
    )

    sold_units = fact_ventas.groupby("art_id", as_index=False).agg(
        unidades_vendidas=("qty_vendida", "sum")
    )

    returned_units = fact_devoluciones.groupby("art_id", as_index=False).agg(
        unidades_devueltas=("qty_devuelta", "sum")
    )

    return_rate = sold_units.merge(returned_units, on="art_id", how="left")
    return_rate["unidades_devueltas"] = return_rate["unidades_devueltas"].fillna(0)

    return_rate["tasa_devolucion_articulo"] = np.where(
        return_rate["unidades_vendidas"] > 0,
        return_rate["unidades_devueltas"] / return_rate["unidades_vendidas"],
        0,
    )

    fact_devoluciones = fact_devoluciones.merge(
        return_rate[["art_id", "tasa_devolucion_articulo"]],
        on="art_id",
        how="left",
    )

    selected_columns = [
        "id_devolucion",
        "id_trans_origen",
        "art_id",
        "id_tienda",
        "fec_devolucion",
        "qty_devuelta",
        "motivo_cod",
        "motivo_desc",
        "canal_devolucion",
        "estado_devolucion",
        "vr_reembolso",
        "precio_unitario_venta",
        "vr_venta_neto",
        "canal_venta",
        "categoria_n1",
        "categoria_n2",
        "categoria_n3",
        "tasa_devolucion_articulo",
    ]

    fact_devoluciones = cast(
        pd.DataFrame,
        fact_devoluciones.loc[:, selected_columns],
    )

    return fact_devoluciones


def build_fact_rfm_clientes(
    fact_ventas: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Construye la tabla RFM de clientes activos."""
    rfm_window_days = config["business_rules"]["rfm_window_days"]
    active_window_days = config["business_rules"]["active_customer_window_days"]

    customer_sales = fact_ventas[fact_ventas["id_miembro"] != 0].copy()
    reference_date = customer_sales["fec_trans"].max()

    active_start_date = reference_date - pd.Timedelta(days=active_window_days)
    rfm_start_date = reference_date - pd.Timedelta(days=rfm_window_days)

    active_customers = customer_sales[customer_sales["fec_trans"] >= active_start_date][
        "id_miembro"
    ].unique()

    rfm_sales = customer_sales[
        (customer_sales["id_miembro"].isin(active_customers))
        & (customer_sales["fec_trans"] >= rfm_start_date)
    ]

    fact_rfm = rfm_sales.groupby("id_miembro", as_index=False).agg(
        ultima_transaccion=("fec_trans", "max"),
        frecuencia_90d=("id_trans", "nunique"),
        valor_monetario_90d=("vr_venta_neto", "sum"),
    )

    fact_rfm["recencia_dias"] = (
        reference_date - fact_rfm["ultima_transaccion"]
    ).dt.days

    # En recencia, menor número de dias representa mejor comportamiento.
    fact_rfm["r_score"] = _safe_qcut(
        fact_rfm["recencia_dias"],
        ascending=False,
    )
    fact_rfm["f_score"] = _safe_qcut(
        fact_rfm["frecuencia_90d"],
        ascending=True,
    )
    fact_rfm["m_score"] = _safe_qcut(
        fact_rfm["valor_monetario_90d"],
        ascending=True,
    )

    fact_rfm["segmento_rfm"] = (
        "R"
        + fact_rfm["r_score"].astype(str)
        + "-F"
        + fact_rfm["f_score"].astype(str)
        + "-M"
        + fact_rfm["m_score"].astype(str)
    )

    fact_rfm["segmento_valor"] = fact_rfm["segmento_rfm"].map(RFM_SEGMENT_MAP)
    fact_rfm["segmento_valor"] = fact_rfm["segmento_valor"].fillna("Segmento regular")

    selected_columns = [
        "id_miembro",
        "ultima_transaccion",
        "recencia_dias",
        "frecuencia_90d",
        "valor_monetario_90d",
        "r_score",
        "f_score",
        "m_score",
        "segmento_rfm",
        "segmento_valor",
    ]

    return fact_rfm[selected_columns]


def build_kpi_ventas_diarias(
    fact_ventas: pd.DataFrame,
    dim_tiendas: pd.DataFrame,
    dim_productos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye KPIs diarios de ventas para dashboard ejecutivo."""
    sales = fact_ventas.merge(
        dim_tiendas[["id_tienda", "id_pais"]],
        on="id_tienda",
        how="left",
    )

    sales = sales.merge(
        dim_productos[["art_id", "categoria_n1"]],
        on="art_id",
        how="left",
    )

    kpi = sales.groupby(
        ["fec_trans", "id_pais", "canal_venta", "categoria_n1"],
        as_index=False,
    ).agg(
        ventas_netas=("vr_venta_neto", "sum"),
        unidades_vendidas=("qty_vendida", "sum"),
        transacciones=("id_trans", "nunique"),
        descuento_total=("descuento_aplicado", "sum"),
        venta_bruta=("venta_bruta", "sum"),
    )

    kpi["ticket_promedio"] = np.where(
        kpi["transacciones"] > 0,
        kpi["ventas_netas"] / kpi["transacciones"],
        0,
    )

    kpi["tasa_descuento_promedio"] = np.where(
        kpi["venta_bruta"] > 0,
        kpi["descuento_total"] / kpi["venta_bruta"],
        0,
    )

    comparison = kpi[
        [
            "fec_trans",
            "id_pais",
            "canal_venta",
            "categoria_n1",
            "ventas_netas",
        ]
    ].copy()

    comparison["fec_trans"] = comparison["fec_trans"] + pd.Timedelta(days=7)
    comparison["ventas_netas_semana_anterior"] = comparison["ventas_netas"]
    comparison = comparison.drop(columns=["ventas_netas"])

    kpi = kpi.merge(
        comparison,
        on=["fec_trans", "id_pais", "canal_venta", "categoria_n1"],
        how="left",
    )

    kpi["ventas_netas_semana_anterior"] = kpi["ventas_netas_semana_anterior"].fillna(0)

    kpi["variacion_vs_semana_anterior"] = np.where(
        kpi["ventas_netas_semana_anterior"] > 0,
        (kpi["ventas_netas"] - kpi["ventas_netas_semana_anterior"])
        / kpi["ventas_netas_semana_anterior"],
        0,
    )

    return kpi


def build_kpi_top_articulos_categoria(
    fact_ventas: pd.DataFrame,
    dim_productos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye el top 10 de articulos por categoria."""
    sales = fact_ventas.merge(
        dim_productos[["art_id", "desc_art", "categoria_n1"]],
        on="art_id",
        how="left",
    )

    article_sales = sales.groupby(
        ["categoria_n1", "art_id", "desc_art"], as_index=False
    ).agg(
        ventas_netas=("vr_venta_neto", "sum"),
        unidades_vendidas=("qty_vendida", "sum"),
        transacciones=("id_trans", "nunique"),
    )

    article_sales["ranking_categoria"] = article_sales.groupby("categoria_n1")[
        "ventas_netas"
    ].rank(method="first", ascending=False)

    top_articles = cast(
        pd.DataFrame,
        article_sales.loc[article_sales["ranking_categoria"] <= 10, :],
    )
    top_articles = cast(
        pd.DataFrame,
        top_articles.sort_values(
            by=["categoria_n1", "ranking_categoria"],
            ascending=[True, True],
        ),
    )

    return top_articles


def run_gold_transformations(config: dict) -> None:
    """Ejecuta las transformaciones de Silver hacia Gold."""
    silver_path = Path(config["paths"]["silver"])
    gold_path = Path(config["paths"]["gold"])

    proveedores = _read_silver_table(silver_path, "MSTR_PROVEEDORES")
    articulos = _read_silver_table(silver_path, "MSTR_ARTICULOS")
    tiendas = _read_silver_table(silver_path, "MSTR_TIENDAS")
    miembros = _read_silver_table(silver_path, "CRM_MIEMBROS")
    ventas = _read_silver_table(silver_path, "TRANS_VENTAS")
    stock = _read_silver_table(silver_path, "INV_STOCK_DIARIO")
    devoluciones = _read_silver_table(silver_path, "POST_DEVOLUCIONES")

    dim_productos = build_dim_productos(articulos, proveedores)
    dim_tiendas = build_dim_tiendas(tiendas)
    dim_clientes = build_dim_clientes(miembros)

    fact_ventas = build_fact_ventas(
        ventas,
        dim_clientes,
        dim_productos,
        dim_tiendas,
    )
    fact_inventario = build_fact_inventario(stock, fact_ventas)
    fact_devoluciones = build_fact_devoluciones(
        devoluciones,
        fact_ventas,
        dim_productos,
    )
    fact_rfm_clientes = build_fact_rfm_clientes(fact_ventas, config)

    kpi_ventas_diarias = build_kpi_ventas_diarias(
        fact_ventas,
        dim_tiendas,
        dim_productos,
    )
    kpi_top_articulos_categoria = build_kpi_top_articulos_categoria(
        fact_ventas,
        dim_productos,
    )

    save_parquet(dim_productos, gold_path / "dim_productos.parquet")
    save_parquet(dim_tiendas, gold_path / "dim_tiendas.parquet")
    save_parquet(dim_clientes, gold_path / "dim_clientes.parquet")
    save_parquet(fact_ventas, gold_path / "fact_ventas.parquet")
    save_parquet(fact_inventario, gold_path / "fact_inventario.parquet")
    save_parquet(fact_devoluciones, gold_path / "fact_devoluciones.parquet")
    save_parquet(fact_rfm_clientes, gold_path / "fact_rfm_clientes.parquet")
    save_parquet(kpi_ventas_diarias, gold_path / "kpi_ventas_diarias.parquet")
    save_parquet(
        kpi_top_articulos_categoria,
        gold_path / "kpi_top_articulos_categoria.parquet",
    )

    print("Datos Gold generados correctamente.")
    print(f"dim_productos: {len(dim_productos):,} registros")
    print(f"dim_tiendas: {len(dim_tiendas):,} registros")
    print(f"dim_clientes: {len(dim_clientes):,} registros")
    print(f"fact_ventas: {len(fact_ventas):,} registros")
    print(f"fact_inventario: {len(fact_inventario):,} registros")
    print(f"fact_devoluciones: {len(fact_devoluciones):,} registros")
    print(f"fact_rfm_clientes: {len(fact_rfm_clientes):,} registros")
    print(f"kpi_ventas_diarias: {len(kpi_ventas_diarias):,} registros")
    print(
        f"kpi_top_articulos_categoria: {len(kpi_top_articulos_categoria):,} registros"
    )
