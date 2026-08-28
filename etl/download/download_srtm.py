"""Download 30m Global DEM tiles and compute slope rasters for pilot provinces.

Uses the Copernicus GLO-30 (30m) Global DEM hosted on AWS Open Data.
Provides 30m resolution, void-filled elevation data with direct public HTTPS downloads.

For each pilot province (Lampung, East Java, South Sulawesi):
  1. Downloads 1x1 degree 30m DEM tiles from AWS S3
  2. Merges tiles using gdalwarp (or rasterio.merge if gdalwarp is unavailable)
  3. Computes slope raster using gdaldem (or numpy gradient if gdaldem is unavailable)
"""

import math
import subprocess
import sys
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "elevation" / "tiles"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "elevation"

# Pilot province bounding boxes
PILOT_PROVINCES = {
    "lampung": {"west": 103, "east": 106, "south": -6, "north": -3},
    "east_java": {"west": 110, "east": 115, "south": -9, "north": -6},
    "south_sulawesi": {"west": 118, "east": 122, "south": -7, "north": -1},
}


def get_copernicus_tile_info(lat: int, lon: int):
    """Generate Copernicus 30m DEM tile filename and AWS HTTPS URL."""
    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"
    lat_str = f"{lat_prefix}{abs(lat):02d}"
    lon_str = f"{lon_prefix}{abs(lon):03d}"
    tile_name = f"Copernicus_DSM_COG_10_{lat_str}_00_{lon_str}_00_DEM"
    filename = f"{tile_name}.tif"
    url = f"https://copernicus-dem-30m.s3.amazonaws.com/{tile_name}/{filename}"
    return filename, url


def generate_tile_coords(bbox: dict):
    """Generate (lat, lon) integer coordinates covering a bounding box."""
    min_lon = math.floor(bbox["west"])
    max_lon = math.ceil(bbox["east"]) - 1
    min_lat = math.floor(bbox["south"])
    max_lat = math.ceil(bbox["north"]) - 1

    coords = []
    for lat in range(min_lat, max_lat + 1):
        for lon in range(min_lon, max_lon + 1):
            coords.append((lat, lon))
    return coords


def merge_and_slope_with_rasterio(downloaded_tifs, dem_output, slope_output):
    """Fallback merge and slope computation using pure Python (rasterio + numpy)."""
    import numpy as np
    import rasterio
    from rasterio.merge import merge

    print("Using rasterio + numpy for merging and slope calculation...")
    src_files = [rasterio.open(f) for f in downloaded_tifs]
    mosaic, out_trans = merge(src_files)
    out_meta = src_files[0].meta.copy()
    for src in src_files:
        src.close()

    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "compress": "deflate",
    })

    with rasterio.open(dem_output, "w", **out_meta) as dest:
        dest.write(mosaic)
    print(f"DEM merged: {dem_output}")

    # Compute slope using numpy gradient (degrees)
    elev = mosaic[0].astype(np.float32)
    # Resolution in meters approximation (1 deg ~ 111,320 meters at equator)
    res_x = abs(out_trans[0]) * 111320.0
    res_y = abs(out_trans[4]) * 111320.0

    dy, dx = np.gradient(elev, res_y, res_x)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad).astype(np.float32)

    with rasterio.open(slope_output, "w", **out_meta) as dest:
        dest.write(slope_deg[np.newaxis, :, :])
    print(f"Slope raster generated: {slope_output}")


def download_and_process_dem():
    has_gdal_cli = False
    try:
        subprocess.run(["gdaldem", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        has_gdal_cli = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    has_rasterio = False
    try:
        import rasterio  # noqa: F401
        import numpy  # noqa: F401
        has_rasterio = True
    except ImportError:
        pass

    if not has_gdal_cli and not has_rasterio:
        print("=" * 60)
        print("ERROR: Neither GDAL command line tools nor rasterio are available.")
        print("To fix this on Ubuntu/Debian, install gdal-bin:")
        print("    sudo apt update && sudo apt install -y gdal-bin libgdal-dev")
        print("Or install python rasterio in your active virtual environment:")
        print("    pip install rasterio numpy")
        print("=" * 60)
        sys.exit(1)

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("30m Global DEM (Copernicus GLO-30) Downloader & Processor")
    print("Direct public access via AWS Open Data")
    print("=" * 60)

    for province, bbox in PILOT_PROVINCES.items():
        print(f"\n>>> Processing {province.upper()}...")
        coords = generate_tile_coords(bbox)
        downloaded_tifs = []

        for i, (lat, lon) in enumerate(coords, 1):
            filename, url = get_copernicus_tile_info(lat, lon)
            target_path = DATA_RAW / filename

            if target_path.exists() and target_path.stat().st_size > 1000:
                print(f"[{i}/{len(coords)}] {filename} already exists. Skipping download.")
                downloaded_tifs.append(str(target_path))
                continue

            lat_str = f"{'S' if lat < 0 else 'N'}{abs(lat):02d}"
            lon_str = f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}"
            print(f"[{i}/{len(coords)}] Downloading {lat_str}{lon_str} ({filename})...")

            try:
                response = requests.get(url, stream=True, timeout=30)
                if response.status_code == 404:
                    print(f"[{i}/{len(coords)}] Pure ocean tile (404). Skipping.")
                    continue
                response.raise_for_status()

                with open(target_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

                size_mb = target_path.stat().st_size / (1024 * 1024)
                print(f"[{i}/{len(coords)}] Downloaded {filename} ({size_mb:.1f} MB)")
                downloaded_tifs.append(str(target_path))

            except requests.exceptions.RequestException as e:
                print(f"[{i}/{len(coords)}] Download error for {filename}: {e}")
                if target_path.exists():
                    target_path.unlink()

        if not downloaded_tifs:
            print(f"Warning: No valid land tiles found for {province}.")
            continue

        dem_output = DATA_PROCESSED / f"{province}_dem.tif"
        slope_output = DATA_PROCESSED / f"{province}_slope.tif"

        if has_gdal_cli:
            print(f"\nMerging {len(downloaded_tifs)} tiles with gdalwarp into {dem_output.name}...")
            merge_cmd = [
                "gdalwarp",
                "-r", "bilinear",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-overwrite",
            ] + downloaded_tifs + [str(dem_output)]

            try:
                subprocess.run(merge_cmd, check=True)
                print(f"DEM saved: {dem_output}")
            except subprocess.CalledProcessError as e:
                print(f"Error merging with gdalwarp: {e}")
                continue

            print(f"Computing slope with gdaldem into {slope_output.name}...")
            slope_cmd = [
                "gdaldem",
                "slope",
                str(dem_output),
                str(slope_output),
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
            ]
            try:
                subprocess.run(slope_cmd, check=True)
                print(f"Slope saved: {slope_output}")
            except subprocess.CalledProcessError as e:
                print(f"Error generating slope: {e}")
        else:
            merge_and_slope_with_rasterio(downloaded_tifs, dem_output, slope_output)

    print("\n" + "=" * 60)
    print("Elevation and Slope processing completed!")
    print("=" * 60)


if __name__ == "__main__":
    download_and_process_dem()
