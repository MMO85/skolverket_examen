import taipy.gui.builder as tgb

with tgb.Page() as kpi_fairness_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# KPI — Fairness", mode="md")
        tgb.text("Fairness indicators will go here.", mode="md")

__all__ = ["kpi_fairness_page"]
