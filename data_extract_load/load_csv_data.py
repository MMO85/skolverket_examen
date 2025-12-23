from pathlib import Path
import dlt

# مسیر فولدر CSV ها
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "raw_data"

@dlt.resource(
    name="raw_data",
    write_disposition="append"
)
def skolverket_raw_csv():
    """
    Reads all Skolverket CSV files as raw text lines.
    Each row = one raw line from file + source_file
    """
    for csv_file in RAW_DATA_DIR.glob("*.csv"):
        print(f"Loading file: {csv_file.name}")

        # ✅ utf-8-sig برای حذف BOM (خیلی مهم)
        with open(csv_file, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                raw_line = line.strip("\n").strip("\r")

                # اگر خط کاملاً خالی بود ردش کن
                if raw_line.strip() == "":
                    continue

                yield {
                    "raw_line": raw_line,
                    "source_file": csv_file.name
                }


def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="csv_ingestion_pipeline",
        destination="duckdb",
        dataset_name="main"
    )

    load_info = pipeline.run(skolverket_raw_csv())
    print(load_info)


if __name__ == "__main__":
    run_pipeline()
