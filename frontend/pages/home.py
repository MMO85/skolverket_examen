import taipy.gui.builder as tgb

FEATURES = [
    ("🎓", "Results over time (Grade 9)",
     "Shows how Grade 9 results change over time (2018–2024) for different subjects. "
     "Use it to spot trends (improvement/decline), compare municipalities and counties, "
     "and see differences between school providers (public vs independent)."),

    ("⚥", "Gender differences",
     "Compares girls’ and boys’ outcomes side-by-side for the selected year, subject, county, and provider. "
     "Use it to identify where the gender gap is largest, whether it favors girls or boys, "
     "and which municipalities are outliers that may need further investigation."),

    ("🏫", "School choice (Public vs Independent)",
     "Explains how student distribution between public (Kommunal) and independent (Enskild) schools varies by municipality. "
     "The 100% stacked chart shows the share split for a chosen year, while the trend view shows how the independent-school share evolves over time. "
     "Use it to understand local differences in school choice and how they develop across years."),

    ("✅", "Equity & key indicators",
     "Highlights equity-related indicators and disparities across municipalities using a clear ranking view. "
     "Use it to detect uneven outcomes, compare patterns across counties/providers/subjects, "
     "and quickly find municipalities that stand out as unusually high/low (potential best practices or risk areas)."),

    ("🗺️", "Budget map",
     "Visualizes budget/cost per student on a map to show geographical variation. "
     "Includes Top/Bottom comparisons to quickly see which municipalities spend the most and least per student. "
     "Use it to spot regional patterns, extremes, and municipalities that may deserve deeper analysis."),

    ("📌", "How to use the dashboard",
     "A quick guide to working with filters (year, county, municipality, provider, subject) and reading the charts. "
     "Use it to build consistent comparisons, avoid misinterpretation (e.g., small groups/outliers), "
     "and turn the visualizations into evidence-based conclusions."),
]


with tgb.Page() as home_page:
    with tgb.part(class_name="container card"):
        tgb.text(value="# School performance and equity - a data-driven analysis", mode="md")

        with tgb.html("div", style="margin-top:14px; display:flex; flex-direction:column; gap:12px;"):
            for icon, title, desc in FEATURES:
                with tgb.html("div", style="display:flex; gap:12px; align-items:flex-start;"):
                    tgb.html("div", style="font-size:20px; font-weight:800; width:34px;")
                    tgb.html("div", icon, style="font-size:34px; width:44px; line-height:1;")
                    with tgb.html("div", style="flex:1;"):
                        tgb.html("div", title, style="font-size:18px; font-weight:800; margin-bottom:2px;")
                        tgb.html("div", desc, style="font-size:16px; color:#374151;")

__all__ = ["home_page"]
