import pandas as pd
from backend.db import load_table
from backend.db import query_df
from backend.charts import chart_behorighet_gender

TREND_TABLE = "main.mart_parent_trend_ak9"
CHOICE_TABLE = "main.mart_parent_choice_ak1_9"
FAIR_TABLE = "main.mart_parent_fairness_ak9"

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
subject_list = ["All"] + sorted({s for s in subject_list if str(s).strip() != "All"})

# ---------------- Parent Choice state ----------------

parent_choice_year = "All"
parent_choice_lan = "All"
parent_choice_top_n = 30
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
        from main.mart_behorighet_national_gender_2024_25
        order by program, kon
    """).df()


# Figure state
beh_fig = None

def build_behorighet_gender_figure(year: str):
    # اگر بعداً چند سال داشتی، اینجا می‌تونه فیلتر سال بخوره.
    df = query_df("""
        select kon, program, behorighet_pct
        from main.mart_behorighet_national_gender_2024_25
        order by program, kon
    """)
    return chart_behorighet_gender(df)

