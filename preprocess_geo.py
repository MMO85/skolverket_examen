import geopandas as gpd
from pathlib import Path

RAW_DIR = Path("app/geo/raw")
OUT_DIR = Path("app/geo/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def simplify(infile: Path, out_geojson: Path, out_parquet: Path | None = None, tolerance=0.005):
    gdf = gpd.read_file(infile)

    # فقط ستون‌های لازم را نگه دار (اسم‌ها ممکن است در فایل تو فرق کند)
    # یک بار print(gdf.columns) بزن اگر خواستی دقیقش کنی
    keep_cols = [c for c in gdf.columns if c.lower() in ("name", "namn", "kommun", "lan", "id", "kommun_kod", "lan_kod", "geometry")]
    if "geometry" not in keep_cols:
        keep_cols.append("geometry")
    gdf = gdf[keep_cols] if keep_cols else gdf[["geometry"]]

    # ساده‌سازی هندسه برای کم‌حجم شدن
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=tolerance, preserve_topology=True)

    # خروجی GeoJSON سبک
    gdf.to_file(out_geojson, driver="GeoJSON")

    # خروجی سریع‌تر برای لود (اختیاری ولی عالی)
    if out_parquet is not None:
        gdf.to_parquet(out_parquet, index=False)

if __name__ == "__main__":
    simplify(
        RAW_DIR / "kommuner.geojson",
        OUT_DIR / "kommuner_simplified.geojson",
        OUT_DIR / "kommuner.parquet",
        tolerance=0.003,   # اگر هنوز بزرگ بود، کمی بیشترش کن مثل 0.006
    )

    simplify(
        RAW_DIR / "lan.geojson",
        OUT_DIR / "lan_simplified.geojson",
        None,
        tolerance=0.005,
    )

    print("Done. Files written to app/geo/processed/")
