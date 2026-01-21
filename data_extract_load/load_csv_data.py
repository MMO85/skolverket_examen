from pathlib import Path
import os
import subprocess
import sys

import dlt
import duckdb

from config import BASE_DIR, RAW_DATA_DIR, DB_FILE, DBT_DIR, as_posix
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

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


def keep_only_latest_load() -> None:
    """
    Keep only latest _dlt_load_id in staging_data.raw_data (sync DB to latest ingestion).
    """
    db_path = as_posix(DB_FILE)

    con = duckdb.connect(db_path)
    con.execute("""
        delete from staging_data.raw_data
        where _dlt_load_id <> (select max(_dlt_load_id) from staging_data.raw_data);
    """)
    con.close()


def run_dbt() -> None:
    """
    Runs dbt run + dbt test using the local profiles.yml inside DBT_DIR.

    Key details:
    - uses sys.executable so we run dbt with the same python/venv
    - sets DBT_PROFILES_DIR to dbt_project/
    - sets DUCKDB_PATH to the repo DB file so dbt always points to the right database
    - runs with cwd=repo root so relative paths resolve correctly
    """
    if not DBT_DIR.exists():
        raise FileNotFoundError(f"dbt project dir not found: {DBT_DIR}")

    # sanity checks
    dbt_project_yml = DBT_DIR / "dbt_project.yml"
    profiles_yml = DBT_DIR / "profiles.yml"
    if not dbt_project_yml.exists():
        raise FileNotFoundError(f"Missing dbt_project.yml: {dbt_project_yml}")
    if not profiles_yml.exists():
        raise FileNotFoundError(f"Missing profiles.yml: {profiles_yml}")

    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = as_posix(DBT_DIR)
    env["DUCKDB_PATH"] = as_posix(DB_FILE)  # ✅ single source of truth for db path
    env.setdefault("PYTHONWARNINGS", "ignore")

    py = sys.executable

    print(f"Running dbt with python: {py}")
    print(f"DBT_PROFILES_DIR={env['DBT_PROFILES_DIR']}")
    print(f"DUCKDB_PATH={env['DUCKDB_PATH']}")

    # IMPORTANT: run dbt from repo root (not inside dbt_project)
    repo_root = as_posix(BASE_DIR)

    subprocess.run(
        [py, "-m", "dbt.cli.main", "run"],
        cwd=repo_root,
        check=True,
        env=env,
    )
    subprocess.run(
        [py, "-m", "dbt.cli.main", "test"],
        cwd=repo_root,
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
