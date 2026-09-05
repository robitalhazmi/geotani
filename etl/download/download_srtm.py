"""Download 30m Global DEM tiles and compute slope rasters for pilot provinces.

Uses the Copernicus GLO-30 (30m) Global DEM hosted on AWS Open Data.
Provides 30m resolution, void-filled elevation data with direct public HTTPS downloads.

Memory-optimized for low-RAM cloud VPS environments (< 256MB RAM usage).
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


def merge_and_slope_chunked_rasterio(downloaded_tifs, dem_output, slope_output):
    """Fallback merge and slope computation using windowed chunking for low memory usage."""
    import numpy as np
    import rasterio
    from rasterio.merge import merge
    from rasterio.windows import Window

    print("Merging DEM tiles using rasterio...")
    src_files = [rasterio.open(f) for f in downloaded_tifs]
    mosaic, out_trans = merge(src_files)
    out_meta = src_files[0].meta.copy()
    for src in src_files:
        src.close()

    height, width = mosaic.shape[1], mosaic.shape[2]
    out_meta.update(
        {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "transform": out_trans,
            "compress": "deflate",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512,
        }
    )

    with rasterio.open(dem_output, "w", **out_meta) as dest:
        dest.write(mosaic)
    print(f"DEM merged: {dem_output}")

    # Free mosaic from memory before slope calculation
    del mosaic

    print("Computing slope raster in memory-efficient chunks (512x512)...")
    res_x = abs(out_trans[0]) * 111320.0
    res_y = abs(out_trans[4]) * 111320.0

    with rasterio.open(dem_output) as src_dem:
        slope_meta = src_dem.meta.copy()
        slope_meta.update({"dtype": "float32", "nodata": -9999.0})

        with rasterio.open(slope_output, "w", **slope_meta) as dst_slope:
            # Process in 512x512 tile windows with 1-pixel padding
            block_size = 512
            for row in range(0, height, block_size):
                for col in range(0, width, block_size):
                    w_width = min(block_size, width - col)
                    w_height = min(block_size, height - row)

                    # Add 1px padding around window for finite differences gradient
                    pad_top = 1 if row > 0 else 0
                    pad_bottom = 1 if (row + w_height) < height else 0
                    pad_left = 1 if col > 0 else 0
                    pad_right = 1 if (col + w_width) < width else 0

                    read_win = Window(
                        col - pad_left,
                        row - pad_top,
                        w_width + pad_left + pad_right,
                        w_height + pad_top + pad_bottom,
                    )
                    write_win = Window(col, row, w_width, w_height)

                    chunk = src_dem.read(1, window=read_win).astype(np.float32)
                    dy, dx = np.gradient(chunk, res_y, res_x)
                    slope_chunk = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

                    # Trim padding to match write_win
                    slope_clean = slope_chunk[
                        pad_top : pad_top + w_height, pad_left : pad_left + w_width
                    ]
                    dst_slope.write(slope_clean[np.newaxis, :, :], window=write_win)

    print(f"Slope raster generated: {slope_output}")


def download_and_process_dem():
    has_gdal_cli = False
    try:
        subprocess.run(
            ["gdaldem", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        has_gdal_cli = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    has_rasterio = False
    try:
        import numpy  # noqa: F401
        import rasterio  # noqa: F401

        has_rasterio = True
    except ImportError:
        pass

    if not has_gdal_cli and not has_rasterio:
        print("=" * 60)
        print("ERROR: Neither GDAL command line tools nor rasterio are available.")
        print("=" * 60)
        sys.exit(1)

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("30m Global DEM (Copernicus GLO-30) Downloader & Processor")
    print("Direct public access via AWS Open Data")
    print("=" * 60)

    for province, bbox in PILOT_PROVINCES.items():
        dem_output = DATA_PROCESSED / f"{province}_dem.tif"
        slope_output = DATA_PROCESSED / f"{province}_slope.tif"

        if (
            dem_output.exists()
            and slope_output.exists()
            and dem_output.stat().st_size > 10000
            and slope_output.stat().st_size > 10000
        ):
            print(f"✓ DEM and Slope rasters for {province.upper()} already exist. Skipping.")
            continue

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

        if has_gdal_cli:
            vrt_file = DATA_PROCESSED / f"{province}_temp.vrt"
            print(f"\nBuilding virtual raster VRT: {vrt_file.name}...")
            vrt_cmd = ["gdalbuildvrt", "-overwrite", str(vrt_file)] + downloaded_tifs
            try:
                subprocess.run(vrt_cmd, check=True)
                print(f"Translating VRT to optimized GeoTIFF: {dem_output.name}...")
                translate_cmd = [
                    "gdal_translate",
                    "-co",
                    "COMPRESS=DEFLATE",
                    "-co",
                    "TILED=YES",
                    str(vrt_file),
                    str(dem_output),
                ]
                subprocess.run(translate_cmd, check=True)
                if vrt_file.exists():
                    vrt_file.unlink()
                print(f"DEM saved: {dem_output}")
            except subprocess.CalledProcessError as e:
                print(f"GDAL translation error: {e}. Trying fallback...")
                merge_and_slope_chunked_rasterio(downloaded_tifs, dem_output, slope_output)
                continue

            print(f"Computing slope with gdaldem into {slope_output.name}...")
            slope_cmd = [
                "gdaldem",
                "slope",
                str(dem_output),
                str(slope_output),
                "-co",
                "COMPRESS=DEFLATE",
                "-co",
                "TILED=YES",
            ]
            try:
                subprocess.run(slope_cmd, check=True)
                print(f"Slope saved: {slope_output}")
            except subprocess.CalledProcessError as e:
                print(f"Error generating slope: {e}")
        else:
            merge_and_slope_chunked_rasterio(downloaded_tifs, dem_output, slope_output)

    print("\n" + "=" * 60)
    print("Elevation and Slope processing completed!")
    print("=" * 60)


if __name__ == "__main__":
    download_and_process_dem()
