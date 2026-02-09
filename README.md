# skolverket_examen

Ett lokalt, reproducerbart end-to-end-projekt som visar hur man går från Skolverkets öppna CSV-filer till en körbar analysdashboard.

Pipeline (översikt):
1) **DLT** läser alla filer i `raw_data/` och laddar dem till **DuckDB** (`staging_data.raw_data`)
2) **dbt** transformerar `raw_data` → `stg_*` (staging) → `slv_*` (silver) → `mart_*` (analysmarts)
3) **Geo-preprocess** förbereder kommun-/län-geometrier för kartvyer
4) **App** (Taipy) visualiserar trender, könsskillnader, skolval, behörighet och budgetkarta

---

## Teknikstack

- Python (3.10+)
- DuckDB (lokal analytisk databas)
- DLT (ingestion)
- dbt + duckdb-adapter (modellering)
- GeoPandas + Plotly (kartor/figurer)
- Taipy (dashboard)
- Git/GitHub (versionshantering)

---

## Projektstruktur (kort)

skolverket_examen/
├─ raw_data/ # Rådata (CSV/XLSX)
├─ data_extract_load/ # DLT-pipeline
│ └─ load_csv_data.py
├─ csv_ingestion_pipeline.duckdb
├─ dbt_project/ # dbt-projekt
│ ├─ dbt_project.yml
│ ├─ profiles.yml
│ ├─ staging/
│ ├─ models/
│ └─ marts/
├─ app/ # App entrypoints + geo
│ ├─ main.py
│ ├─ app.py
│ ├─ app_karta.py
│ └─ geo/
├─ backend/ # Processing, charts, DB, state updates
├─ frontend/ # Pages, layout, theme
├─ assets/ # CSS
└─ storytelling/ # Notebook/analys


---

## Förutsättningar

- Python 3.10+
- Git
- Windows: PowerShell eller Git Bash

---

## Installation

### 1) Skapa och aktivera virtual environment

PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Git Bash:

python -m venv .venv
source .venv/Scripts/activate
2) Installera beroenden
python -m pip install -r requirements.txt
Steg 1: Ladda data med DLT (CSV → DuckDB)
Kör från repo-roten:

python data_extract_load/load_csv_data.py
Scriptet gör i korthet:

hittar alla CSV-filer i raw_data/

läser varje fil robust (för att minska läsfel)

konverterar kolumner till text för att undvika schema-konflikter

lägger till filnamn som kolumn (t.ex. source_file)

laddar data till DuckDB: csv_ingestion_pipeline.duckdb

skriver rådata till staging_data.raw_data

Snabbcheck: finns data?
python -c "import duckdb; con=duckdb.connect('csv_ingestion_pipeline.duckdb'); print(con.execute(\"select count(*) from staging_data.raw_data\").fetchone())"
Snabbcheck: antal körningar (_dlt_load_id)
python -c "import duckdb; con=duckdb.connect('csv_ingestion_pipeline.duckdb'); print(con.execute(\"select count(distinct _dlt_load_id) from staging_data.raw_data\").fetchone())"
Steg 2: dbt (staging → silver → marts)
Rekommenderat: använd projektets profiles.yml
I den här setupen kör du dbt med --profiles-dir . från dbt_project/ så att dbt alltid använder projektets profil.

cd dbt_project
python -m dbt.cli.main debug --profiles-dir .
python -m dbt.cli.main run   --profiles-dir .
python -m dbt.cli.main test  --profiles-dir .
Om allt är rätt ska dbt test ge PASS på testerna.

Exempel på centrala marts
mart_ranked_kommun_ak9

mart_nationella_prov_ak9

mart_parent_trend_ak9

mart_parent_fairness_ak9

mart_budget_per_elev_kommun

Steg 3: Geo-data (kommuner & län)
Rå geo:

app/geo/raw/kommuner.geojson

app/geo/raw/lan.geojson

Preprocess (bygger om/uppdaterar förenklade filer):

python app/geo/preprocess_geo.py
Output (för prestanda i kartor):

app/geo/processed/kommuner.parquet

app/geo/processed/lan.parquet

(ev. förenklade geojson beroende på implementation)

Steg 4: Starta dashboarden (Taipy)
Kör från repo-roten:

python -m app.main
Dashboarden innehåller vyer för:

Results over time (Åk 9)

Gender gap

School choice

High school eligibility

Budget map (karta)

Designprinciper (viktigt i grupparbete)
Raw layer först: staging_data.raw_data är rådata (minimalt tolkad).

All logik i dbt: typning, rensning och business logic i stg_*, slv_*, mart_*.

Inga hårdkodade scheman: använd {{ target.schema }} i SQL där det behövs.

Undvik binära merge-konflikter: checka inte in lokala artefakter:

*.duckdb

target/

logs/

Vanliga problem & fixar
dbt fungerar inte som dbt.exe på Windows
Använd alltid:

python -m dbt.cli.main ...
dbt hittar inte profiles.yml
Kör kommandon från dbt_project/ och ange:

python -m dbt.cli.main run --profiles-dir .
Appen hittar inte moduler (t.ex. frontend)
Kör från repo-roten och som modul:

python -m app.main
DuckDB-path fel i dbt
Öppna dbt_project/profiles.yml och kontrollera att path: pekar på rätt csv_ingestion_pipeline.duckdb (relativt dbt_project/).

Status
✔ DLT pipeline fungerar (CSV → DuckDB)

✔ dbt run & test (staging/silver/marts)

✔ Geo-preprocess för kartor

✔ Dashboard (Taipy) med flera analysvyer

Nästa steg (förbättringar)
Klick på kommun → drilldown (detaljkort + tooltips)

Utöka dbt-testning (uniqueness + not_null på fler nycklar/mått)

Deployment (Docker/Cloud)

Utöka dataset (fler år/indikatorer)


Om du vill kan jag också anpassa README:n 1:1 mot exakt hur din `load_csv_data.py` beter sig (t.ex. om den synkar/”rensar gamla loads”, exakt vilka kolumner som finns i `staging_data.raw_data`, och om ni kör Taipy-only eller även har kvar Streamlit).
::contentReference[oaicite:0]{index=0}
