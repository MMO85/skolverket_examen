from pathlib import Path
import dlt

# Base directory (repo root) and raw data folder
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "raw_data"


@dlt.resource(name="raw_data", write_disposition="append")
def skolverket_raw_csv():
    """
    Read all Skolverket CSV files as raw text lines.

    Each yielded item represents one raw line from a CSV file plus metadata
    about the source file.
    """
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")

    for csv_file in sorted(RAW_DATA_DIR.glob("*.csv")):
        print(f"Loading file: {csv_file.name}")

        # Use utf-8-sig to remove BOM if present (important for some CSV exports)
        with csv_file.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                raw_line = line.strip("\n").strip("\r")

                # Skip completely empty lines
                if not raw_line.strip():
                    continue

                yield {
                    "raw_line": raw_line,
                    "source_file": csv_file.name,
                }


def run_pipeline() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="csv_ingestion_pipeline",
        destination="duckdb",
        dataset_name="staging_data",
        dev_mode=False,
    )

    load_info = pipeline.run(skolverket_raw_csv())
    print(load_info)


if __name__ == "__main__":
    run_pipeline()
