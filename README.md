# skolverket_examen
CSV-pipeline med DLT och DuckDB

Det här projektet innehåller en pipeline för dataladdning byggd med DLT (Data Load Tool) och DuckDB som mål. Pipelinens syfte är att läsa in råa CSV-filer från mappen raw_data/ och lagra dem i en lokal DuckDB-databas för vidare bearbetning.

Mappstruktur
project_root/
│
├── data_extract_load/
│     └── load_csv_data.py        # Huvudscript för att ladda in CSV-filer
│
├── raw_data/                     # Rådata i CSV-format
│
├── requirements.txt
└── README.md

Förutsättningar

Skapa och aktivera ett virtual environment

Installera beroenden:

pip install -r requirements.txt


requirements.txts innehålla:

dlt
pandas
duckdb

Om load_csv_data.py

Scriptet gör följande:

Letar upp alla CSV-filer i mappen raw_data/

Läser varje fil med en flexibel Pythontolkare för att undvika läsfel

Konverterar alla kolumner till text för att undvika schema-konflikter mellan olika CSV-filer

Lägger till filnamnet som en extra kolumn

Kör DLT-pipen och laddar datan till DuckDB

Skapar den lokala databasen:

csv_ingestion_pipeline.duckdb

Så kör du pipelinen

I projektroten, kör:

python data_extract_load/load_csv_data.py


Vid lyckad körning visas ett meddelande i stil med:

CSV data loaded successfully via DLT.

Inspektera datan i DuckDB

Starta Python och kör exempelvis:

import duckdb
con = duckdb.connect("csv_ingestion_pipeline.duckdb")
con.execute("SELECT * FROM staging_data.raw_data LIMIT 10").fetchall()


Då kan du verifiera att datan har laddats korrekt.

Övrigt:

Alla CSV-filer laddas in oavsett om deras kolumnstrukturer skiljer sig åt.

Konvertering till textformat är avsiktligt och följer principen för rådata (raw layer).

Pipeline-utdata kan senare användas för att bygga silver-lager, datamodeller eller analyser.

-------------------------------------------------------------

DBT: ###  jag har ändrat några path, ser så här ut nedan, men vi kan fixa senare hela snyggare. 
Projektstruktur (kort)
skolverket_examen/
├── data_extract_load/        # DLT-pipeline (CSV → DuckDB)
├── raw_data/                 # Rå CSV-filer (lokalt)
├── csv_ingestion_pipeline.duckdb
├── dbt_project/              # dbt-projekt
│   ├── dbt_project.yml
│   ├── staging/
│   ├── models/
│   └── marts/
├── requirements.txt
└── README.md

Förutsättningar : Python 3.10+, Git, Windows (Git Bash eller PowerShell funkar)

Så kör du projektet (från noll)
1️. Skapa och aktivera virtual environment
python -m venv .venv
source .venv/Scripts/activate

2️. Installera beroenden
python -m pip install -r requirements.txt

 Steg 1: Ladda data med DLT

Detta läser alla CSV-filer i raw_data/ och skapar/uppdaterar DuckDB-filen.

python data_extract_load/load_csv_data.py


Resultat:

csv_ingestion_pipeline.duckdb skapas/uppdateras

Tabellen staging_data.raw_data innehåller:

raw_line

source_file

Steg 2: Konfigurera dbt (en gång per dator)  اینجا برای ت هم مهمە

Skapa filen:

~/.dbt/profiles.yml


Innehåll:

skolverket_examen:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: ../csv_ingestion_pipeline.duckdb
      schema: staging_data

Steg 3: Kör dbt (staging → silver → marts)

Gå in i dbt-mappen:

cd dbt_project


Kör modeller:

python -m dbt.cli.main run --profiles-dir "$USERPROFILE/.dbt"


Kör tester:

python -m dbt.cli.main test --profiles-dir "$USERPROFILE/.dbt"


Om allt är rätt ska:

dbt run bygga 16 modeller

dbt test ge PASS på alla tester

Designprinciper (viktigt för grupparbete)

stg_raw_data
Endast rådata (raw_line, source_file)
 ingen parsing

slv_cleaned_data
Första “rensade” lagret
 URL extraheras här
url_value är valfri (kan vara NULL)

schema & sources

