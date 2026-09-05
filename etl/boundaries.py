"""Process Indonesia administrative boundaries for GeoTani.

1. Extracts village-level polygons (ADM4) for the 3 pilot provinces:
   - Lampung (ID18)
   - Jawa Timur / East Java (ID35)
   - Sulawesi Selatan / South Sulawesi (ID73)
2. Extracts regency-level polygons (ADM2) for the rest of Indonesia as coarse boundaries.
3. Fixes any invalid geometries.
4. Outputs the unified boundary layer to data/processed/boundaries/geotani_boundaries.gpkg.
"""

import glob
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.validation import make_valid

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "boundaries"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "boundaries"

# BPS / HDX Province P-Codes & Names for Pilot
PILOT_PROVINCES = {
    "ID18": "Lampung",
    "ID35": "Jawa Timur",
    "ID73": "Sulawesi Selatan",
}


def fix_geometries(geom):
    """Ensure geometry is valid MultiPolygon."""
    if not geom.is_valid:
        geom = make_valid(geom)
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom


def find_shapefile(level_num: int):
    """Find shapefile for a given admin level (e.g., 4 for village, 2 for regency)."""
    patterns = [
        str(DATA_RAW / f"*admin{level_num}*.shp"),
        str(DATA_RAW / f"*adm{level_num}*.shp"),
        str(DATA_RAW / f"*ADM{level_num}*.shp"),
        str(DATA_RAW / f"*Admin{level_num}*.shp"),
    ]
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No shapefile found for admin level {level_num} in {DATA_RAW}")


def get_col(df, *candidates):
    """Helper to find the first matching column case-insensitively."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process administrative boundaries.")
    parser.add_argument("--force", action="store_true", help="Force re-processing of boundaries.")
    args = parser.parse_args()

    out_file = DATA_PROCESSED / "geotani_boundaries.gpkg"
    if not args.force and out_file.exists() and out_file.stat().st_size > 1000000:
        print(f"✓ Found processed boundaries: {out_file.name}. Skipping.")
        return

    print(f"Searching for shapefiles in {DATA_RAW}...")
    adm4_path = find_shapefile(4)
    adm2_path = find_shapefile(2)

    print(f"Loading ADM4 villages: {Path(adm4_path).name}")
    gdf_adm4 = gpd.read_file(adm4_path)

    print(f"Loading ADM2 regencies: {Path(adm2_path).name}")
    gdf_adm2 = gpd.read_file(adm2_path)

    # Detect province code / name column in ADM4
    pcode4_col = get_col(gdf_adm4, "adm1_pcode", "ADM1_PCODE", "PCODE1")
    name4_col = get_col(gdf_adm4, "adm1_name", "ADM1_EN", "ADM1_NAME", "PROVINSI")

    # Detect province code / name column in ADM2
    pcode2_col = get_col(gdf_adm2, "adm1_pcode", "ADM1_PCODE", "PCODE1")
    name2_col = get_col(gdf_adm2, "adm1_name", "ADM1_EN", "ADM1_NAME", "PROVINSI")

    pilot_codes = set(PILOT_PROVINCES.keys())
    pilot_names = {"Lampung", "Jawa Timur", "East Java", "Sulawesi Selatan", "South Sulawesi"}

    if pcode4_col:
        print(f"Using {pcode4_col} for ADM4 pilot filtering.")
        pilot_mask_4 = gdf_adm4[pcode4_col].isin(pilot_codes)
    elif name4_col:
        print(f"Using {name4_col} for ADM4 pilot filtering.")
        pilot_mask_4 = gdf_adm4[name4_col].isin(pilot_names)
    else:
        raise ValueError("Cannot identify province identifier in ADM4 dataset.")

    if pcode2_col:
        pilot_mask_2 = gdf_adm2[pcode2_col].isin(pilot_codes)
    elif name2_col:
        pilot_mask_2 = gdf_adm2[name2_col].isin(pilot_names)
    else:
        raise ValueError("Cannot identify province identifier in ADM2 dataset.")

    # 1. Filter pilot villages
    print("Filtering pilot villages (ADM4)...")
    pilot_villages = gdf_adm4[pilot_mask_4].copy()

    # 2. Filter coarse boundaries (rest of Indonesia)
    print("Filtering coarse nationwide boundaries (ADM2)...")
    coarse_regions = gdf_adm2[~pilot_mask_2].copy()

    # Standardize ADM4
    pcode_col = get_col(pilot_villages, "adm4_pcode", "ADM4_PCODE")
    name_col = get_col(pilot_villages, "adm4_name", "ADM4_EN", "ADM4_NAME")
    kec_col = get_col(pilot_villages, "adm3_name", "ADM3_EN", "ADM3_NAME")
    kab_col = get_col(pilot_villages, "adm2_name", "ADM2_EN", "ADM2_NAME")
    prov_col = get_col(pilot_villages, "adm1_name", "ADM1_EN", "ADM1_NAME")

    fallback_pcodes = [f"ID_{i}" for i in range(len(pilot_villages))]
    pilot_df = pd.DataFrame(
        {
            "adm_pcode": pilot_villages[pcode_col] if pcode_col else fallback_pcodes,
            "name": pilot_villages[name_col] if name_col else "",
            "kecamatan": pilot_villages[kec_col] if kec_col else "",
            "kabupaten": pilot_villages[kab_col] if kab_col else "",
            "province": pilot_villages[prov_col] if prov_col else "",
            "resolution": "village",
            "geometry": pilot_villages.geometry,
        }
    )

    # Standardize ADM2
    pcode2_col = get_col(coarse_regions, "adm2_pcode", "ADM2_PCODE")
    name2_col = get_col(coarse_regions, "adm2_name", "ADM2_EN", "ADM2_NAME")
    prov2_col = get_col(coarse_regions, "adm1_name", "ADM1_EN", "ADM1_NAME")

    fallback_c_pcodes = [f"ID_C_{i}" for i in range(len(coarse_regions))]
    coarse_df = pd.DataFrame(
        {
            "adm_pcode": coarse_regions[pcode2_col] if pcode2_col else fallback_c_pcodes,
            "name": coarse_regions[name2_col] if name2_col else "",
            "kecamatan": None,
            "kabupaten": coarse_regions[name2_col] if name2_col else "",
            "province": coarse_regions[prov2_col] if prov2_col else "",
            "resolution": "coarse",
            "geometry": coarse_regions.geometry,
        }
    )

    print("Combining datasets...")
    combined = gpd.GeoDataFrame(
        pd.concat([pilot_df, coarse_df], ignore_index=True), crs=gdf_adm4.crs
    )

    print("Validating and fixing geometries...")
    invalid_mask = ~combined.is_valid
    invalid_count = int(invalid_mask.sum())
    combined["geometry"] = combined["geometry"].apply(fix_geometries)
    print(f"Fixed {invalid_count} invalid geometries.")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_file = DATA_PROCESSED / "geotani_boundaries.gpkg"
    print(f"Saving to {out_file}...")
    combined.to_file(out_file, driver="GPKG")

    print("\n" + "=" * 50)
    print("--- Boundary Processing Summary ---")
    print(f"Total features: {len(combined)}")
    print(f"Pilot villages count: {len(pilot_df)}")
    print("Village features by province:")
    print(pilot_df["province"].value_counts().to_string())
    print(f"Coarse kabupaten count: {len(coarse_df)}")
    print(f"Output file: {out_file} ({out_file.stat().st_size / (1024*1024):.2f} MB)")
    print("=" * 50)


if __name__ == "__main__":
    main()
