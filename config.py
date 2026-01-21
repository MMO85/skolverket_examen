from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "raw_data"
DB_FILE = BASE_DIR / "csv_ingestion_pipeline.duckdb"
DBT_DIR = BASE_DIR / "dbt_project"

def as_posix(p: Path) -> str:
    # برای ویندوز/DBT بعضی وقت‌ها بهتره
    return p.as_posix()
