import taipy.gui.builder as tgb

with tgb.Page() as extra_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# Not Found", mode="md")
        tgb.text("This page does not exist.", mode="md")

__all__ = ["extra_page"]
