import taipy.gui.builder as tgb

with tgb.Page() as home_page:
    with tgb.part(class_name="container card"):
        tgb.text("# Skolverket Dashboard", mode="md")
        tgb.text(    """This dashboard provides a data-driven overview of the Swedish education system.
It allows users to explore trends in Grade 9 student performance, gender differences in outcomes, parental school choice between public and independent schools, and key indicators related to educational equity across municipalities and over time.
The dashboard is designed to support comparison, insight generation, and evidence-based analysis for policymakers, researchers, and other stakeholders.
Its goal is to improve understanding of patterns, disparities, and developments within the education system.    """, mode="md")

__all__ = ["home_page"]
