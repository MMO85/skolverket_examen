from __future__ import annotations

import json
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_plotly_events import plotly_events

# ------------------------------------------------------------
# App setup
# ------------------------------------------------------------
st.set_page_config(page_title="Skolverket – karta", layout="wide")

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
DB_PATH = ROOT_DIR / "csv_ingestion_pipeline.duckdb"
GEO_KOMMUN_PARQUET = APP_DIR / "geo" / "processed" / "kommuner.parquet"

DEFAULT_CENTER = {"lat": 62.0, "lon": 15.0}
DEFAULT_ZOOM = 3.6

# ------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------
def get_con(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=read_only)

def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

@st.cache_data(show_spinner=False)
def load_df(sql: str) -> pd.DataFrame:
    with get_con(read_only=True) as con:
        return con.execute(sql).df()

@st.cache_data(show_spinner=False)
def distinct_vals(table: str, col: str) -> list:
    df = load_df(f'SELECT DISTINCT "{col}" AS v FROM {table} WHERE "{col}" IS NOT NULL ORDER BY 1')
    return df["v"].tolist()

# ------------------------------------------------------------
# Geo helpers (cache + simplify)
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_kommun_geo_base() -> gpd.GeoDataFrame:
    if not GEO_KOMMUN_PARQUET.exists():
        raise FileNotFoundError(f"Geo parquet saknas: {GEO_KOMMUN_PARQUET}")

    gdf = gpd.read_parquet(GEO_KOMMUN_PARQUET)

    required = {"kommun", "kommun_kod", "geometry"}
    missing = required - set(gdf.columns)
    if missing:
        raise ValueError(f"kommuner.parquet saknar kolumner: {missing}. Har: {list(gdf.columns)}")

    gdf = gdf[["kommun", "kommun_kod", "geometry"]].copy()
    gdf["kommun"] = gdf["kommun"].astype(str).str.strip()
    gdf["kommun_kod"] = gdf["kommun_kod"].astype(str).str.zfill(4)

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    return gdf

@st.cache_data(show_spinner=False)
def load_kommun_geo_simplified(tolerance: float) -> gpd.GeoDataFrame:
    gdf = load_kommun_geo_base().copy()
    # Den här raden gör geometrin lättare/snabbare:
    if tolerance and float(tolerance) > 0:
        gdf["geometry"] = gdf["geometry"].simplify(tolerance=float(tolerance), preserve_topology=True)
    return gdf

@st.cache_data(show_spinner=False)
def geojson_from_geo(tolerance: float) -> dict:
    """
    Cachebar version: vi bygger geojson från geo (inte från merged gdf).
    Då slipper vi att Streamlit försöker hash:a GeoDataFrame som argument.
    """
    gdf = load_kommun_geo_simplified(tolerance)
    return json.loads(gdf.to_json())

# ------------------------------------------------------------
# Plot helpers
# ------------------------------------------------------------
def make_sweden_choropleth(
    gdf_geo: gpd.GeoDataFrame,
    geojson: dict,
    df_values: pd.DataFrame,
    value_col: str,
    title: str,
    center: dict,
    zoom: float,
    key: str,
) -> tuple:
    df = df_values.copy()
    df["kommun_kod"] = df["kommun_kod"].astype(str).str.zfill(4)

    # Plotly behöver bara df + geojson. Geo-dataframe används bara som "template" för locations,
    # men vi kan skicka df direkt.
    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations="kommun_kod",
        featureidkey="properties.kommun_kod",
        color=value_col,
        hover_name="kommun",
        hover_data={"kommun_kod": True, value_col: True},
        mapbox_style="carto-positron",
        center={"lat": center["lat"], "lon": center["lon"]},
        zoom=float(zoom),
        opacity=0.75,
        title=title,
    )

    # Viktigt: fullscreen/fitbounds kan strula i vissa plotly-versioner,
    # så vi kör med fast center+zoom för Sverige.
    fig.update_layout(margin={"r": 0, "t": 55, "l": 0, "b": 0})

    selected = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=560,
        key=key,
    )
    return fig, selected

def bar_top_bottom(df: pd.DataFrame, value_col: str, n: int):
    d = df.dropna(subset=[value_col]).copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    d = d.dropna(subset=[value_col])

    top = d.sort_values(value_col, ascending=False).head(n)
    bot = d.sort_values(value_col, ascending=True).head(n)

    fig_top = px.bar(
        top.sort_values(value_col, ascending=True),
        x=value_col,
        y="kommun",
        orientation="h",
        title=f"Top {n} (högst {value_col})",
        labels={"kommun": "Kommun", value_col: value_col},
    )
    fig_top.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0}, height=520)

    fig_bot = px.bar(
        bot.sort_values(value_col, ascending=False),
        x=value_col,
        y="kommun",
        orientation="h",
        title=f"Bottom {n} (lägst {value_col})",
        labels={"kommun": "Kommun", value_col: value_col},
    )
    fig_bot.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0}, height=520)

    return fig_top, fig_bot

