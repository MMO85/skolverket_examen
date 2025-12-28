from __future__ import annotations

import os
from pathlib import Path
import geopandas as gpd


# -------------------------
# Paths
# -------------------------
ROOT = Path(__file__).resolve().parents[1]  # .../app
GEO_DIR = ROOT / "geo"
RAW_DIR = GEO_DIR / "raw"
OUT_DIR = GEO_DIR / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# Helpers
# -------------------------
def ensure_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ensure CRS is EPSG:4326 (lon/lat)."""
    if gdf.crs is None:
        return gdf.set_crs("EPSG:4326")
    return gdf.to_crs("EPSG:4326")


def fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Fix invalid geometries. buffer(0) is a common trick, but can be expensive.
    We only apply it when needed.
    """
    try:
        invalid_mask = ~gdf.is_valid
        if invalid_mask.any():
            gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)
    except Exception:
        # If is_valid fails for any reason, fall back to a cautious attempt
        gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


def simplify(gdf: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    gdf_s = gdf.copy()
    gdf_s["geometry"] = gdf_s["geometry"].simplify(tolerance, preserve_topology=True)
    return gdf_s


def pick_col(gdf: gpd.GeoDataFrame, candidates: list[str]) -> str | None:
    """Return first matching column name from candidates."""
    for c in candidates:
        if c in gdf.columns:
            return c
    return None


def save_outputs(gdf: gpd.GeoDataFrame, base_name: str) -> None:
    out_geojson = OUT_DIR / f"{base_name}_simplified.geojson"
    out_parquet = OUT_DIR / f"{base_name}.parquet"

    gdf.to_file(out_geojson, driver="GeoJSON")
    gdf.to_parquet(out_parquet, index=False)

    print(f"✅ {base_name}: {len(gdf)} features")
    print(f"   -> {out_geojson}")
    print(f"   -> {out_parquet}")
    print(f"   columns: {list(gdf.columns)}")


# -------------------------
# Main processors
# -------------------------
def process_kommuner(simplify_tolerance: float = 0.003) -> None:
    in_path = RAW_DIR / "kommuner.geojson"
    if not in_path.exists():
        raise FileNotFoundError(f"Missing file: {in_path}")

    gdf = gpd.read_file(in_path)
    gdf = ensure_wgs84(gdf)
    gdf = fix_geometries(gdf)

    # Try to map columns robustly across common datasets:
    # - name: kom_namn / kommun / name
    # - code: id / kommun_kod / kom_kod
    # - lan: lan_code / lan_kod / lan
    name_col = pick_col(gdf, ["kom_namn", "kommun", "name"])
    code_col = pick_col(gdf, ["id", "kommun_kod", "kom_kod", "komkod"])
    lan_col = pick_col(gdf, ["lan_code", "lan_kod", "lanskod", "lan"])

    if name_col is None or code_col is None:
        raise ValueError(
            "Unexpected columns in kommuner.geojson.\n"
            f"Columns found: {list(gdf.columns)}\n"
            "Need at least a municipality name + municipality code column.\n"
            "Expected one of name=[kom_namn, kommun, name] and code=[id, kommun_kod, kom_kod]."
        )

    # Standard columns used by Streamlit/dbt matching:
    gdf["kommun"] = gdf[name_col].astype(str).str.strip()
    gdf["kommun_kod"] = gdf[code_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(4)

    if lan_col is not None:
        gdf["lan_kod"] = gdf[lan_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(2)

    # Simplify and keep minimal set
    gdf_s = simplify(gdf, simplify_tolerance)

    keep = ["kommun", "kommun_kod", "geometry"]
    if "lan_kod" in gdf_s.columns:
        keep.insert(2, "lan_kod")  # kommun, kommun_kod, lan_kod, geometry

    gdf_s = gdf_s[keep]
    save_outputs(gdf_s, "kommuner")


def process_lan(simplify_tolerance: float = 0.003) -> None:
    in_path = RAW_DIR / "lan.geojson"
    if not in_path.exists():
        raise FileNotFoundError(f"Missing file: {in_path}")

    gdf = gpd.read_file(in_path)
    gdf = ensure_wgs84(gdf)
    gdf = fix_geometries(gdf)

    # Common variants:
    # - name: name / lan / region
    # - code: l_id / lan_kod / id
    name_col = pick_col(gdf, ["lan", "name", "region"])
    code_col = pick_col(gdf, ["lan_kod", "l_id", "id", "code"])

    if name_col is None or code_col is None:
        raise ValueError(
            "Unexpected columns in lan.geojson.\n"
            f"Columns found: {list(gdf.columns)}\n"
            "Need at least a county name + county code column.\n"
            "Expected one of name=[lan, name, region] and code=[lan_kod, l_id, id]."
        )

    gdf["lan"] = gdf[name_col].astype(str).str.strip()
    gdf["lan_kod"] = gdf[code_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(2)

    gdf_s = simplify(gdf, simplify_tolerance)
    gdf_s = gdf_s[["lan", "lan_kod", "geometry"]]
    save_outputs(gdf_s, "lan")


if __name__ == "__main__":
    process_kommuner(simplify_tolerance=0.003)
    process_lan(simplify_tolerance=0.003)
