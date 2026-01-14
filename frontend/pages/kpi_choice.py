import taipy.gui.builder as tgb
from backend.data_processing import (
    years, lan_list, huvudman_list, subject_list,
    choice_metrics,
    choice_year, choice_lan, choice_huvudman, choice_subject,
    choice_metric, choice_top_n, choice_fig, choice_table,
)
from backend.updates import on_change_choice, on_click_choice, refresh_choice

with tgb.Page() as kpi_choice_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# KPI — Parent Choice", mode="md")

        with tgb.layout(columns="2 1"):
            with tgb.part(class_name="card"):
                tgb.chart(figure="{choice_fig}", mode="plotly")
                tgb.table("{choice_table}", page_size=10)

            with tgb.part(class_name="card"):
                tgb.text("### Filters", mode="md")
                tgb.selector(value="{choice_year}", lov=years, dropdown=True, label="Year", on_change=on_change_choice)
                tgb.selector(value="{choice_lan}", lov=lan_list, dropdown=True, label="Län", on_change=on_change_choice)
                tgb.selector(value="{choice_huvudman}", lov=huvudman_list, dropdown=True, label="Huvudman", on_change=on_change_choice)
                tgb.selector(value="{choice_subject}", lov=subject_list, dropdown=True, label="Subject", on_change=on_change_choice)
                tgb.selector(value="{choice_metric}", lov=choice_metrics, dropdown=True, label="Metric", on_change=on_change_choice)

                tgb.selector(
                    value="{choice_top_n}",
                    lov=[10, 20, 30, 50, 100],
                    dropdown=True,
                    label="Top N kommun",
                    on_change=on_change_choice
                )

                tgb.button("Refresh", on_action=on_click_choice)

def on_init(state):
    refresh_choice(state)

__all__ = ["kpi_choice_page", "on_init"]
