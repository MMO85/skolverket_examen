import taipy.gui.builder as tgb

FEATURES = [
    ("1", "🎓", "Results over time (Grade 9)",
     "Track Grade 9 performance trends over time by subject, and compare across municipalities, counties, and school providers."),
    ("2", "👓", "Gender differences",
     "Compare outcomes between girls and boys to identify where gaps are widening or narrowing across regions and years."),
    ("3", "🏫", "School choice (Public vs Independent)",
     "Explore parental school choice patterns and how they vary over time and between municipalities/counties."),
    ("4", "✅", "Equity & key indicators",
     "Review indicators related to educational equity to highlight disparities, outliers, and areas needing attention."),
    ("5", "🗺️", "Budget map",
     "Visualize cost/budget per student geographically to quickly spot municipalities that stand out."),
    ("6", "📌", "How to use the dashboard",
     "Use filters (year, municipality/county, provider, subject) to build comparisons and generate evidence-based insights."),
]

with tgb.Page() as home_page:
    with tgb.part(class_name="container card"):
        tgb.text(value="# School performance and equity - a data-driven analysis", mode="md")

        with tgb.html("div", style="margin-top:14px; display:flex; flex-direction:column; gap:12px;"):
            for num, icon, title, desc in FEATURES:
                with tgb.html("div", style="display:flex; gap:12px; align-items:flex-start;"):
                    tgb.html("div", f"{num}.", style="font-size:20px; font-weight:800; width:34px;")
                    tgb.html("div", icon, style="font-size:34px; width:44px; line-height:1;")
                    with tgb.html("div", style="flex:1;"):
                        tgb.html("div", title, style="font-size:18px; font-weight:800; margin-bottom:2px;")
                        tgb.html("div", desc, style="font-size:16px; color:#374151;")

__all__ = ["home_page"]