# ------------------------------------------------------------
# Header + checks
# ------------------------------------------------------------
st.title("Skolverket")
st.caption("DuckDB (DLT) + dbt marts + Sverigekarta (kommuner)")

if not DB_PATH.exists():
    st.error(f"Databasen hittas inte: {DB_PATH}. Kör DLT + dbt först.")
    st.stop()

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.header("Inställningar")
    dbt_schema = st.text_input("DBT-schema", value="staging_data")

    page = st.radio("Välj vy", ["Karta (Ranking)", "Karta (Budget per elev)"], index=1)

    st.markdown("---")
    st.caption("Kartutjämning (snabbare/lättare)")
    tolerance = st.slider("Förenkling", 0.0, 0.05, 0.01, 0.005)

# Ladda geo (cachad) + geojson (cachad, baserat på tolerance)
try:
    gdf_geo = load_kommun_geo_simplified(tolerance)
    geojson = geojson_from_geo(tolerance)
except Exception as e:
    st.error(f"Kunde inte läsa geo-data: {e}")
    st.stop()

# ------------------------------------------------------------
# PAGE 1: Ranking
# ------------------------------------------------------------
if page == "Karta (Ranking)":
    st.subheader("Sverigekarta – kommunranking (åk 9)")

    table = f"{dbt_schema}.mart_ranked_kommun_ak9"
    years = distinct_vals(table, "lasar_start")
    if not years:
        st.warning("Inga år hittades i mart_ranked_kommun_ak9.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        year = st.selectbox("Läsår start", years, index=len(years) - 1)
    with c2:
        metric = st.selectbox("Färgskala", ["score_0_100", "avg_total", "avg_gap_f_minus_m"], index=0)

    df_scores = load_df(f"""
        SELECT kommun_kod, kommun, {metric} AS {metric}
        FROM {table}
        WHERE lasar_start = {int(year)}
    """)

    fig, selected = make_sweden_choropleth(
        gdf_geo=gdf_geo,
        geojson=geojson,
        df_values=df_scores,
        value_col=metric,
        title=f"Ranking – {metric} ({year})",
        center=DEFAULT_CENTER,
        zoom=DEFAULT_ZOOM,
        key="map_ranking",
    )
    st.plotly_chart(fig, use_container_width=True)

    if selected:
        kk = str(selected[0].get("location", "")).zfill(4)
        row = df_scores[df_scores["kommun_kod"].astype(str).str.zfill(4) == kk]
        if not row.empty:
            st.info(f"Vald kommun: {row.iloc[0]['kommun']} ({kk})")

# ------------------------------------------------------------
# PAGE 2: Budget per elev (Din huvudvy)
# ------------------------------------------------------------
else:
    st.subheader("Budget per elev (kommuner)")

    budget_table = f"{dbt_schema}.mart_budget_per_elev_kommun"
    years = distinct_vals(budget_table, "lasar_start")
    if not years:
        st.error("Hittar inga år i mart_budget_per_elev_kommun. Har du kört dbt för den modellen?")
        st.stop()

    with st.sidebar:
        st.markdown("---")
        st.header("Filter (Budget)")
        year = st.selectbox("Läsår start", years, index=len(years) - 1)
        n = st.slider("Antal kommuner i jämförelse", 10, 80, 40, 5)

    df_budget = load_df(f"""
        SELECT kommun_kod, kommun, totalt_per_elev
        FROM {budget_table}
        WHERE lasar_start = {int(year)}
    """)

    if df_budget.empty:
        st.warning("Inga rader för valt år.")
        st.stop()

    # 1) EN karta (Sverige) – ingen extra karta längre ner
    fig_map, selected = make_sweden_choropleth(
        gdf_geo=gdf_geo,
        geojson=geojson,
        df_values=df_budget,
        value_col="totalt_per_elev",
        title=f"Budget per elev – {year}",
        center=DEFAULT_CENTER,
        zoom=DEFAULT_ZOOM,
        key="map_budget",
    )
    st.plotly_chart(fig_map, use_container_width=True)

    if selected:
        kk = str(selected[0].get("location", "")).zfill(4)
        row = df_budget[df_budget["kommun_kod"].astype(str).str.zfill(4) == kk]
        if not row.empty:
            kommun = row.iloc[0]["kommun"]
            v = row.iloc[0]["totalt_per_elev"]
            st.success(f"Vald kommun: {kommun} ({kk}) — totalt_per_elev: {v:,.0f}".replace(",", " "))

    # 2) Jämförelse Top/Bottom
    st.markdown("## Jämförelse mellan kommuner")
    fig_top, fig_bot = bar_top_bottom(df_budget, "totalt_per_elev", int(n))

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_top, use_container_width=True)
    with c2:
        st.plotly_chart(fig_bot, use_container_width=True)

    # OBS: medvetet ingen extra karta här.
