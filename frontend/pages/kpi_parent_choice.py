import taipy.gui.builder as tgb
from backend.data_processing import (
    parent_choice_years,
    lan_list,
    
)
from backend.updates import on_change_parent_choice, on_click_parent_choice


with tgb.Page() as kpi_parent_choice_page:
    with tgb.part(class_name="container card"):
        with tgb.layout(columns="2 1"):
            with tgb.part(class_name="card"):
                tgb.text("### Kommunal vs Enskild per kommun (100% stacked)", mode="md")
                tgb.chart(figure="{parent_choice_fig_stack}", mode="plotly")
                tgb.chart(figure="{parent_choice_fig_trend}", mode="plotly")
                #tgb.table("{parent_choice_table}", page_size=10)

            with tgb.part(class_name="card"):
                tgb.text("### Filters", mode="md")

                tgb.selector(
                    value="{parent_choice_year}",
                    lov=parent_choice_years,
                    dropdown=True,
                    label="Year (kommun chart)",
                    on_change=on_change_parent_choice,
                )

                tgb.selector(
                    value="{parent_choice_lan}",
                    lov=lan_list,
                    dropdown=True,
                    label="Län",
                    on_change=on_change_parent_choice,
                )

                tgb.selector(
                    value="{parent_choice_top_n}",
                    lov=[5, 10, 20, 30],
                    dropdown=True,
                    label="Top N kommun",
                    on_change=on_change_parent_choice,
                )

                tgb.button("Refresh", on_action=on_click_parent_choice)
