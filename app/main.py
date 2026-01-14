from taipy.gui import Gui
from frontend.pages.home import home_page
from frontend.pages.kpi_trend import kpi_trend_page
from frontend.pages.kpi_choice import kpi_choice_page
from frontend.pages.kpi_fairness import kpi_fairness_page
from frontend.pages.extra import extra_page
from backend.updates import update_trend_kommun_lov
from backend.data_processing import (
    # LOVs
    years, lan_list, kommun_list, huvudman_list, subject_list,
    trend_metric, choice_metrics, fair_metrics, trend_kommun_lov,

    # Trend state
    trend_year, trend_lan, trend_kommun, trend_huvudman, trend_subject,
    trend_metric, trend_fig, trend_table,

    # Choice state
    choice_year, choice_lan, choice_huvudman, choice_subject,
    choice_metric, choice_top_n, choice_fig, choice_table,

    # Fairness state
    fair_year, fair_lan, fair_huvudman, fair_subject,
    fair_metric, fair_fig, fair_table,
)

from backend.updates import refresh_trend, refresh_choice, refresh_fairness


pages = {
    "home": home_page,
    "kpi_trend": kpi_trend_page,
    "kpi_choice": kpi_choice_page,
    "kpi_fairness": kpi_fairness_page,
    "_": extra_page,
}


def on_init(state):
    # ✅ اولین بار چارت‌ها را پر کن
    refresh_trend(state)
    refresh_choice(state)
    refresh_fairness(state)
    update_trend_kommun_lov(state)
    


if __name__ == "__main__":
    Gui(pages=pages, css_file="assets/main.css").run(
        title="Skolverket KPI Dashboard",
        port=8080,
        dark_mode=False,
        use_reloader=False,   # ✅ برای جلوگیری از invalid session
        on_init=on_init,
    )
