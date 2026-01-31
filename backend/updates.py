import pandas as pd
import plotly.express as px
from backend.data_processing import trend_df, choice_df, fair_df
from backend.data_processing import build_behorighet_gender_figure
from backend.data_processing import (
    build_karta_budget_figure,   # (fig_map, df_budget) برای یک سال
    build_top_bottom_budget,     # (fig_top, fig_bot) از df_budget
    query_df,)   # ✅ از backend.db میاد داخل data_processing و اینجا قابل استفاده است



def _is_all(x) -> bool:
    """Treat All/ALL/None/empty as All."""
    if x is None:
        return True
    s = str(x).strip()
    return s == "" or s.lower() == "all"


def _apply_common_filters(df: pd.DataFrame, year, lan, kommun, huvudman, subject):
    """Common filter helper (used by Trend/Fairness)."""
    if not _is_all(year):
        df = df[df["year"] == year]
    if not _is_all(lan):
        df = df[df["lan"] == lan]
    if kommun is not None and not _is_all(kommun):
        df = df[df["kommun"] == kommun]
    if not _is_all(huvudman):
        df = df[df["huvudman_typ"] == huvudman]
    if not _is_all(subject):
        df = df[df["subject"] == subject]
    return df


# ---------------- TREND ----------------

def refresh_trend(state):
    df = trend_df.copy()

    # Trend باید چندساله باشد → year را فیلتر نمی‌کنیم
    df = _apply_common_filters(
        df,
        year="All",
        lan=state.trend_lan,
        kommun=state.trend_kommun,
        huvudman=(    "All"
        if not _is_all(state.trend_subject)
        else state.trend_huvudman
),
        subject=state.trend_subject,
    )

    metric = "score"

    if metric in df.columns:
        df = df.dropna(subset=[metric])

    if not df.empty and "year" in df.columns:
        # مطمئن شو year عددی است
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df.dropna(subset=["year"])
        if not df.empty:
            last_year = int(df["year"].max())
            df = df[df["year"] < last_year]

    if df.empty or metric not in df.columns:
        fig = px.line(pd.DataFrame({"year": [], "value": []}), x="year", y="value")
        fig.update_layout(title="No data for this selection")
        state.trend_fig = fig
        return

    # Color logic: if subject is All -> split by subject, else split by huvudman
    color = "subject" if _is_all(state.trend_subject) else "huvudman_typ"

    group_cols = ["year"]
    if color in df.columns:
        group_cols.append(color)

    df_plot = (
        df.groupby(group_cols, as_index=False)[metric]
          .mean()
          .sort_values("year")
    )


    fig = px.line(
        df_plot,
        x="year",
        y=metric,
        color=(color if color in df_plot.columns else None),
        markers=True,
    )

        # ---- Styling / Layout (clean & no duplicates) ----
    fig.update_layout(
        title=dict(
            text="How Grade 9 Scores Have Changed Over Time",
            x=0.0,
            xanchor="left",
            y=0.98,
            yanchor="top",
            pad=dict(t=6, r=2),
            automargin=True,
        ),
        showlegend=False,
        
        margin=dict(l=80, r=30, t=70, b=70),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        modebar_remove=[
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
        ],
    )

    fig.update_xaxes(
        title_text="Year",
        title_standoff=22,     # year پایین‌تر
        showgrid=False,        # grid حذف
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.18)",
        tickfont=dict(color="rgba(0,0,0,0.55)"),
        title_font=dict(color="rgba(0,0,0,0.55)"),
    )

    fig.update_yaxes(
        title_text="Performance Percentile (0–100)",
        range=[0, 100],
        showgrid=False,        # grid حذف
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.18)",
        tickfont=dict(color="rgba(0,0,0,0.55)"),
        title_font=dict(color="rgba(0,0,0,0.55)"),
        automargin=True,
    )

    fig.update_traces(line=dict(width=3), marker=dict(size=7))
    last_year = df_plot["year"].max()

    for key, g in df_plot.groupby(color):
        last_row = g[g["year"] == last_year]
        if last_row.empty:
            continue

        fig.add_annotation(
            x=last_row["year"].iloc[0],
            y=last_row[metric].iloc[0],
            text=str(key),
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(size=12, color="rgba(0,0,0,0.7)"),
            xshift=8,
        )



    state.trend_fig = fig


