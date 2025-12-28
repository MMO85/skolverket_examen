import json
from pathlib import Path

import duckdb
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st


# -------------------------
# App setup
# -------------------------
st.set_page_config(page_title="Skolverket Dashboard", layout="wide")
st.title("📊 Skolverket")
st.caption("DuckDB (DLT) + dbt marts + Sverigekarta (kommuner)")

APP_DIR = Path(__file__).resolve().parent          # .../skolverket_examen/app
ROOT_DIR = APP_DIR.parent                          # .../skolverket_examen
DB_PATH = ROOT_DIR / "csv_ingestion_pipeline.duckdb"

GEO_KOMMUN_PARQUET = APP_DIR / "geo" / "processed" / "kommuner.parquet"


# -------------------------
# Helpers
# -------------------------
def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


@st.cache_data(show_spinner=False)
def load_df(sql: str) -> pd.DataFrame:
    with get_con() as con:
        return con.execute(sql).df()


@st.cache_data(show_spinner=False)
def distinct_vals(table: str, col: str):
    df = load_df(f'SELECT DISTINCT "{col}" AS v FROM {table} WHERE "{col}" IS NOT NULL ORDER BY 1')
    return df["v"].tolist()


@st.cache_data(show_spinner=False)
def load_kommun_geo() -> gpd.GeoDataFrame:
    if not GEO_KOMMUN_PARQUET.exists():
        raise FileNotFoundError(f"Geo parquet saknas: {GEO_KOMMUN_PARQUET}")

    gdf = gpd.read_parquet(GEO_KOMMUN_PARQUET)

    required = {"kommun", "kommun_kod", "geometry"}
    missing = required - set(gdf.columns)
    if missing:
        raise ValueError(f"kommuner.parquet saknar kolumner: {missing}. Har: {list(gdf.columns)}")

    # Standardisera nycklar
    gdf["kommun"] = gdf["kommun"].astype(str).str.strip()
    gdf["kommun_kod"] = gdf["kommun_kod"].astype(str).str.zfill(4)

    # Säkerställ CRS (Plotly vill ha lon/lat)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    return gdf


def kpis(df: pd.DataFrame):
    a, b, c, d = st.columns(4)
    a.metric("Rader", f"{len(df):,}")
    b.metric("Kolumner", f"{df.shape[1]}")
    c.metric("Null-celler", f"{int(df.isna().sum().sum()):,}")
    d.metric("Unika kommuner", f"{df['kommun'].nunique():,}" if "kommun" in df.columns else "—")


def map_center_sweden():
    # Ungefärlig mittpunkt för Sverige
    return {"lat": 62.0, "lon": 15.0, "zoom": 3.6}


# -------------------------
# Checks
# -------------------------
if not DB_PATH.exists():
    st.error(f"Databasen hittas inte: {DB_PATH}\n\nKör DLT + dbt först.")
    st.stop()

try:
    gdf_geo = load_kommun_geo()
except Exception as e:
    st.error(f"Kunde inte läsa geo-data.\n\n{e}")
    st.stop()


# -------------------------
# Navigation
# -------------------------
PAGES = ["🗺️ Karta (Ranking)", "🏆 Topplista", "🧪 Nationella prov (trend)", "🧾 Overview"]
page = st.sidebar.radio("Välj vy", PAGES, index=0)

st.sidebar.markdown("---")
st.sidebar.caption("Körflöde: DLT → dbt run/test → Streamlit")


