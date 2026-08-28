import os
import glob
from pathlib import Path
import geopandas as gpd
from shapely.validation import make_valid
from shapely.geometry import Polygon, MultiPolygon

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "boundaries"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "boundaries"

PILOT_PROVINCES = {
    "Lampung": "ID-LA",
    "Sulawesi Selatan": "ID-SN",
    "Jawa Timur": "ID-JI",
}

def fix_geometries(geom):
    if not geom.is_valid:
        geom = make_valid(geom)
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom

def find_shapefile(level):
    search_pattern = str(DATA_RAW / f"*{level}*.shp")
    matches = glob.glob(search_pattern)
    if not matches:
        raise FileNotFoundError(f"No shapefile found for {level} in {DATA_RAW}")
    return matches[0]

def main():
    print(f"Reading ADM4 and ADM2 shapefiles from {DATA_RAW}...")
    adm4_path = find_shapefile("adm4")
    adm2_path = find_shapefile("adm2")
    
    print(f"Loading ADM4: {adm4_path}")
    gdf_adm4 = gpd.read_file(adm4_path)
    
    print(f"Loading ADM2: {adm2_path}")
    gdf_adm2 = gpd.read_file(adm2_path)

    # Detect matching column
    pcode_col = "ADM1_PCODE" if "ADM1_PCODE" in gdf_adm4.columns else None
    name_col = "ADM1_EN" if "ADM1_EN" in gdf_adm4.columns else None
    
    if pcode_col:
        print(f"Using {pcode_col} for province matching.")
        pilot_mask = gdf_adm4[pcode_col].isin(PILOT_PROVINCES.values())
        pilot_mask_adm2 = gdf_adm2[pcode_col].isin(PILOT_PROVINCES.values())
    elif name_col:
        print(f"Using {name_col} for province matching.")
        names = ["Lampung", "South Sulawesi", "Sulawesi Selatan", "East Java", "Jawa Timur"]
        pilot_mask = gdf_adm4[name_col].isin(names)
        pilot_mask_adm2 = gdf_adm2[name_col].isin(names)
    else:
        raise ValueError("Could not find ADM1_PCODE or ADM1_EN in shapefile.")

    # Process ADM4 (villages in pilot provinces)
    print("Filtering pilot villages (ADM4)...")
    pilot_villages = gdf_adm4[pilot_mask].copy()
    pilot_villages["resolution"] = "village"
    
    # Process ADM2 (coarse nationwide, excluding pilot provinces)
    print("Filtering coarse nationwide boundaries (ADM2)...")
    coarse_regions = gdf_adm2[~pilot_mask_adm2].copy()
    coarse_regions["resolution"] = "coarse"

    # Standardize columns
    def standardize_cols(gdf, level):
        df = gdf.copy()
        if level == "adm4":
            df["adm_pcode"] = df.get("ADM4_PCODE", df.get("ADM4_EN", ""))
            df["name"] = df.get("ADM4_EN", "")
            df["kecamatan"] = df.get("ADM3_EN", "")
        else:
            df["adm_pcode"] = df.get("ADM2_PCODE", df.get("ADM2_EN", ""))
            df["name"] = df.get("ADM2_EN", "")
            df["kecamatan"] = None
            
        df["kabupaten"] = df.get("ADM2_EN", "")
        df["province"] = df.get("ADM1_EN", "")
        
        return df[["adm_pcode", "name", "kecamatan", "kabupaten", "province", "resolution", "geometry"]]

    pilot_villages_std = standardize_cols(pilot_villages, "adm4")
    coarse_regions_std = standardize_cols(coarse_regions, "adm2")

    print("Combining datasets...")
    combined = gpd.GeoDataFrame(
        pd.concat([pilot_villages_std, coarse_regions_std], ignore_index=True),
        crs=gdf_adm4.crs
    )

    print("Validating and fixing geometries...")
    invalid_count = (~combined.is_valid).sum()
    combined["geometry"] = combined["geometry"].apply(fix_geometries)
    print(f"Fixed {invalid_count} invalid geometries.")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_file = DATA_PROCESSED / "taniscope_boundaries.gpkg"
    print(f"Saving to {out_file}...")
    combined.to_file(out_file, driver="GPKG")

    print("\n--- Summary ---")
    print(f"Total features: {len(combined)}")
    print("Village features per province:")
    print(pilot_villages_std["province"].value_counts())
    print(f"Coarse kabupaten features: {len(coarse_regions_std)}")
    print(f"Invalid geometries fixed: {invalid_count}")
    print(f"Output file size: {out_file.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    import pandas as pd
    main()
