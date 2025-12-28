import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path

# -------------------------
# Basic setup
# -------------------------
st.set_page_config(page_title="Skolverket Dashboard", layout="wide")
st.title("📊 Skolverket (Simple)")
st.caption("DuckDB + dbt marts")

DB_PATH = Path(__file__).resolve().parents[1] / "csv_ingestion_pipeline.duckdb"


def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)


def sql_quote(s: str) -> str:
    # minimal "safe quoting" for strings
    return "'" + s.replace("'", "''") + "'"


@st.cache_data
def load_df(sql: str) -> pd.DataFrame:
    with get_con() as con:
        return con.execute(sql).df()


@st.cache_data
def distinct_vals(table: str, col: str):
    df = load_df(f'SELECT DISTINCT "{col}" AS v FROM {table} WHERE "{col}" IS NOT NULL ORDER BY 1')
    return df["v"].tolist()


def show_kpis(df: pd.DataFrame):
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", f"{df.shape[1]}")
    c3.metric("Null cells", f"{int(df.isna().sum().sum()):,}")


if not DB_PATH.exists():
    st.error(f"Hittar inte databasen: {DB_PATH}. Kör DLT + dbt först.")
    st.stop()

# -------------------------
# Tabs (simple)
# -------------------------
tab_rank, tab_over = st.tabs(["🏆 Ranking", "🧾 Overview"])


# =========================
# TAB 1: Ranking (mart_ranked_kommun_ak9)
# =========================
with tab_rank:
    st.subheader("🏆 Kommun ranking (åk 9)")
    table = "staging_data.mart_ranked_kommun_ak9"

    years = distinct_vals(table, "lasar_start")
    lans = distinct_vals(table, "lan")
    amnen = distinct_vals(table, "amne")
    huvudman = distinct_vals(table, "huvudman_typ")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        year = st.selectbox("Läsår start", years, index=0 if years else 0, key="rank_year")
    with col2:
        lan_sel = st.selectbox("Län", ["(alla)"] + lans, index=0, key="rank_lan")
    with col3:
        amne_sel = st.selectbox("Ämne", ["(alla)"] + amnen, index=0, key="rank_amne")
    with col4:
        huvud_sel = st.selectbox("Huvudman", ["(alla)"] + huvudman, index=0, key="rank_huvud")

    top_n = st.slider("Top N", 5, 50, 20, key="rank_topn")

    where = []
    if years:
        where.append(f"lasar_start = {int(year)}")
    if lan_sel != "(alla)":
        where.append(f"lan = {sql_quote(lan_sel)}")
    if amne_sel != "(alla)":
        where.append(f"amne = {sql_quote(amne_sel)}")
    if huvud_sel != "(alla)":
        where.append(f"huvudman_typ = {sql_quote(huvud_sel)}")

    where_sql = " AND ".join(where) if where else "1=1"

    df = load_df(f"""
        SELECT *
        FROM {table}
        WHERE {where_sql}
        ORDER BY rank_in_sweden ASC
        LIMIT {int(top_n)}
    """)

    show_kpis(df)
    st.dataframe(df, use_container_width=True)

    # small chart
    if not df.empty and "score_0_100" in df.columns:
        st.write("### 📊 score_0_100 (Top N)")
        chart_df = df[["kommun", "score_0_100"]].set_index("kommun")
        st.bar_chart(chart_df)


# =========================
# TAB 2: Overview (mart_overview)
# =========================
with tab_over:
    st.subheader("🧾 Overview")
    table = "staging_data.mart_overview"

    source_files = distinct_vals(table, "source_file")

    chosen_file = st.selectbox(
        "Välj en fil (source_file)",
        ["(alla)"] + source_files,
        index=0,
        key="over_source_file"
    )

    text_search = st.text_input("Sök i statistik_text", "", key="over_search")

    where = []
    if chosen_file != "(alla)":
        where.append(f"source_file = {sql_quote(chosen_file)}")
    if text_search.strip():
        text_safe = text_search.replace("'", "''")
        where.append(f"statistik_text ILIKE '%{text_safe}%'")

    where_sql = " AND ".join(where) if where else "1=1"

    df = load_df(f"""
        SELECT *
        FROM {table}
        WHERE {where_sql}
        LIMIT 500
    """)

    show_kpis(df)
    st.dataframe(df, use_container_width=True)
