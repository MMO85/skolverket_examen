from pathlib import Path
import os
import subprocess
import sys

import dlt
import duckdb

# Base directory (repo root) and raw data folder
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "raw_data"
DB_PATH = str(BASE_DIR / "csv_ingestion_pipeline.duckdb")

# dbt project directory (where dbt_project.yml + profiles.yml live)
DBT_DIR = BASE_DIR / "dbt_project"


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


def run_dbt():
    """
    Runs dbt run + dbt test using the local profiles.yml inside DBT_DIR.

    Key detail: uses sys.executable so we always run dbt with the SAME python/venv
    that is executing this script (avoids "No module named dbt").
    """
    if not DBT_DIR.exists():
        raise FileNotFoundError(f"dbt project dir not found: {DBT_DIR}")

    # Sanity checks to catch misconfig early
    dbt_project_yml = DBT_DIR / "dbt_project.yml"
    profiles_yml = DBT_DIR / "profiles.yml"
    if not dbt_project_yml.exists():
        raise FileNotFoundError(f"Missing dbt_project.yml: {dbt_project_yml}")
    if not profiles_yml.exists():
        raise FileNotFoundError(f"Missing profiles.yml: {profiles_yml}")

    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(DBT_DIR)

    # Optional: silence the runpy warning noise
    env.setdefault("PYTHONWARNINGS", "ignore")

    # Use the venv python (same interpreter as running this script)
    py = sys.executable

    print(f"Running dbt with python: {py}")
    print(f"DBT_PROFILES_DIR={env['DBT_PROFILES_DIR']}")

    # Run dbt (show output, fail fast on errors)
    subprocess.run(
        [py, "-m", "dbt.cli.main", "run"],
        cwd=str(DBT_DIR),
        check=True,
        env=env,
    )
    subprocess.run(
        [py, "-m", "dbt.cli.main", "test"],
        cwd=str(DBT_DIR),
        check=True,
        env=env,
    )


def run_pipeline() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="csv_ingestion_pipeline",
        destination="duckdb",
        dataset_name="staging_data",
        dev_mode=False,
    )

    load_info = pipeline.run(skolverket_raw_csv())
    print(load_info)

    # Sync raw_data: keep only the latest load
    keep_only_latest_load()
    print("✅ raw_data synced: kept only latest load")

    # Build stg/silver/marts + run tests
    run_dbt()
    print("✅ dbt run + test complete")


if __name__ == "__main__":
    run_pipeline()
