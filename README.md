📊 Skolverket KPI Dashboard

School performance, equity, and resource allocation — a data-driven analysis

📌 Project overview

This project is a data-driven analytics dashboard built on Swedish school data from Skolverket.
The goal is to make complex educational data more accessible and interpretable by transforming raw datasets into clear KPIs and interactive visualizations.

The dashboard focuses on:

student performance over time,

gender differences in outcomes,

school choice patterns (public vs independent),

equity-related indicators,

and budget per student across municipalities.

The project was developed as part of a Data Engineering / Data Analytics degree programme and serves as a complete end-to-end example of a modern analytics pipeline.

🎯 Objectives

Build a reproducible data pipeline from raw public data

Transform data into well-defined analytical models

Define and compute meaningful KPIs for education analysis

Present insights through an interactive and user-friendly dashboard

Enable comparisons across years, municipalities, counties, providers, and genders

🧱 Architecture (high level)
Raw data (Skolverket)
        ↓
DLT (data ingestion)
        ↓
DuckDB (local analytical database)
        ↓
dbt (staging + marts / KPI models)
        ↓
Taipy (interactive dashboard UI)

🛠️ Tools & technologies

Python – core programming language

DLT – reproducible data ingestion

DuckDB – analytical database

dbt – data transformation and modeling

Taipy GUI – interactive dashboard

Plotly – visualizations

Git & GitHub – version control

📈 Dashboard features
🎓 Results over time (Grade 9)

Track Grade 9 performance trends across years and subjects.
Compare municipalities, counties, and school providers to identify long-term patterns and changes.

⚥ Gender differences

Side-by-side comparison of girls’ and boys’ outcomes.
Highlights where gender gaps are largest, shrinking, or widening across regions and years.

🏫 School choice (Public vs Independent)

Shows how students are distributed between Kommunal and Enskild schools.

100% stacked bars for a selected year

Trend view showing how the share of independent schools evolves over time

✅ Equity & key indicators

Highlights disparities and outliers using ranking-based KPIs.
Helps identify municipalities that may require further attention or represent best practices.

🗺️ Budget map

Geographical visualization of budget per student.
Includes Top/Bottom comparisons to quickly identify municipalities with unusually high or low spending.

📌 How to use the dashboard

Guidance on filters and interpretation to support evidence-based analysis and avoid common pitfalls.

👥 Project roles & responsibilities

This project was developed by two contributors:

Kanilla

Data ingestion using DLT

UI structure, layout, and storytelling design

Maryam

Data modeling and transformations using dbt

KPI definitions and analytical logic

Implementation of multiple KPI pages and visualizations

Integration between data layer and UI

Work was done collaboratively, but each contributor was responsible for clearly separated parts of the pipeline.

✅ Project status

✔ The project is fully completed.
All planned KPIs are implemented, tested, and available in the dashboard.

Testing and validation included:

cross-checking KPIs against source data,

verifying filter combinations,

handling missing data and edge cases,

and visual inspection of trends and distributions.

🚀 How to run the project locally
# activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# run dbt models
dbt run

# start the dashboard
python -m app.main


The dashboard will be available at:

http://127.0.0.1:8080

📄 Data sources

Skolverket – Swedish National Agency for Education
Publicly available datasets on school results, demographics, and resources.

📌 Notes

The project is designed for analytical insight, not prediction.

Results should be interpreted with care, especially for municipalities with small student populations.

The dashboard supports exploratory analysis and hypothesis generation.