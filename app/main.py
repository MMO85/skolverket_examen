from taipy.gui import Gui
from frontend.pages.home import home_page
from frontend.pages.kpi_trend import kpi_trend_page
from frontend.pages.kpi_fairness import kpi_fairness_page
from frontend.pages.kpi_parent_choice import kpi_parent_choice_page
from frontend.pages.extra import extra_page
from frontend.pages.behorighet_gender import behorighet_gender_page
from backend.updates import refresh_karta
import frontend.theme.plotly_theme
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

    #karta state
   
    karta_fig, karta_top_fig, karta_bot_fig,
)
from frontend.pages.karta import on_init as karta_on_init

from frontend.pages.karta import karta_page

from backend.updates import (
    refresh_trend,
    refresh_fairness,
    update_trend_kommun_lov,
    refresh_parent_choice,
)



nav = [
  ("Home", "home"),
  ("Utveckling över tid (Åk 9)", "kpi_trend"),
  ("Likvärdighet", "kpi_fairness"),
  ("Skolval", "kpi-parent-choice"),
  ("Bakgrund & Kön", "behorighet_gender"),
  ("Budgetkarta", "karta"),
]

root_md = """
<|{nav}|navbar|>
"""

pages = {
    "/": root_md,
    "home": home_page,
    "results-over-time": kpi_trend_page,
    "Gender-Gap": kpi_fairness_page,
    "School-Choice": kpi_parent_choice_page,
    "HighSchool-Eligibility": behorighet_gender_page,
    "Budget-map": karta_page,
    "_": extra_page,
}


# =========================
# DEBUG PRINTS (اضافه شد)
# =========================




def on_init(state):
    # Trend
    update_trend_kommun_lov(state)
    refresh_trend(state)

    # Fairness
    refresh_fairness(state)

    # Parent Choice
    refresh_parent_choice(state)

  
    refresh_behorighet_gender(state)

    karta_on_init(state)

    refresh_karta(state)

print(">>> PLOTLY THEME LOADED <<<")



if __name__ == "__main__":
    Gui(pages=pages, css_file="assets/main.css").run(
        port=8080,
        dark_mode=False,
        use_reloader=False,  # ✅ جلوگیری از invalid session
        on_init=on_init,
    )
