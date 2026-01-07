import taipy.gui.builder as tgb

with tgb.Page() as kpi_choice_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# KPI — Parent Choice", mode="md")
        tgb.text("Choice KPIs and charts will go here.", mode="md")

__all__ = ["kpi_choice_page"]
