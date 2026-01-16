from pathlib import Path
import dlt
import duckdb

# Base directory (repo root) and raw data folder
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "raw_data"
DB_PATH = str(BASE_DIR / "csv_ingestion_pipeline.duckdb")


@dlt.resource(name="raw_data", write_disposition="append")
def skolverket_raw_csv():
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")

    for csv_file in sorted(RAW_DATA_DIR.glob("*.csv")):
        print(f"Loading file: {csv_file.name}")
        with csv_file.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                raw_line = line.strip("\n").strip("\r")
                if not raw_line.strip():
                    continue
                yield {"raw_line": raw_line, "source_file": csv_file.name}


def keep_only_latest_load():
    con = duckdb.connect(DB_PATH)
    con.execute("""
        delete from staging_data.raw_data
        where _dlt_load_id <> (select max(_dlt_load_id) from staging_data.raw_data);
    """)
    con.close()


def run_pipeline() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="csv_ingestion_pipeline",
        destination="duckdb",
        dataset_name="staging_data",
        dev_mode=False,
    )

    load_info = pipeline.run(skolverket_raw_csv())
    print(load_info)

    # 👇 این خط کلیدی است: دیتابیس را دقیقاً با آخرین اجرای فعلی sync می‌کند
    keep_only_latest_load()
    print("✅ raw_data synced: kept only latest load")


if __name__ == "__main__":
    run_pipeline()
