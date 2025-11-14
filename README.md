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