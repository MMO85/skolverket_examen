
import pandas as pd
from backend.db import load_table

TREND_TABLE = "main.mart_parent_trend_ak9"
CHOICE_TABLE = "main.mart_parent_choice_ak9"
FAIR_TABLE = "main.mart_parent_fairness_ak9"

# Load once (fast enough for local DuckDB)
trend_df = load_table(TREND_TABLE)
choice_df = load_table(CHOICE_TABLE)
fair_df = load_table(FAIR_TABLE)

# Normalize "ALL" values coming from data to "All"
for df in (trend_df, choice_df, fair_df):
    if "subject" in df.columns:
        df["subject"] = df["subject"].replace({"ALL": "All"})
def _lov(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return ["All"]
    vals = df[col].dropna().unique().tolist()
    try:
        vals = sorted(vals)
    except Exception:
        pass
    return ["All"] + vals



# Common LOVs
years = _lov(trend_df, "year")  # year exists in all 3
lan_list = _lov(trend_df, "lan")
kommun_list = _lov(trend_df, "kommun")
huvudman_list = _lov(trend_df, "huvudman_typ")
subject_list = _lov(trend_df, "subject")
# Deduplicate subject_list and keep a single "All" on top
subject_list = ["All"] + sorted({s for s in subject_list if str(s).strip() != "All"})


# Taipy selector lov: {label: value}




choice_metrics = [
    "score",
    "rank_sweden",
    "rank_lan",
    "betygspoang_totalt",
    "betygpoang_flickor",
    "betygpoang_pojkar",
    "betygpoang_gap_f_minus_m",
]

fair_metrics = [
    "fairness_score",
    "gap_abs",
    "betygpoang_gap_f_minus_m",
    "score",
    "betygspoang_totalt",
]

# --------- State defaults (these become Taipy variables) ----------
# Trend dependent LOV for kommun (changes when trend_lan changes)
trend_kommun_lov = kommun_list[:]  # شروع: همه
# Trend
trend_year = "All"
trend_lan = "All"
trend_kommun = "All"
trend_huvudman = "All"
trend_subject = "All"
trend_metric = "score"
trend_fig = None


# Choice
choice_year = "All"
choice_lan = "All"
choice_huvudman = "All"
choice_subject = "All"
choice_metric = "score"
choice_top_n = 20
choice_fig = None
choice_table = None

# Fairness
fair_year = "All"
fair_lan = "All"
fair_huvudman = "All"
fair_subject = "All"
fair_metric = "fairness_score"
fair_fig = None
fair_table = None
