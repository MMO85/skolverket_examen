import pandas as pd
import plotly.express as px
from backend.data_processing import trend_df, choice_df, fair_df


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
        huvudman=state.trend_huvudman,
        subject=state.trend_subject,
    )

    metric = "score"

    if metric in df.columns:
        df = df.dropna(subset=[metric])

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

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(x=0.02, xanchor="left"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_traces(line=dict(width=3), marker=dict(size=7))

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        title="Trend: Total Score",
    )
    fig.update_yaxes(title_text="Total Score")

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

    # ✅ FIX: normalize year type (Taipy gives "2022" as str, DF has np.int32)
    fair_year = state.fair_year
    if not _is_all(fair_year):
        try:
            fair_year = int(fair_year)
        except Exception:
            fair_year = "All"

    df = _apply_common_filters(
        df,
        year=fair_year,
        lan=state.fair_lan,
        kommun=None,
        huvudman=state.fair_huvudman,
        subject=state.fair_subject,
    )

    metric = state.fair_metric

    if metric in df.columns:
        df = df.dropna(subset=[metric])

    if df.empty or metric not in df.columns:
        state.fair_table = df.head(50)
        fig = px.bar(pd.DataFrame({"kommun": [], "value": []}), x="kommun", y="value")
        fig.update_layout(title="No data for this selection")
        state.fair_fig = fig
        return

def refresh_fairness(state):
    df = fair_df.copy()

    # ✅ year type fix
    fair_year = state.fair_year
    if not _is_all(fair_year):
        try:
            fair_year = int(fair_year)
        except Exception:
            fair_year = "All"

    # فیلترها
    df = _apply_common_filters(
        df,
        year=fair_year,
        lan=state.fair_lan,
        kommun=None,
        huvudman=state.fair_huvudman,
        subject=state.fair_subject,
    )

    # اگر دیتا نبود
    if df.empty:
        state.fair_table = df.head(50)
        fig = px.bar(pd.DataFrame({"kommun": [], "value": []}), x="kommun", y="value")
        fig.update_layout(title="No data for this selection")
        state.fair_fig = fig
        return

    # ✅ 1) آماده‌سازی دیتا (Aggregation صحیح)
    df_g = (
        df.groupby("kommun", as_index=False)[
            ["betygpoang_flickor", "betygpoang_pojkar"]
        ]
        .mean()
    )

    # Top 30 برای خوانایی
    df_g["gap_abs"] = (df_g["betygpoang_flickor"] - df_g["betygpoang_pojkar"]).abs()
    df_g = df_g.sort_values("gap_abs", ascending=False).head(30)

    # ✅ 2) نمودار دوتایی کنار هم
    fig = px.bar(
        df_g,
        x="kommun",
        y=["betygpoang_flickor", "betygpoang_pojkar"],
        barmode="group",
        labels={"value": "Average grade", "variable": "Group"},
    )

    fig.update_layout(
        title=(
            f"Average grades — Girls vs Boys (Top 30 gap)<br>"
            f"{state.fair_subject} | {state.fair_huvudman} | {state.fair_lan} | {state.fair_year}"
        ),
        xaxis_tickangle=-40,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)

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

    # =========================
    # 1) 100% stacked per kommun (single year)
    # =========================
    df = choice_df.copy()

    # Filters for the kommun chart
    if not _is_all(state.parent_choice_year):
        try:
            y = int(state.parent_choice_year)
            df = df[df["year"] == y]
        except Exception:
            # اگر year قابل تبدیل نبود، خالی برگردان
            df = df.iloc[0:0]

    if not _is_all(state.parent_choice_lan):
        df = df[df["lan"] == state.parent_choice_lan]

    # only Kommunal/Enskild
    df = df[df["huvudman_typ"].isin(["Kommunal", "Enskild"])].dropna(subset=["share", "n_students"])

    if df.empty:
        state.parent_choice_fig_stack = px.bar(
            pd.DataFrame({"kommun": [], "share": [], "huvudman_typ": []}),
            x="kommun",
            y="share",
            color="huvudman_typ",
            barmode="stack",
        ).update_layout(title="No data for this selection")

        state.parent_choice_fig_trend = px.line(
            pd.DataFrame({"year": [], "share": [], "kommun": []}),
            x="year",
            y="share",
            color="kommun",
        ).update_layout(title="No data for trend selection")
        return

    top_n = int(state.parent_choice_top_n)

    # Top kommun by total students (stable)
    top_kommun = (
        df.groupby("kommun", as_index=False)["n_students"]
          .sum()
          .sort_values("n_students", ascending=False)
          .head(top_n)["kommun"]
          .tolist()
    )

    df_k = df[df["kommun"].isin(top_kommun)]

    fig_stack = px.bar(
        df_k,
        x="kommun",
        y="share",
        color="huvudman_typ",
        barmode="stack",
    )

    fig_stack.update_layout(
        title=f"Parent choice by kommun (Top {top_n}) — Kommunal vs Enskild (Åk 1–9)",
        xaxis_tickangle=-40,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.02, x=0),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig_stack.update_yaxes(
        title_text="Share",
        tickformat=".0%",
        range=[0, 1],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    )
    fig_stack.update_xaxes(showgrid=False)

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
        title=f"Trend över tid — Andel Enskild per kommun (Top {top_n}, Åk 1–9)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.02, x=0),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig_trend.update_yaxes(
        title_text="Share of Enskild",
        tickformat=".0%",
        range=[0, 1],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    )
    fig_trend.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)

    state.parent_choice_fig_trend = fig_trend


def on_change_parent_choice(state):
    refresh_parent_choice(state)


def on_click_parent_choice(state):
    refresh_parent_choice(state)