# ==========================================================
# PAGE 1: Map (kommun choropleth) - från mart_ranked_kommun_ak9
# ==========================================================
if page == "🗺️ Karta (Ranking)":
    st.subheader("🗺️ Sverigekarta – kommunranking (åk 9)")

    table = "staging_data.mart_ranked_kommun_ak9"

    years = distinct_vals(table, "lasar_start")
    lans = distinct_vals(table, "lan")
    amnen = distinct_vals(table, "amne")
    huvudman = distinct_vals(table, "huvudman_typ")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        year = st.selectbox("Läsår start", years, index=(len(years) - 1) if years else 0, key="map_year")
    with c2:
        lan_sel = st.selectbox("Län", ["(alla)"] + lans, index=0, key="map_lan")
    with c3:
        amne_sel = st.selectbox("Ämne", ["(alla)"] + amnen, index=0, key="map_amne")
    with c4:
        huvud_sel = st.selectbox("Huvudman", ["(alla)"] + huvudman, index=0, key="map_huvud")

    metric = st.selectbox(
        "Färgskala",
        ["score_0_100", "avg_gap_f_minus_m", "avg_total"],
        index=0,
        help="score_0_100 är normaliserad 0–100. avg_total är snittbetygspoäng.",
        key="map_metric",
    )

    where = [f"lasar_start = {int(year)}"] if years else ["1=1"]
    if lan_sel != "(alla)":
        where.append(f"lan = {sql_quote(lan_sel)}")
    if amne_sel != "(alla)":
        where.append(f"amne = {sql_quote(amne_sel)}")
    if huvud_sel != "(alla)":
        where.append(f"huvudman_typ = {sql_quote(huvud_sel)}")

    # Vi tar bara det vi behöver + kommun_kod (nyckeln!)
    df_scores = load_df(f"""
        SELECT
            kommun,
            kommun_kod,
            lan,
            lan_kod,
            {metric} AS score,
            rank_in_sweden
        FROM {table}
        WHERE {" AND ".join(where)}
    """)

    if df_scores.empty:
        st.warning("Inga rader för valda filter.")
        st.stop()

    # Standardisera nycklar
    df_scores["kommun_kod"] = df_scores["kommun_kod"].astype(str).str.zfill(4)

    # Merge: geo + score via kommun_kod (stabilt!)
    gdf_merged = gdf_geo.merge(
        df_scores[["kommun_kod", "score", "rank_in_sweden"]],
        on="kommun_kod",
        how="left",
    )

    # GeoJSON för Plotly
    geojson = json.loads(gdf_merged.to_json())  # properties innehåller kommun/kommun_kod/lan_kod/score

    center = map_center_sweden()

    # Plotly choropleth_mapbox
    fig = px.choropleth_mapbox(
        gdf_merged,
        geojson=geojson,
        locations="kommun_kod",
        featureidkey="properties.kommun_kod",
        color="score",
        hover_name="kommun",
        hover_data={"kommun_kod": True, "score": True, "rank_in_sweden": True},
        mapbox_style="carto-positron",
        center={"lat": center["lat"], "lon": center["lon"]},
        zoom=center["zoom"],
        opacity=0.7,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(fig, use_container_width=True)

    # Debug/Matchning – visa ev. missing scores
    with st.expander("🔎 Debug / matchning (valfritt)"):
        st.write("Geo features:", len(gdf_geo))
        st.write("Score rows:", len(df_scores))
        miss = gdf_merged[gdf_merged["score"].isna()][["kommun", "kommun_kod"]].head(30)
        st.write("Kommuner utan match (första 30):")
        st.dataframe(miss, use_container_width=True)

    st.write("### 🔎 Data (förhandsvisning)")
    kpis(df_scores)
    st.dataframe(df_scores.sort_values("rank_in_sweden").head(200), use_container_width=True)


# =========================================
# PAGE 2: Topplista (samma mart-tabell)
# =========================================
elif page == "🏆 Topplista":
    st.subheader("🏆 Topplista – kommunranking (åk 9)")
    table = "staging_data.mart_ranked_kommun_ak9"

    years = distinct_vals(table, "lasar_start")
    amnen = distinct_vals(table, "amne")

    c1, c2, c3 = st.columns(3)
    with c1:
        year = st.selectbox("Läsår start", years, index=(len(years) - 1) if years else 0, key="top_year")
    with c2:
        amne_sel = st.selectbox("Ämne", ["(alla)"] + amnen, index=0, key="top_amne")
    with c3:
        top_n = st.slider("Top N", 5, 100, 25, key="top_n")

    where = [f"lasar_start = {int(year)}"] if years else ["1=1"]
    if amne_sel != "(alla)":
        where.append(f"amne = {sql_quote(amne_sel)}")

    df = load_df(f"""
        SELECT *
        FROM {table}
        WHERE {" AND ".join(where)}
        ORDER BY rank_in_sweden ASC
        LIMIT {int(top_n)}
    """)

    kpis(df)
    st.dataframe(df, use_container_width=True)

    if not df.empty and "score_0_100" in df.columns and "kommun" in df.columns:
        st.write("### 📊 score_0_100 (Top N)")
        chart_df = df.sort_values("score_0_100")[["kommun", "score_0_100"]].set_index("kommun")
        st.bar_chart(chart_df)


# =========================================
# PAGE 3: Nationella prov trend
# =========================================
elif page == "🧪 Nationella prov (trend)":
    st.subheader("🧪 Nationella prov (åk 9) – trend över tid")
    table = "staging_data.mart_nationella_prov_ak9"

    years = distinct_vals(table, "lasar_start")
    amnen = distinct_vals(table, "amne")
    lans = distinct_vals(table, "lan")

    c1, c2, c3 = st.columns(3)
    with c1:
        amne_sel = st.selectbox("Ämne", ["(alla)"] + amnen, index=0, key="np_amne")
    with c2:
        lan_sel = st.selectbox("Län", ["(alla)"] + lans, index=0, key="np_lan")
    with c3:
        metric = st.selectbox(
            "Metric",
            ["betygspoang_totalt", "betygspoang_flickor", "betygspoang_pojkar", "betygspoang_gap_f_minus_m"],
            index=0,
            key="np_metric",
        )

    where = ["1=1"]
    if amne_sel != "(alla)":
        where.append(f"amne = {sql_quote(amne_sel)}")
    if lan_sel != "(alla)":
        where.append(f"lan = {sql_quote(lan_sel)}")

    trend = load_df(f"""
        SELECT lasar_start, AVG({metric}) AS value
        FROM {table}
        WHERE {" AND ".join(where)}
        GROUP BY lasar_start
        ORDER BY lasar_start
    """)

    if trend.empty:
        st.info("Inga rader för valda filter.")
    else:
        st.line_chart(trend.set_index("lasar_start")["value"])

    st.write("### 🔎 Preview")
    preview = load_df(f"""
        SELECT *
        FROM {table}
        WHERE {" AND ".join(where)}
        LIMIT 300
    """)
    kpis(preview)
    st.dataframe(preview, use_container_width=True)


# =========================================
# PAGE 4: Overview
# =========================================
else:
    st.subheader("🧾 Overview")
    table = "staging_data.mart_overview"

    source_files = distinct_vals(table, "source_file")
    chosen = st.multiselect("source_file (valfritt)", source_files, default=source_files[:1], key="ov_files")
    text_search = st.text_input("Sök i statistik_text (valfritt)", "", key="ov_search")

    where = ["1=1"]
    if chosen:
        escaped = ", ".join(sql_quote(x) for x in chosen)
        where.append(f"source_file IN ({escaped})")
    if text_search.strip():
        safe = text_search.replace("'", "''")
        where.append(f"statistik_text ILIKE '%{safe}%'")

    df = load_df(f"""
        SELECT *
        FROM {table}
        WHERE {" AND ".join(where)}
        LIMIT 1000
    """)

    a, b, c = st.columns(3)
    a.metric("Rader (preview)", f"{len(df):,}")
    b.metric("Har URL", f"{int(df['url_value'].notna().sum()):,}" if "url_value" in df.columns else "—")
    c.metric("Unika source_file", f"{df['source_file'].nunique():,}" if "source_file" in df.columns else "—")

    st.dataframe(df, use_container_width=True)
