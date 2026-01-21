from pathlib import Path
import duckdb
import pandas as pd

DB_PATH = Path("csv_ingestion_pipeline.duckdb")  # ✅ فایل اصلی

def _connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB not found: {DB_PATH.resolve()}")
    return duckdb.connect(str(DB_PATH), read_only=True)

def query_df(sql: str) -> pd.DataFrame:
    with _connect() as con:
        return con.execute(sql).fetchdf()

def show_tables() -> pd.DataFrame:
    return query_df("SHOW ALL TABLES")

def table_info(table: str) -> pd.DataFrame:
    # table should be schema-qualified, e.g. mart_parent_trend_ak9
    return query_df(f"PRAGMA table_info('{table}')")

def load_table(table: str, limit: int | None = None) -> pd.DataFrame:
    sql = f"SELECT * FROM {table}"
    if limit:
        sql += f" LIMIT {limit}"
    return query_df(sql)

def distinct_values(table: str, col: str, limit: int = 500) -> list:
    sql = f"""
        SELECT DISTINCT {col} AS v
        FROM {table}
        WHERE {col} IS NOT NULL
        ORDER BY 1
        LIMIT {limit}
    """
    df = query_df(sql)
    return df["v"].tolist() if not df.empty else []

def get_connection():
    return _connect()
