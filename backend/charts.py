import pandas as pd
import plotly.express as px

def empty_fig(title: str = "No data"):
    fig = px.line(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
    fig.update_layout(title=title)
    return fig

def line_fig(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = ""):
    if df.empty:
        return empty_fig(title or "No data")
    fig = px.line(df, x=x, y=y, color=color, markers=True)
    fig.update_layout(title=title, margin=dict(l=10, r=10, t=40, b=10))
    return fig

def bar_fig(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = ""):
    if df.empty:
        return empty_fig(title or "No data")
    fig = px.bar(df, x=x, y=y, color=color)
    fig.update_layout(title=title, margin=dict(l=10, r=10, t=40, b=10))
    return fig



def chart_behorighet_gender(df):
    fig = px.bar(
        df,
        x="program",
        y="behorighet_pct",
        color="kon",
        barmode="group",
        range_y=[0, 100],
        labels={
            "program": "Gymnasieprogram",
            "behorighet_pct": "Behörighet (%)",
            "kon": "Kön"
        },
        title="Behörighet till gymnasieprogram – Flickor vs Pojkar (Nationellt, 2024/25)"
    )
    return fig