def on_change_trend(state):
    update_trend_kommun_lov(state)
    refresh_trend(state)


def on_click_trend(state):
    refresh_trend(state)


def update_trend_kommun_lov(state):
    if _is_all(state.trend_lan):
        state.trend_kommun_lov = ["All"] + sorted(trend_df["kommun"].dropna().unique().tolist())
        if state.trend_kommun not in state.trend_kommun_lov:
            state.trend_kommun = "All"
        return

    df_lan = trend_df[trend_df["lan"] == state.trend_lan]
    kommuner = ["All"] + sorted(df_lan["kommun"].dropna().unique().tolist())
    state.trend_kommun_lov = kommuner

    if state.trend_kommun not in state.trend_kommun_lov:
        state.trend_kommun = "All"


# ---------------- FAIRNESS ----------------

def refresh_fairness(state):
    df = fair_df.copy()

    # --- year type fix (Taipy may give str) ---
    fair_year = state.fair_year
    if not _is_all(fair_year):
        try:
            fair_year = int(fair_year)
        except Exception:
            fair_year = "All"

    # --- filters ---
    df = _apply_common_filters(
        df,
        year=fair_year,
        lan=state.fair_lan,
        kommun=None,
        huvudman=state.fair_huvudman,
        subject=state.fair_subject,
    )

    if df.empty:
        state.fair_table = df.head(50)
        fig = px.bar(pd.DataFrame({"kommun": [], "value": []}), x="value", y="kommun", orientation="h")
        fig.update_layout(title="No data for this selection")
        state.fair_fig = fig
        return

    # --- aggregate to kommun level ---
    df_g = (
        df.groupby("kommun", as_index=False)[["betygpoang_flickor", "betygpoang_pojkar"]]
          .mean()
    )

    # --- Top 15 by absolute gender gap ---
    TOP_N = 10
    df_g["gap_abs"] = (df_g["betygpoang_flickor"] - df_g["betygpoang_pojkar"]).abs()
    df_g = df_g.sort_values("gap_abs", ascending=False).head(TOP_N)

    # --- reshape to long format for grouped bars (Girls/Boys) ---
    df_long = df_g.melt(
        id_vars=["kommun", "gap_abs"],
        value_vars=["betygpoang_flickor", "betygpoang_pojkar"],
        var_name="Group",
        value_name="Average grade points",
    )

    # nicer labels
    df_long["Group"] = df_long["Group"].replace({
        "betygpoang_flickor": "Girls",
        "betygpoang_pojkar": "Boys",
    })

    # keep kommun order (top gap at top)
    kommun_order = df_g["kommun"].tolist()
    df_long["kommun"] = pd.Categorical(df_long["kommun"], categories=kommun_order, ordered=True)
    df_long = df_long.sort_values("kommun", ascending=False)  # so first appears on top in horizontal bar

    # --- plot: horizontal grouped bar ---
    fig = px.bar(
        df_long,
        x="Average grade points",
        y="kommun",
        color="Group",
        barmode="group",
        orientation="h",
    )

    # --- clean title (no clutter line with filters) ---
    title_text = f"Average Grade Differences Between Girls and Boys {TOP_N} Municipalities"
    #subtitle = f"{state.fair_subject} • {state.fair_huvudman} • {state.fair_lan} • {state.fair_year}"

    fig.update_layout(
        title=dict(
            text=f"{title_text}<br><span style='font-size:12px;color:rgba(0,0,0,0.55)'></span>",
            x=0.0,
            xanchor="left",
            y=0.92,
            yanchor="top",
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            y=1.08,
            x=0.0,
            xanchor="left",
            title_text="",
            font=dict(size=12),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=90, r=20, t=90, b=50),
        modebar_remove=[
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
        ],
    )

    # --- axes styling (minimal) ---
    fig.update_xaxes(
        title_text="Average grade points",
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.18)",
        tickfont=dict(color="rgba(0,0,0,0.6)"),
        title_font=dict(color="rgba(0,0,0,0.6)"),
    )

    fig.update_yaxes(
        title_text="",  # kommun labels are self-explanatory
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(color="rgba(0,0,0,0.65)"),
        automargin=True,
    )

    # slightly thicker bars
    fig.update_traces(marker_line_width=0)

    # --- table (optional but useful) ---
    state.fair_table = df_g[["kommun", "betygpoang_flickor", "betygpoang_pojkar", "gap_abs"]].copy()

    state.fair_fig = fig



