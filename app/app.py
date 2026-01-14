import taipy.gui.builder as tgb
from layout import render_layout

def build_pages():

    # ---------------- Home ----------------
    with tgb.Page() as home:
        render_layout("Home")
        tgb.text("### Welcome", mode="md")
        tgb.text(
            "Use the menu to explore trends, parental choices, and fairness indicators.",
            mode="md",
        )

    # ---------------- Trend ----------------
    with tgb.Page() as trend:
        render_layout("Trend")
        tgb.text("# Parent Trend", mode="md")
        tgb.text("Trend charts will go here.", mode="md")

    # ---------------- Choice ----------------
    with tgb.Page() as choice:
        render_layout("Choice")
        tgb.text("# Parent Choice", mode="md")
        tgb.text("Choice analysis will go here.", mode="md")

    # ---------------- Fairness ----------------
    with tgb.Page() as fairness:
        render_layout("Fairness")
        tgb.text("# Fairness", mode="md")
        tgb.text("Fairness indicators will go here.", mode="md")

    return {
        "/": home,
        "Trend": trend,
        "Choice": choice,
        "Fairness": fairness,
    }
