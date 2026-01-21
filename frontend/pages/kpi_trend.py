import taipy.gui.builder as tgb
from backend.updates import on_change_trend, on_click_trend, refresh_trend
from backend.data_processing import (
    years, lan_list, huvudman_list, subject_list,
    trend_lan, trend_kommun, trend_kommun_lov, trend_huvudman, trend_subject, trend_fig,
)




with tgb.Page() as kpi_trend_page:
    with tgb.part(class_name="container card"):
        with tgb.layout(columns="2 1"):
            with tgb.part(class_name="card"):
                tgb.chart(figure="{trend_fig}", mode="plotly")
                

            with tgb.part(class_name="card"):
                tgb.text("### Filters", mode="md")
                
                tgb.selector(value="{trend_lan}", lov=lan_list, dropdown=True, label="Län", on_change=on_change_trend)
                tgb.selector(
    value="{trend_kommun}",
    lov="{trend_kommun_lov}",
    dropdown=True,
    label="Kommun",
    on_change=on_change_trend,
)
                #tgb.selector(value="{trend_kommun}", lov=kommun_list, dropdown=True, label="Kommun", on_change=on_change_trend)
                tgb.selector(value="{trend_huvudman}", lov=huvudman_list, dropdown=True, label="Huvudman", on_change=on_change_trend)
                tgb.selector(value="{trend_subject}", lov=subject_list, dropdown=True, label="Subject", on_change=on_change_trend)
                #tgb.selector(value="{trend_metric}", lov=trend_metrics_lov, dropdown=True, label="Metric", on_change=on_change_trend)

                tgb.button("Refresh", on_action=on_click_trend)

def on_init(state):
    refresh_trend(state)

__all__ = ["kpi_trend_page", "on_init"]
