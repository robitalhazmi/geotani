"""Download and clip SoilGrids v2.0 layers for Indonesia using GDAL.

Uses GDAL's /vsicurl/ to read remote VRT files and clips directly to
Indonesia bounding box — no full global download needed.

Layers downloaded (0-5cm topsoil):
    - phh2o: Soil pH in H2O
    - clay: Clay content
    - sand: Sand content
    - soc: Soil organic carbon

Note: Pixel values are stored as integers. Divide by 10 for actual values.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "soil"
INDONESIA_BBOX_WGS84 = (95, 6, 141, -11)  # (west, north, east, south)

SOILGRIDS_LAYERS = {
    "phh2o": {
        "url": "https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_0-5cm_mean.vrt",
        "output": "phh2o_0-5cm_indonesia.tif",
        "description": "Soil pH in H2O (divide by 10 for actual value)",
    },
    "clay": {
        "url": "https://files.isric.org/soilgrids/latest/data/clay/clay_0-5cm_mean.vrt",
        "output": "clay_0-5cm_indonesia.tif",
        "description": "Clay content in g/kg (divide by 10 for g/100g = %)",
    },
    "sand": {
        "url": "https://files.isric.org/soilgrids/latest/data/sand/sand_0-5cm_mean.vrt",
        "output": "sand_0-5cm_indonesia.tif",
        "description": "Sand content in g/kg (divide by 10 for g/100g = %)",
    },
    "soc": {
        "url": "https://files.isric.org/soilgrids/latest/data/soc/soc_0-5cm_mean.vrt",
        "output": "soc_0-5cm_indonesia.tif",
        "description": "Soil organic carbon in dg/kg (divide by 10 for g/kg)",
    },
}


def check_gdal_installed():
    """Check if gdal_translate is available."""
    try:
        subprocess.run(
            ["gdal_translate", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_soilgrids():
    """Download and clip SoilGrids layers for Indonesia."""
    if not check_gdal_installed():
        print("Error: GDAL is not installed or 'gdal_translate' is not in PATH.")
        print("Please install GDAL (e.g., 'sudo apt install gdal-bin' on Ubuntu).")
        sys.exit(1)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # Set GDAL config options for better performance with remote VRTs
    os.environ["GDAL_HTTP_MULTIRANGE"] = "YES"
    os.environ["GDAL_HTTP_MERGE_CONSECUTIVE_RANGES"] = "YES"
    os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".tif,.vrt"

    print(f"Starting SoilGrids download for Indonesia bounding box: {INDONESIA_BBOX_WGS84}")
    print("Note: Pixel values will need to be divided by 10 for actual values.\n")

    for layer_id, layer_info in SOILGRIDS_LAYERS.items():
        vrt_url = layer_info["url"]
        output_filename = layer_info["output"]
        output_path = DATA_PROCESSED / output_filename

        print(f"[{layer_id}] Downloading: {layer_info['description']}")

        if output_path.exists():
            print(f"[{layer_id}] File {output_filename} already exists. Skipping.")
            print("-" * 40)
            continue

        print(
            f"[{layer_id}] Running gdal_translate. "
            "This may take a few minutes depending on network speed..."
        )

        cmd = [
            "gdal_translate",
            "-projwin",
            str(INDONESIA_BBOX_WGS84[0]),
            str(INDONESIA_BBOX_WGS84[1]),
            str(INDONESIA_BBOX_WGS84[2]),
            str(INDONESIA_BBOX_WGS84[3]),
            "-projwin_srs",
            "EPSG:4326",
            "-co",
            "COMPRESS=DEFLATE",
            "-co",
            "TILED=YES",
            f"/vsicurl/{vrt_url}",
            str(output_path),
        ]

        try:
            # Don't hide output so the user can see gdal's built-in progress bar
            subprocess.run(cmd, check=True)
            print(f"[{layer_id}] Successfully saved to {output_path}")
        except subprocess.CalledProcessError:
            print(
                f"[{layer_id}] Error downloading layer. "
                "Check network connection or GDAL installation."
            )
            print(f"Command failed: {' '.join(cmd)}")

            # Clean up incomplete file
            if output_path.exists():
                output_path.unlink()

        print("-" * 40)

    print("SoilGrids download process completed.")


if __name__ == "__main__":
    download_soilgrids()