def on_change_fairness(state):
    refresh_fairness(state)

def on_click_fairness(state):
    refresh_fairness(state)


# ---------------- PARENT CHOICE (NO SUBJECT) ----------------

def _is_all(x):
    if x is None:
        return True
    return str(x).strip().lower() == "all"


def refresh_parent_choice(state):
    """
    Requires choice_df with columns:
      year (int), lan (str), kommun (str), huvudman_typ (Kommunal/Enskild),
      n_students (int), share (float 0..1)
    """

    df = choice_df.copy()

    # -------------------------
    # Filters (single year)
    # -------------------------
    if not _is_all(state.parent_choice_year):
        try:
            y = int(state.parent_choice_year)
            df = df[df["year"] == y]
        except Exception:
            df = df.iloc[0:0]

    if not _is_all(state.parent_choice_lan):
        df = df[df["lan"] == state.parent_choice_lan]

    df = df[df["huvudman_typ"].isin(["Kommunal", "Enskild"])].dropna(subset=["n_students"])

    if df.empty:
        state.parent_choice_fig_stack = (
            px.bar(pd.DataFrame({"kommun": [], "share": [], "huvudman_typ": []}),
                   x="kommun", y="share", color="huvudman_typ", barmode="stack")
            .update_layout(title="No data for this selection")
        )
       
        return

    # -------------------------
    # Top N kommun (by total students)
    # -------------------------
    try:
        top_n = int(state.parent_choice_top_n)
    except Exception:
        top_n = 10

    totals = (
        df.groupby("kommun", as_index=False)["n_students"]
          .sum()
          .sort_values("n_students", ascending=False)
          .head(top_n)
    )
    top_kommun = totals["kommun"].tolist()
    df_k = df[df["kommun"].isin(top_kommun)].copy()

    # -------------------------
    # Ensure share is valid (recompute if missing/bad)
    # -------------------------
    share_bad = ("share" not in df_k.columns) or df_k["share"].isna().any()
    if share_bad:
        denom = (
            df_k.groupby(["kommun"], as_index=False)["n_students"]
               .sum()
               .rename(columns={"n_students": "total_students"})
        )
        df_k = df_k.merge(denom, on="kommun", how="left")
        df_k["share"] = df_k["n_students"] / df_k["total_students"]

    # -------------------------
    # Order kommun by Enskild share (nice reading)
    # -------------------------
    pivot = (
        df_k.pivot_table(index="kommun", columns="huvudman_typ", values="share", aggfunc="mean")
          .fillna(0.0)
    )
    sort_col = "Enskild" if "Enskild" in pivot.columns else pivot.columns[0]
    kommun_order = pivot.sort_values(sort_col, ascending=False).index.tolist()

    # -------------------------
    # Plot (100% stacked)
    # -------------------------
    fig_stack = px.bar(
        df_k,
        x="kommun",
        y="share",
        color="huvudman_typ",
        barmode="stack",
        category_orders={"kommun": kommun_order},
    )

    # -------------------------
    # Styling (clean & slim)
    # -------------------------
    fig_stack.update_layout(

        height=380, 
        bargap=0.38, 
        bargroupgap=0.06,

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=70, r=20, t=70, b=85),

        legend=dict(
            orientation="h",
            y=1.05,
            x=0.0,
            xanchor="left",
            yanchor="bottom",
            title_text="",
            font=dict(size=12),
        ),

        modebar_remove=[
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
        ],
    )

    fig_stack.update_yaxes(
        title_text="Share (%)",
        tickformat=".0%",
        range=[0, 1],
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.18)",
        tickfont=dict(color="rgba(0,0,0,0.55)"),
        title_font=dict(color="rgba(0,0,0,0.55)"),
        automargin=True,
    )

    fig_stack.update_xaxes(
        title_text="Municipality",
        tickangle=-30,
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.18)",
        tickfont=dict(color="rgba(0,0,0,0.55)"),
        title_font=dict(color="rgba(0,0,0,0.55)"),
    )

    fig_stack.update_traces(marker_line_width=0)

    state.parent_choice_fig_stack = fig_stack





    # =========================
    # 2) Trend over time — Enskild share per kommun (within selected län)
    # =========================
    df_t = choice_df.copy()

    if not _is_all(state.parent_choice_lan):
        df_t = df_t[df_t["lan"] == state.parent_choice_lan]

    df_t = df_t[df_t["huvudman_typ"].isin(["Kommunal", "Enskild"])].dropna(subset=["n_students"])

    if df_t.empty:
        fig_trend = px.line(
            pd.DataFrame({"year": [], "share": [], "kommun": []}),
            x="year",
            y="share",
            color="kommun",
        )
        fig_trend.update_layout(title="No data for trend selection")
        state.parent_choice_fig_trend = fig_trend
        return

    # Sum counts per year/kommun/type
    g = (
        df_t.groupby(["year", "kommun", "huvudman_typ"], as_index=False)["n_students"]
            .sum()
    )

    # Pivot to get Kommunal + Enskild counts
    p = (
        g.pivot_table(
            index=["year", "kommun"],
            columns="huvudman_typ",
            values="n_students",
            aggfunc="sum",
        )
        .fillna(0.0)
        .reset_index()
    )

    if "Enskild" not in p.columns:
        p["Enskild"] = 0.0
    if "Kommunal" not in p.columns:
        p["Kommunal"] = 0.0

    p["total"] = p["Enskild"] + p["Kommunal"]
    p["share"] = p.apply(lambda r: (r["Enskild"] / r["total"]) if r["total"] > 0 else 0.0, axis=1)

    # Limit lines: Top N kommun by total students across years (within selected län)
    top_n = int(state.parent_choice_top_n)
    kommun_rank = (
        df_t.groupby("kommun", as_index=False)["n_students"]
            .sum()
            .sort_values("n_students", ascending=False)
            .head(top_n)["kommun"]
            .tolist()
    )

    p = p[p["kommun"].isin(kommun_rank)].sort_values(["year", "kommun"])

    fig_trend = px.line(
        p,
        x="year",
        y="share",
        color="kommun",
        markers=False,
    )

    fig_trend.update_layout(
        title=dict(
            text="Trend in Independent School Enrollment Over Time",
            x=0,
            xanchor="left",
            font=dict(size=20)
    
    ) ,  
        height=380,
        margin=dict(l=70, r=20, t=50, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,   # 👈 legend حذف
    
)
    fig_trend.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.2)",
        tickfont=dict(color="rgba(0,0,0,0.6)"),
        title_font=dict(color="rgba(0,0,0,0.6)"),
        dtick=1,
)

    
    max_share = df_k["share"].max()  # یا df_plot اگر اسمش اونه

    fig_trend.update_yaxes(
        title_text="Share of Independent Schools",
        tickformat=".0%",
        range=[0, max_share * 1.15],
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.2)",
        tickfont=dict(color="rgba(0,0,0,0.6)"),
        title_font=dict(color="rgba(0,0,0,0.6)"),
    )
    fig_trend.update_traces(
        line=dict(width=2),
)


    state.parent_choice_fig_trend = fig_trend


def on_change_parent_choice(state):
    refresh_parent_choice(state)


def on_click_parent_choice(state):
    refresh_parent_choice(state)


def refresh_behorighet_gender(state):
    state.beh_fig = build_behorighet_gender_figure("2024/25")


## ------------------ karta (BUDGET only) ------------------
def refresh_karta(state):
    """
    Budget per elev per kommun (senaste tillgängliga år).
    - بدون Ranking
    - بدون فیلتر
    - Top 10 / Bottom 10
    """

    # آخرین سال موجود را مستقیم از DB می‌گیریم
    dfy = query_df("""
        select max(lasar_start) as y
        from main.mart_budget_per_elev_kommun
    """)
    if dfy.empty or dfy.iloc[0]["y"] is None:
        state.karta_fig = None
        state.karta_top_fig = None
        state.karta_bot_fig = None
        return

    year = int(dfy.iloc[0]["y"])

    fig, df_budget = build_karta_budget_figure(year)
    state.karta_fig = fig

    state.karta_top_fig, state.karta_bot_fig = build_top_bottom_budget(df_budget, 10)


def on_click_karta(state):
    refresh_karta(state)