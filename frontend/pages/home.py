import taipy.gui.builder as tgb

with tgb.Page() as home_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# Skolverket Dashboard", mode="md")
        tgb.text("Choose a KPI page from the menu.", mode="md")

__all__ = ["home_page"]
