import pandas as pd
import json
import geopandas as gpd
import plotly.express as px
from backend.db import load_table
from backend.db import query_df
from backend.charts import chart_behorighet_gender
from pathlib import Path
from config import BASE_DIR

TREND_TABLE = "mart_parent_trend_ak9"
CHOICE_TABLE = "mart_parent_choice_ak1_9"
FAIR_TABLE = "mart_parent_fairness_ak9"

# Load once
trend_df = load_table(TREND_TABLE)
choice_df = load_table(CHOICE_TABLE)
fair_df = load_table(FAIR_TABLE)

# ---------------- Parent Choice LOVs ----------------

# Year LOV (ONLY from parent choice data, safe as strings)
parent_choice_years = ["All"] + sorted(
    choice_df["year"].dropna().astype(int).astype(str).unique().tolist()
)

# Kommun LOV for trend selector (from parent choice data)
#parent_choice_kommun_trend_lov = ["All"] + sorted(
#    choice_df["kommun"].dropna().unique().tolist()
#)

# ---------------- Common LOV helper ----------------

def _lov(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return ["All"]
    vals = df[col].dropna().unique().tolist()
    try:
        vals = sorted(vals)
    except Exception:
        pass
    return ["All"] + vals


# ---------------- Common LOVs (other pages) ----------------

years = _lov(trend_df, "year")
lan_list = _lov(trend_df, "lan")
kommun_list = _lov(trend_df, "kommun")
huvudman_list = _lov(trend_df, "huvudman_typ")
subject_list = _lov(trend_df, "subject")
subject_list = ["All"] + sorted({s for s in subject_list if str(s).strip().lower() != "all"})

# ---------------- Parent Choice state ----------------

parent_choice_year = "All"
parent_choice_lan = "All"
parent_choice_top_n = 10
parent_choice_kommun_trend = "All"

parent_choice_fig_stack = None
parent_choice_fig_trend = None
parent_choice_table = None

# ---------------- Trend state ----------------

trend_kommun_lov = kommun_list[:]

trend_year = "All"
trend_lan = "All"
trend_kommun = "All"
trend_huvudman = "All"
trend_subject = "All"
trend_metric = "score"
trend_fig = None

# ---------------- Fairness state ----------------



fair_year = "All"
fair_lan = "All"
fair_huvudman = "All"
fair_subject = "All"
#fair_metric = "fairness_score"
fair_fig = None
fair_table = None

#----------------Behörighet state ----------------
from backend.db import get_connection

def load_mart_behorighet_national_gender():
    con = get_connection()
    return con.execute("""
        select kon, program, behorighet_pct
        from mart_behorighet_national_gender_2024_25
        order by program, kon
    """).df()


# Figure state
beh_fig = None

def build_behorighet_gender_figure(year: str):
    # اگر بعداً چند سال داشتی، اینجا می‌تونه فیلتر سال بخوره.
    df = query_df("""
        select kon, program, behorighet_pct
        from mart_behorighet_national_gender_2024_25
        order by program, kon
    """)
    return chart_behorighet_gender(df)



# -------------------------
# KARTA: config + state
# -------------------------


# IMPORTANT:
# - BASE_DIR and query_df must already exist in your project (as they do now).
# - This code is meant to live inside backend/data_processing.py

GEO_KOMMUN_PARQUET = BASE_DIR / "app" / "geo" / "processed" / "kommuner.parquet"

# Sweden-focused view
DEFAULT_CENTER = {"lat": 62.0, "lon": 15.0}
DEFAULT_ZOOM = 4.3

# Figures (optional globals, if you use them elsewhere)
karta_fig = None
karta_top_fig = None
karta_bot_fig = None

# -------------------------
# KARTA: geo helpers
# -------------------------
_geo_base_cache = None

def load_kommun_geo_base() -> gpd.GeoDataFrame:
    global _geo_base_cache
    if _geo_base_cache is not None:
        return _geo_base_cache

    if not GEO_KOMMUN_PARQUET.exists():
        raise FileNotFoundError(f"Geo parquet saknas: {GEO_KOMMUN_PARQUET}")

    gdf = gpd.read_parquet(GEO_KOMMUN_PARQUET)

    required = {"kommun", "kommun_kod", "geometry"}
    missing = required - set(gdf.columns)
    if missing:
        raise ValueError(
            f"kommuner.parquet saknar kolumner: {missing}. Har: {list(gdf.columns)}"
        )

    gdf = gdf[["kommun", "kommun_kod", "geometry"]].copy()
    gdf["kommun"] = gdf["kommun"].astype(str).str.strip()
    gdf["kommun_kod"] = gdf["kommun_kod"].astype(str).str.zfill(4)

    # Ensure WGS84
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    _geo_base_cache = gdf
    return gdf


def geojson_from_geo_simplified(tolerance: float = 0.01) -> dict:
    """
    Returns a GeoJSON that is CROPPED to Sweden bounding box,
    so the map won't show Norway/Finland etc.
    """
    gdf = load_kommun_geo_base().copy()

    # 🔒 Crop to Sweden bounding box (lon: 10.5–24.5, lat: 55.0–69.5)
    # geopandas cx uses [xmin:xmax, ymin:ymax]
    gdf = gdf.cx[10.5:24.5, 55.0:69.5]

    if tolerance and float(tolerance) > 0:
        gdf["geometry"] = gdf["geometry"].simplify(
            tolerance=float(tolerance),
            preserve_topology=True
        )

    return json.loads(gdf.to_json())


# -------------------------
# KARTA: budget map + top/bottom
# -------------------------
def build_karta_budget_figure(year: int) -> tuple["px.Figure", pd.DataFrame]:
    table = "mart_budget_per_elev_kommun"

    df = query_df(f"""
        select kommun_kod, kommun, totalt_per_elev
        from {table}
        where lasar_start = {int(year)}
    """)

    if df.empty:
        fig = px.scatter(title=f"Budget per elev – {year} (no data)")
        return fig, df

    df["kommun_kod"] = df["kommun_kod"].astype(str).str.zfill(4)
    df["totalt_per_elev"] = pd.to_numeric(df["totalt_per_elev"], errors="coerce")

    geojson = geojson_from_geo_simplified(0.01)

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations="kommun_kod",
        featureidkey="properties.kommun_kod",
        color="totalt_per_elev",
        hover_name="kommun",
        hover_data={
            "kommun_kod": True,
            # nicer formatting in tooltip
            "totalt_per_elev": ":,.0f",
        },
        mapbox_style="carto-positron",
        center=DEFAULT_CENTER,
        zoom=float(DEFAULT_ZOOM),
        opacity=0.80,
        title=f"Budget per elev – {year}",
    )

    fig.update_layout(
        margin={"r": 0, "t": 55, "l": 0, "b": 0},
    )

    return fig, df