Inga hårdkodade scheman (main)

{{ target.schema }} används överallt

Lokala filer ignoreras

.duckdb

target/

logs/
→ inga binära merge-konflikter

 Vanliga problem

dbt.exe funkar inte på Windows
→ använd alltid:

python -m dbt.cli.main ...


dbt hittar inte projektet
→ se till att du kör kommandon inifrån dbt_project/

--- Status

✔ DLT pipeline fungerar
✔ dbt run & test gröna
✔ Team-safe setup
-------------------------------------------------------
stremlit app/app.py
Data ingestion (DLT)

Transformation & modeller (dbt + DuckDB)

Visualisering (Streamlit + Plotly + GeoData)

🧱 Systemöversikt

Teknikstack

Python 3.11

DuckDB (lokal analytisk databas)

DLT (data ingestion)

dbt (staging + marts)

Streamlit (dashboard)

GeoPandas + Plotly (kartvisualisering)

Git / GitHub (versionshantering)

 Projektstruktur
skolverket_examen/
│
├── app/
│   ├── app.py                  # Streamlit-dashboard
│   └── geo/
│       ├── raw/                # Original geojson (kommuner, län)
│       ├── processed/          # Förenklad geo-data (parquet + geojson)
│       ├── preprocess_geo.py   # Rensar & standardiserar geo-data
│       └── load_geo.py
│
├── data_extract_load/
│   └── load_csv_data.py        # DLT-pipeline (CSV → DuckDB)
│
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   └── dbt_project.yml
│
├── csv_ingestion_pipeline.duckdb
├── requirements.txt
├── README.md
└── .gitignore

🔄 Dataflöde (Steg för steg)
1️⃣ Data ingestion – DLT

Skolverkets CSV-filer laddas till DuckDB via DLT.

source .venv/Scripts/activate
python data_extract_load/load_csv_data.py


Resultat:

DuckDB-fil skapas/uppdateras:

csv_ingestion_pipeline.duckdb


Rådata hamnar i schema staging_data

2️⃣ Transformation – dbt

dbt används för:

Staging (rensning, typning)

Business logic

Analytiska marts

cd dbt_project
python -m dbt.cli.main debug --profiles-dir "$USERPROFILE/.dbt"
python -m dbt.cli.main run   --profiles-dir "$USERPROFILE/.dbt"
python -m dbt.cli.main test  --profiles-dir "$USERPROFILE/.dbt"


Exempel på marts:

mart_ranked_kommun_ak9

mart_nationella_prov_ak9

mart_parent_trend_ak9

mart_parent_fairness_ak9

3️⃣ Geo-data – Kommuner & Län

Sveriges kommun- och länsgränser används för kartan.

Rådata

app/geo/raw/kommuner.geojson

app/geo/raw/lan.geojson

Bearbetning

Geo-datan:

projiceras till WGS84

trasiga geometrier fixas

förenklas (för prestanda)

standardiseras så att kolumner matchar dbt-data

python app/geo/preprocess_geo.py


Resultat:

app/geo/processed/
├── kommuner.parquet   # kolumner: kommun, kommun_kod, lan_kod, geometry
├── lan.parquet        # kolumner: lan, lan_kod, geometry

🗺️ Dashboard – Streamlit

Dashboarden visar:

🗺️ Karta

Choropleth-karta över Sveriges kommuner

Färg baserat på score_0_100 (åk 9)

Filter:

Läsår

Ämne

Huvudman

🏆 Ranking

Topp/Nedersta kommuner

Jämförelser inom län och nationellt

🧾 Overview

Textdata och metadata från källfiler

Starta dashboarden från projektroten:

python -m streamlit run app/app.py

✅ Kvalitet & Robusthet

dbt tester (not_null, m.fl.)

Säker SQL-escape i Streamlit

Tydlig matchning mellan geo-data och dbt-marts

Debug-sektion för att visa om kommuner saknar matchning
#
## Streamlit 
python app/geo/process_geo.py
python -m streamlit run app/app.py


🎯 Sammanfattning

Detta projekt demonstrerar:

End-to-end data engineering

Analytisk modellering med dbt

Geografisk visualisering

Tydlig separation mellan ingestion, transformation och presentation

Allt körbart lokalt, reproducerbart och granskningsbart.
--------------------------