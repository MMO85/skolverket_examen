from __future__ import annotations

from pathlib import Path
import os
import duckdb
import pandas as pd

DB_PATH = Path("csv_ingestion_pipeline.duckdb")  # ✅ فایل اصلی

# اگر خواستی دستی مشخص کنی (اختیاری):
# PowerShell:
#   $env:DBT_SCHEMA="csv_ingestion_pipeline"
# CMD:
#   set DBT_SCHEMA=csv_ingestion_pipeline
DBT_SCHEMA = os.getenv("DBT_SCHEMA", "").strip()

# cache برای اینکه هر بار دنبال schema نگردیم
_TABLE_SCHEMA_CACHE: dict[str, str] = {}


def _connect(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB not found: {DB_PATH.resolve()}")
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def query_df(sql: str) -> pd.DataFrame:
    with _connect(read_only=True) as con:
        return con.execute(sql).fetchdf()


def show_tables() -> pd.DataFrame:
    return query_df("SHOW ALL TABLES")


def _detect_schema_for_table(table_name: str) -> str:
    """
    اگر table بدون schema داده شد (مثلاً mart_xxx)، این تابع schema درست را پیدا می‌کند.
    اولویت:
      1) DBT_SCHEMA اگر ست شده باشد
      2) schemaهای رایج پروژه: csv_ingestion_pipeline, staging_data, main
      3) هر schema دیگری که در DB پیدا شود
    """
    t = table_name.strip()
    if t in _TABLE_SCHEMA_CACHE:
        return _TABLE_SCHEMA_CACHE[t]

    # schema های کاندید
    preferred = []
    if DBT_SCHEMA:
        preferred.append(DBT_SCHEMA)

    # از روی خطای شما معلومه این یکی مهمه
    preferred += ["csv_ingestion_pipeline", "staging_data", "main"]

    with _connect(read_only=True) as con:
        # همه schema هایی که این table داخلش هست
        rows = con.execute(
            """
            SELECT table_schema
            FROM information_schema.tables
            WHERE table_name = ?
            ORDER BY table_schema
            """,
            [t],
        ).fetchall()

    schemas_found = [r[0] for r in rows]

    if not schemas_found:
        # هیچ جا پیدا نشد
        raise duckdb.CatalogException(
            f"Table '{t}' not found in any schema. "
            f"Checked information_schema.tables."
        )

    # اگر preferred ها وجود داشتند، همون رو انتخاب کن
    for s in preferred:
        if s in schemas_found:
            _TABLE_SCHEMA_CACHE[t] = s
            return s

    # در غیر اینصورت اولین مورد پیدا شده
    _TABLE_SCHEMA_CACHE[t] = schemas_found[0]
    return schemas_found[0]


def qualify_table(table: str) -> str:
    """
    اگر schema داده شده بود، همان را برگردان.
    اگر بدون schema بود، schema صحیح را auto-detect می‌کند.
    """
    t = str(table).strip()
    if "." in t:
        return t  # already qualified (schema.table)
    schema = _detect_schema_for_table(t)
    return f"{schema}.{t}"


def table_info(table: str) -> pd.DataFrame:
    qt = qualify_table(table)
    return query_df(f"PRAGMA table_info('{qt}')")


def load_table(table: str, limit: int | None = None) -> pd.DataFrame:
    qt = qualify_table(table)
    sql = f"SELECT * FROM {qt}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return query_df(sql)


def distinct_values(table: str, col: str, limit: int = 500) -> list:
    qt = qualify_table(table)
    sql = f"""
        SELECT DISTINCT {col} AS v
        FROM {qt}
        WHERE {col} IS NOT NULL
        ORDER BY 1
        LIMIT {int(limit)}
    """
    df = query_df(sql)
    return df["v"].tolist() if not df.empty else []


def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    return _connect(read_only=read_only)
