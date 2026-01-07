import taipy.gui.builder as tgb

with tgb.Page() as kpi_trend_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# KPI — Parent Trend", mode="md")

        with tgb.layout(columns="2 1"):
            with tgb.part(class_name="card"):
                tgb.text("Trend chart here (Plotly)", mode="md")
                # tgb.chart(figure="{trend_fig}", mode="plotly")

            with tgb.part(class_name="card"):
                tgb.text("Filters", mode="md")
                # tgb.selector(...)

__all__ = ["kpi_trend_page"]
