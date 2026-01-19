import taipy.gui.builder as tgb
from backend.data_processing import beh_fig
from backend.updates import refresh_behorighet_gender


with tgb.Page() as behorighet_gender_page:
    with tgb.part(class_name="container card"):
        tgb.navbar()
        tgb.text("# Behörighet till gymnasieskolan", mode="md")
        tgb.text("### Flickor vs Pojkar – Nationellt (2024/25)", mode="md")

        with tgb.part(class_name="card"):
            tgb.chart(figure="{beh_fig}", mode="plotly")

        tgb.text(
            "**Tolkning:** I samtliga gymnasieprogram är andelen behöriga elever något högre bland flickor än bland pojkar.",
            mode="md",
        )


def on_init(state):
    refresh_behorighet_gender(state)


__all__ = ["behorighet_gender_page", "on_init"]
