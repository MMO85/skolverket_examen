from taipy.gui import Gui

from frontend.pages.home import home_page
from frontend.pages.kpi_trend import kpi_trend_page
from frontend.pages.kpi_choice import kpi_choice_page
from frontend.pages.kpi_fairness import kpi_fairness_page
from frontend.pages.extra import extra_page

pages = {
    "home": home_page,
    "kpi_trend": kpi_trend_page,
    "kpi_choice": kpi_choice_page,
    "kpi_fairness": kpi_fairness_page,
    "_": extra_page,
}

if __name__ == "__main__":
    Gui(pages=pages, css_file="assets/main.css").run(
        dark_mode=False,
        use_reloader=True,
        title="Skolverket KPI Dashboard",
        port=8080,
    )
