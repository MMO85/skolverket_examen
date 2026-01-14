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

    # drop NaN metric
    if metric in df.columns:
        df = df.dropna(subset=[metric])

    # if empty -> blank chart
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

    # Aggregate to avoid duplicate rows per year
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
    # --- Styling: transparent background + nicer look ---
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",   # بیرون نمودار (کل کارت)
        plot_bgcolor="rgba(0,0,0,0)",    # داخل نمودار
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

    # Grid ملایم
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False)

    # Line/marker کمی نرم‌تر
    fig.update_traces(line=dict(width=3), marker=dict(size=7))

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        title="Trend: Total Score",
    )
    fig.update_yaxes(title_text="Total Score")

    state.trend_fig = fig


def on_change_trend(state):
    # فقط وقتی län عوض شد، kommun lov باید آپدیت بشه
    update_trend_kommun_lov(state)
    refresh_trend(state)


def on_click_trend(state):
    refresh_trend(state)


def update_trend_kommun_lov(state):
    # اگر län انتخاب نشده -> همه kommunها
    if _is_all(state.trend_lan):
        state.trend_kommun_lov = ["All"] + sorted(trend_df["kommun"].dropna().unique().tolist())
        # اگر kommun فعلی داخل لیست نیست، ریست کن
        if state.trend_kommun not in state.trend_kommun_lov:
            state.trend_kommun = "All"
        return

    # kommun های همان län
    df_lan = trend_df[trend_df["lan"] == state.trend_lan]
    kommuner = ["All"] + sorted(df_lan["kommun"].dropna().unique().tolist())
    state.trend_kommun_lov = kommuner

    # اگر kommun فعلی داخل لیست جدید نیست، ریست کن
    if state.trend_kommun not in state.trend_kommun_lov:
        state.trend_kommun = "All"


# ---------------- CHOICE ----------------
def refresh_choice(state):
    df = choice_df.copy()

    df = _apply_common_filters(
        df,
        year=state.choice_year,
        lan=state.choice_lan,
        kommun=None,
        huvudman=state.choice_huvudman,
        subject=state.choice_subject,
    )

    metric = state.choice_metric

    if metric in df.columns:
        df = df.dropna(subset=[metric])

    if df.empty or metric not in df.columns:
        state.choice_table = df.head(50)
        fig = px.bar(pd.DataFrame({"kommun": [], "value": []}), x="kommun", y="value")
        fig.update_layout(title="No data for this selection")
        state.choice_fig = fig
        return

    top_n = int(state.choice_top_n)

    df_plot = (
        df[["kommun", metric, "lan", "huvudman_typ", "year"]]
        .sort_values(metric, ascending=False)
        .head(top_n)
    )

    fig = px.bar(df_plot, x="kommun", y=metric)
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        title=f"Choice: Top {top_n} kommun by {metric}",
        xaxis_tickangle=-40,
    )

    state.choice_fig = fig
    state.choice_table = df_plot


def on_change_choice(state):
    refresh_choice(state)


def on_click_choice(state):
    refresh_choice(state)


# ---------------- FAIRNESS ----------------
def refresh_fairness(state):
    df = fair_df.copy()

    df = _apply_common_filters(
        df,
        year=state.fair_year,
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

    df_plot = (
        df[["kommun", metric, "fairness_label", "gap_abs", "lan", "year"]]
        .sort_values(metric, ascending=False)
        .head(30)
    )

    color = "fairness_label" if "fairness_label" in df_plot.columns else None
    fig = px.bar(df_plot, x="kommun", y=metric, color=color)
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        title=f"Fairness: Top 30 kommun by {metric}",
        xaxis_tickangle=-40,
    )

    state.fair_fig = fig
    state.fair_table = df_plot


def on_change_fairness(state):
    refresh_fairness(state)


def on_click_fairness(state):
    refresh_fairness(state)
