import taipy.gui.builder as tgb

from backend.updates import refresh_karta


with tgb.Page() as karta_page:
    with tgb.part(class_name="container card"):

        tgb.text(
            "Sweden map by municipality based on **Budget per student** (latest available year).",
            mode="md",
        )

       
        with tgb.part(class_name="card"):
            tgb.chart(figure="{karta_fig}", mode="plotly")

        # Top/Bottom
        tgb.text("## Comparison (Top/Bottom)", mode="md")
        with tgb.layout(columns="1 1"):
            tgb.chart(figure="{karta_top_fig}", mode="plotly")
            tgb.chart(figure="{karta_bot_fig}", mode="plotly")


def on_init(state):
  
    refresh_karta(state)


__all__ = ["karta_page", "on_init"]
