"""Zonal statistics and spatial feature extraction pipeline for TaniScope.

Extracts environmental factors for each village polygon:
  1. Climate: Annual Mean Temp (°C) and Annual Rainfall (mm) from WorldClim v2.1
  2. Soil: pH, Clay %, Sand %, SOC (g/kg) from ISRIC SoilGrids v2.0
  3. Terrain: Elevation (m) and Slope (degrees) from Copernicus 30m Global DEM
  4. Accessibility: Centroid distance (meters) to road networks from OpenStreetMap
"""

from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import rasterstats
from shapely.strtree import STRtree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

CLIMATE_DIR = DATA_PROCESSED / "climate"
SOIL_DIR = DATA_PROCESSED / "soil"
ELEV_DIR = DATA_PROCESSED / "elevation"
OSM_DIR = DATA_RAW / "osm"
BOUNDARIES_GPKG = DATA_PROCESSED / "boundaries" / "taniscope_boundaries.gpkg"

PROVINCE_ELEV_MAP = {
    "Lampung": "lampung",
    "Jawa Timur": "east_java",
    "Sulawesi Selatan": "south_sulawesi",
}

PROVINCE_OSM_MAP = {
    "Lampung": OSM_DIR / "sumatra" / "gis_osm_roads_free_1.shp",
    "Jawa Timur": OSM_DIR / "java" / "gis_osm_roads_free_1.shp",
    "Sulawesi Selatan": OSM_DIR / "sulawesi" / "gis_osm_roads_free_1.shp",
}


