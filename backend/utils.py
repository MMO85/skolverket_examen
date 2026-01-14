import pandas as pd

def pick_first_existing(cols: list[str], candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None

def pick_numeric_col(df: pd.DataFrame, preferred: list[str] | None = None) -> str | None:
    cols = list(df.columns)
    if preferred:
        p = pick_first_existing(cols, preferred)
        if p and pd.api.types.is_numeric_dtype(df[p]):
            return p

    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    return numeric_cols[0] if numeric_cols else None

def safe_filter(df: pd.DataFrame, col: str | None, value):
    if col and col in df.columns and value not in (None, "All"):
        return df[df[col] == value]
    return df
