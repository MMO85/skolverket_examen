import taipy.gui.builder as tgb
from backend.data_processing import (
    years, lan_list, huvudman_list, subject_list,
    fair_year, fair_lan, fair_huvudman, fair_subject,
    fair_fig,
)
from backend.updates import on_change_fairness, on_click_fairness, refresh_fairness


with tgb.Page() as kpi_fairness_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# KPI — Fairness", mode="md")

        with tgb.layout(columns="2 1"):
            with tgb.part(class_name="card"):
                tgb.chart(figure="{fair_fig}", mode="plotly")
                # جدول رو هم اگر نمیخوای، اصلاً نیاریم

            with tgb.part(class_name="card"):
                tgb.text("### Filters", mode="md")

                tgb.selector(value="{fair_year}", lov=years, dropdown=True, label="Year", on_change=on_change_fairness)
                tgb.selector(value="{fair_lan}", lov=lan_list, dropdown=True, label="Län", on_change=on_change_fairness)
                tgb.selector(value="{fair_huvudman}", lov=huvudman_list, dropdown=True, label="Huvudman", on_change=on_change_fairness)
                tgb.selector(value="{fair_subject}", lov=subject_list, dropdown=True, label="Subject", on_change=on_change_fairness)

                tgb.button("Refresh", on_action=on_click_fairness)


def on_init(state):
    refresh_fairness(state)


__all__ = ["kpi_fairness_page", "on_init"]