def extract_climate_stats(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Extract temperature and rainfall from WorldClim rasters."""
    print("Extracting climate zonal statistics (WorldClim)...")
    temp_raster = CLIMATE_DIR / "wc2.1_2.5m_bio_1.tif"
    rain_raster = CLIMATE_DIR / "wc2.1_2.5m_bio_12.tif"

    if not temp_raster.exists() or not rain_raster.exists():
        raise FileNotFoundError(f"Climate rasters missing in {CLIMATE_DIR}")

    # WorldClim is in EPSG:4326
    gdf_4326 = gdf.to_crs(epsg=4326)

    temp_stats = rasterstats.zonal_stats(
        gdf_4326,
        str(temp_raster),
        stats="median",
        all_touched=True,
        nodata=-3.4e38,
    )
    rain_stats = rasterstats.zonal_stats(
        gdf_4326,
        str(rain_raster),
        stats="median",
        all_touched=True,
        nodata=-3.4e38,
    )

    temp_values = [s["median"] if s["median"] is not None else 26.0 for s in temp_stats]
    rain_values = [s["median"] if s["median"] is not None else 2000.0 for s in rain_stats]

    return pd.DataFrame(
        {
            "temp_c": temp_values,
            "rainfall_mm": rain_values,
        },
        index=gdf.index,
    )


def extract_soil_stats(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Extract pH, Clay %, Sand %, SOC from SoilGrids rasters."""
    print("Extracting soil zonal statistics (SoilGrids v2.0)...")
    ph_raster = SOIL_DIR / "phh2o_0-5cm_indonesia.tif"
    clay_raster = SOIL_DIR / "clay_0-5cm_indonesia.tif"
    sand_raster = SOIL_DIR / "sand_0-5cm_indonesia.tif"
    soc_raster = SOIL_DIR / "soc_0-5cm_indonesia.tif"

    if not ph_raster.exists():
        raise FileNotFoundError(f"SoilGrids rasters missing in {SOIL_DIR}")

    with rasterio.open(ph_raster) as src:
        soil_crs = src.crs

    gdf_soil_crs = gdf.to_crs(soil_crs)

    print("  - Processing Soil pH...")
    ph_stats = rasterstats.zonal_stats(
        gdf_soil_crs, str(ph_raster), stats="median", all_touched=True, nodata=-32768
    )
    print("  - Processing Clay content...")
    clay_stats = rasterstats.zonal_stats(
        gdf_soil_crs, str(clay_raster), stats="median", all_touched=True, nodata=-32768
    )
    print("  - Processing Sand content...")
    sand_stats = rasterstats.zonal_stats(
        gdf_soil_crs, str(sand_raster), stats="median", all_touched=True, nodata=-32768
    )
    print("  - Processing Soil Organic Carbon...")
    soc_stats = rasterstats.zonal_stats(
        gdf_soil_crs, str(soc_raster), stats="median", all_touched=True, nodata=-32768
    )

    ph_values = [s["median"] / 10.0 if s["median"] is not None else 6.0 for s in ph_stats]
    clay_values = [s["median"] / 10.0 if s["median"] is not None else 30.0 for s in clay_stats]
    sand_values = [s["median"] / 10.0 if s["median"] is not None else 35.0 for s in sand_stats]
    soc_values = [s["median"] / 10.0 if s["median"] is not None else 25.0 for s in soc_stats]

    return pd.DataFrame(
        {
            "soil_ph": ph_values,
            "clay_pct": clay_values,
            "sand_pct": sand_values,
            "soc_g_kg": soc_values,
        },
        index=gdf.index,
    )


def extract_terrain_stats(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Extract Elevation and Slope per province from Copernicus 30m DEM."""
    print("Extracting terrain zonal statistics (Copernicus 30m DEM & Slope)...")
    elev_series = pd.Series(index=gdf.index, dtype=np.float64)
    slope_series = pd.Series(index=gdf.index, dtype=np.float64)

    gdf_4326 = gdf.to_crs(epsg=4326)

    for prov_name, slug in PROVINCE_ELEV_MAP.items():
        prov_mask = gdf_4326["province"] == prov_name
        if not prov_mask.any():
            continue

        prov_gdf = gdf_4326[prov_mask]
        dem_file = ELEV_DIR / f"{slug}_dem.tif"
        slope_file = ELEV_DIR / f"{slug}_slope.tif"

        if dem_file.exists() and slope_file.exists():
            print(f"  - Processing DEM & Slope for {prov_name} ({len(prov_gdf)} features)...")
            dem_stats = rasterstats.zonal_stats(
                prov_gdf, str(dem_file), stats="median", all_touched=True, nodata=-9999
            )
            slope_stats = rasterstats.zonal_stats(
                prov_gdf, str(slope_file), stats="median", all_touched=True, nodata=-9999
            )

            elev_vals = [s["median"] if s["median"] is not None else 100.0 for s in dem_stats]
            slope_vals = [s["median"] if s["median"] is not None else 3.0 for s in slope_stats]

            elev_series.loc[prov_mask] = elev_vals
            slope_series.loc[prov_mask] = slope_vals
        else:
            print(f"  - Warning: Elevation files missing for {prov_name}. Using default lowlands.")
            elev_series.loc[prov_mask] = 100.0
            slope_series.loc[prov_mask] = 3.0

    elev_series.fillna(100.0, inplace=True)
    slope_series.fillna(3.0, inplace=True)

    return pd.DataFrame(
        {
            "elevation_m": np.clip(elev_series.values, 0.0, 4500.0),
            "slope_deg": np.clip(slope_series.values, 0.0, 90.0),
        },
        index=gdf.index,
    )


def extract_road_distances(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Calculate distance in meters from each village centroid to the nearest OSM road."""
    print("Calculating accessibility distances (OpenStreetMap Road Network)...")
    dist_series = pd.Series(index=gdf.index, dtype=np.float64)

    gdf_3857 = gdf.to_crs(epsg=3857)
    centroids_3857 = gdf_3857.geometry.centroid

    drivable_fclasses = {
        "motorway",
        "trunk",
        "primary",
        "secondary",
        "tertiary",
        "unclassified",
        "residential",
        "living_street",
        "service",
    }

    for prov_name, roads_path in PROVINCE_OSM_MAP.items():
        prov_mask = gdf["province"] == prov_name
        if not prov_mask.any():
            continue

        prov_indices = gdf[prov_mask].index
        if roads_path.exists():
            n_pts = len(prov_indices)
            print(f"  - Querying nearest road network for {prov_name} ({n_pts} villages)...")
            try:
                roads_gdf = gpd.read_file(roads_path)
                roads_filtered = roads_gdf[roads_gdf["fclass"].isin(drivable_fclasses)]
                roads_3857 = roads_filtered.to_crs(epsg=3857)

                tree = STRtree(roads_3857.geometry.values)
                prov_centroids = centroids_3857.loc[prov_indices]

                dists = []
                for pt in prov_centroids:
                    nearest_idx = tree.nearest(pt)
                    nearest_geom = roads_3857.geometry.values[nearest_idx]
                    dists.append(float(pt.distance(nearest_geom)))

                dist_series.loc[prov_indices] = dists
            except Exception as e:
                print(f"    Warning: Error calculating road distance for {prov_name}: {e}")
                dist_series.loc[prov_indices] = 3000.0
        else:
            print(f"    Road shapefile not found at {roads_path}. Using default 3km.")
            dist_series.loc[prov_indices] = 3000.0

    dist_series.fillna(3000.0, inplace=True)

    return pd.DataFrame(
        {
            "dist_road_m": dist_series.values,
        },
        index=gdf.index,
    )


def extract_all_factors(
    boundaries_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> gpd.GeoDataFrame:
    """Run full feature extraction pipeline across all villages."""
    gpkg_path = boundaries_path or BOUNDARIES_GPKG
    out_file = output_path or (DATA_PROCESSED / "village_environmental_factors.gpkg")

    if not gpkg_path.exists():
        raise FileNotFoundError(f"Boundaries GPKG not found: {gpkg_path}")

    print("=" * 60)
    print(f"Loading boundaries from {gpkg_path.name}...")
    gdf = gpd.read_file(gpkg_path)
    village_count = len(gdf[gdf["resolution"] == "village"])
    print(f"Total features to process: {len(gdf)} ({village_count} pilot villages)")
    print("=" * 60)

    # 1. Climate
    df_climate = extract_climate_stats(gdf)
    # 2. Soil
    df_soil = extract_soil_stats(gdf)
    # 3. Terrain
    df_terrain = extract_terrain_stats(gdf)
    # 4. Accessibility
    df_access = extract_road_distances(gdf)

    # Combine metadata, geometries, and extracted features
    factors_df = pd.concat([df_climate, df_soil, df_terrain, df_access], axis=1)
    meta_cols = ["adm_pcode", "name", "kecamatan", "kabupaten", "province", "resolution"]

    result_gdf = gpd.GeoDataFrame(
        pd.concat([gdf[meta_cols], factors_df], axis=1),
        geometry=gdf.geometry,
        crs=gdf.crs,
    )

    print(f"\nSaving extracted factors to {out_file}...")
    result_gdf.to_file(out_file, driver="GPKG")

    csv_file = DATA_PROCESSED / "village_environmental_factors.csv"
    result_gdf.drop(columns="geometry").to_csv(csv_file, index=False)
    print(f"Saved tabular factors to {csv_file}")

    print("\n--- Environmental Factors Summary ---")
    print(factors_df.describe().round(2).to_string())
    print("=" * 60)

    return result_gdf


if __name__ == "__main__":
    extract_all_factors()
