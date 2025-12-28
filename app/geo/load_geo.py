from pathlib import Path
import geopandas as gpd
import streamlit as st

BASE = Path(__file__).resolve().parent
PROCESSED = BASE / "processed"

@st.cache_data(show_spinner=False)
def load_kommuner() -> gpd.GeoDataFrame:
    return gpd.read_parquet(PROCESSED / "kommuner.parquet")

@st.cache_data(show_spinner=False)
def load_lan() -> gpd.GeoDataFrame:
    return gpd.read_parquet(PROCESSED / "lan.parquet")
