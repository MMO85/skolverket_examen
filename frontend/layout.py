import taipy.gui.builder as tgb

def render_navbar(active: str = ""):
    with tgb.part(class_name="topbar"):
        tgb.text("Skolverket KPI Dashboard", mode="md", class_name="brand")

        with tgb.part(class_name="nav"):
            tgb.button("Home", on_action=lambda s: s.assign("tp_location", "/home"),
                       class_name=f"nav-btn {'active' if active=='home' else ''}")
            tgb.button("Trend", on_action=lambda s: s.assign("tp_location", "/kpi_trend"),
                       class_name=f"nav-btn {'active' if active=='trend' else ''}")
            tgb.button("Choice", on_action=lambda s: s.assign("tp_location", "/kpi_choice"),
                       class_name=f"nav-btn {'active' if active=='choice' else ''}")
            tgb.button("Fairness", on_action=lambda s: s.assign("tp_location", "/kpi_fairness"),
                       class_name=f"nav-btn {'active' if active=='fairness' else ''}")

    tgb.text("---", mode="md")
