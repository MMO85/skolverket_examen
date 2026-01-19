from taipy.gui import Gui
from frontend.pages.home import home_page
from frontend.pages.kpi_trend import kpi_trend_page
from frontend.pages.kpi_fairness import kpi_fairness_page
from frontend.pages.kpi_parent_choice import kpi_parent_choice_page
from frontend.pages.extra import extra_page
from frontend.pages.behorighet_gender import behorighet_gender_page
from backend.updates import (
    refresh_trend,
    refresh_fairness,
    update_trend_kommun_lov,
    refresh_parent_choice,
    refresh_behorighet_gender,   # ✅ اینو اضافه کن
)
from backend.data_processing import beh_fig

from backend.data_processing import (
    # LOVs (اگر جایی لازم داری)
    years, lan_list, kommun_list, huvudman_list, subject_list,
    trend_kommun_lov,

    # Trend state
    trend_year, trend_lan, trend_kommun, trend_huvudman, trend_subject,
    trend_metric, trend_fig,

    # Fairness state
    fair_year, fair_lan, fair_huvudman, fair_subject,
    fair_fig, fair_table,

    # Parent choice state
    parent_choice_year, parent_choice_lan, parent_choice_top_n,
    parent_choice_fig_stack, parent_choice_fig_trend, parent_choice_table,
)

from backend.updates import (
    refresh_trend,
    refresh_fairness,
    update_trend_kommun_lov,
    refresh_parent_choice,
)

pages = {
    "home": home_page,
    "kpi_trend": kpi_trend_page,
    "kpi_fairness": kpi_fairness_page,
    "kpi-parent-choice": kpi_parent_choice_page,
    "behorighet_gender": behorighet_gender_page,
    "_": extra_page,
}

# =========================
# DEBUG PRINTS (اضافه شد)
# =========================

# اگر کلیدها فاصله/کاراکتر مخفی داشته باشن:
pages = {k.strip(): v for k, v in pages.items()}
print("DBG pages keys AFTER strip:", [repr(k) for k in pages.keys()])


def on_init(state):
    # Trend
    update_trend_kommun_lov(state)
    refresh_trend(state)

    # Fairness
    refresh_fairness(state)

    # Parent Choice
    refresh_parent_choice(state)

  
    refresh_behorighet_gender(state)


if __name__ == "__main__":
    Gui(pages=pages, css_file="assets/main.css").run(
        title="Skolverket KPI Dashboard",
        port=8080,
        dark_mode=False,
        use_reloader=False,  # ✅ جلوگیری از invalid session
        on_init=on_init,
    )
