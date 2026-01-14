# backend/inspect_db.py
from backend.db import query_df
import pandas as pd

pd.set_option("display.max_rows", 300)
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 120)

df = query_df("SHOW ALL TABLES")

print("\n=== ALL TABLES (schema.name) ===")
print(df[["schema", "name"]].sort_values(["schema", "name"]).to_string(index=False))

print("\n=== TABLE COUNT BY SCHEMA ===")
print(df.groupby("schema")["name"].count().to_string())

print("\n=== TABLES THAT LOOK LIKE MART ===")
mart = df[df["name"].str.contains("mart", case=False, na=False)]
print(mart[["schema", "name"]].sort_values(["schema", "name"]).to_string(index=False))
