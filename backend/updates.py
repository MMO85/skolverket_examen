import pandas as pd
import plotly.express as px

from backend.data_processing import trend_df, choice_df, fair_df


def _apply_common_filters(df: pd.DataFrame, year, lan, kommun, huvudman, subject):
    if year != "All":
        df = df[df["year"] == year]
    if lan != "All":
        df = df[df["lan"] == lan]
    if kommun is not None and kommun != "All":
        df = df[df["kommun"] == kommun]
    if huvudman != "All":
        df = df[df["huvudman_typ"] == huvudman]
    if subject != "All":
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
        state.trend_table = df.head(50)
        fig = px.line(pd.DataFrame({"year": [], "value": []}), x="year", y="value")
        fig.update_layout(title="No data for this selection")
        state.trend_fig = fig
        return

    df_plot = df.sort_values("year")

    # رنگ منطقی
    color = "subject" if state.trend_subject == "All" else "huvudman_typ"

    fig = px.line(df_plot, x="year", y=metric, color=color, markers=True)
    metric_label = METRIC_LABELS.get(metric, metric)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), title=f"Trend: {metric_label}")
    fig.update_yaxes(title_text=metric_label)

    state.trend_fig = fig
    state.trend_table = df_plot.head(50)


def on_change_trend(state):
    # اگر län عوض شد، lov kommun را به‌روز کن
    update_trend_kommun_lov(state)
    refresh_trend(state)



def on_click_trend(state):
    refresh_trend(state)


def update_trend_kommun_lov(state):
    # اگر län انتخاب نشده -> همه kommunها
    if state.trend_lan == "All":
        state.trend_kommun_lov = ["All"] + sorted(trend_df["kommun"].dropna().unique().tolist())
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
