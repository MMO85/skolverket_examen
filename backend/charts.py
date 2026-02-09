import pandas as pd
import plotly.express as px

def chart_behorighet_gender(df: pd.DataFrame):
    if df is None or df.empty:
        fig = px.bar(pd.DataFrame({"program": [], "behorighet_pct": [], "kon": []}),
                     x="program", y="behorighet_pct", color="kon")
        fig.update_layout(title="No data")
        return fig

    fig = px.bar(
        df,
        x="program",
        y="behorighet_pct",      # expected 0..100
        color="kon",
        barmode="group",
        range_y=[0, 100],
        labels={
            "program": "Upper secondary program",
            "behorighet_pct": "Eligibility (%)",
            "kon": "Gender",
        },
    )

    # ---- Clean layout (like your other pages) ----
    fig.update_layout(
        title=dict(
            text="Eligibility for Upper Secondary School — Girls vs Boys (National, 2024/25)",
            x=0.0, xanchor="left",
            y=0.95, yanchor="top",
            font=dict(size=20, color="rgba(0,0,0,0.85)"),
        ),
        bargap=0.35,        # فاصله بین برنامه‌ها
        bargroupgap=0.15,   # فاصله بین Girls / Boys
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=70, r=30, t=70, b=60),
        legend=dict(
            orientation="h",
            y=1.05,
            x=0.0,
            xanchor="left",
            title_text="",
            font=dict(size=12),
        ),
        modebar_remove=[
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
        ],
    )

    # ---- Axes (no grid, soft grey) ----
    fig.update_xaxes(
        title_text="Upper secondary program",
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.2)",
        tickfont=dict(color="rgba(0,0,0,0.6)"),
        title_font=dict(color="rgba(0,0,0,0.6)"),
    )

    fig.update_yaxes(
        title_text="Eligibility (%)",
        range=[0, 100],
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="rgba(0,0,0,0.2)",
        tickfont=dict(color="rgba(0,0,0,0.6)"),
        title_font=dict(color="rgba(0,0,0,0.6)"),
        ticksuffix="%",
        tickformat=".0f",
        automargin=True,
    )
    fig.update_traces(
        width=0.25   
)

    return fig