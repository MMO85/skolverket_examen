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


Filen requirements.txt bör innehålla:

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