def build_top_bottom_budget(df_budget: pd.DataFrame, n: int) -> tuple["px.Figure", "px.Figure"]:
    if df_budget is None or df_budget.empty:
        fig_top = px.bar(title=f"Top {n} (no data)")
        fig_bot = px.bar(title=f"Bottom {n} (no data)")
        return fig_top, fig_bot

    d = df_budget.dropna(subset=["totalt_per_elev"]).copy()
    d["totalt_per_elev"] = pd.to_numeric(d["totalt_per_elev"], errors="coerce")
    d = d.dropna(subset=["totalt_per_elev"])

    top = d.sort_values("totalt_per_elev", ascending=False).head(int(n))
    bot = d.sort_values("totalt_per_elev", ascending=True).head(int(n))

    fig_top = px.bar(
        top.sort_values("totalt_per_elev", ascending=True),
        x="totalt_per_elev",
        y="kommun",
        orientation="h",
        title=f"Top {n} (högst budget per elev)",
        labels={"kommun": "Kommun", "totalt_per_elev": "SEK per elev"},
    )
    fig_top.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0}, height=520)

    fig_bot = px.bar(
        bot.sort_values("totalt_per_elev", ascending=False),
        x="totalt_per_elev",
        y="kommun",
        orientation="h",
        title=f"Bottom {n} (lägst budget per elev)",
        labels={"kommun": "Kommun", "totalt_per_elev": "SEK per elev"},
    )
    fig_bot.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0}, height=520)

    return fig_top, fig_bot
