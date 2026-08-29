import os
import zipfile
from pathlib import Path

import rasterio
import requests
from rasterio.windows import from_bounds
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "climate"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "climate"
WORLDCLIM_URL = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip"
INDONESIA_BBOX = (95.0, -11.0, 141.0, 6.0)  # (west, south, east, north)

def get_session():
    """Create a requests session with retries."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def download_file(session, url, dest_path):
    """Download a file with progress reporting."""
    print(f"Downloading from: {url}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    response = session.get(url, stream=True)
    response.raise_for_status()

    chunk_size = 1024 * 1024  # 1 MB
    report_interval = 10 * 1024 * 1024  # 10 MB
    downloaded = 0
    last_report = 0

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded - last_report >= report_interval:
                    print(f"Downloaded: {downloaded / (1024 * 1024):.1f} MB")
                    last_report = downloaded

    print(f"Download complete! Total size: {downloaded / (1024 * 1024):.1f} MB")

def extract_target_files(zip_path, extract_dir, target_files):
    """Extract specific files from a ZIP."""
    print(f"Extracting specific files to {extract_dir}...")
    extract_dir.mkdir(parents=True, exist_ok=True)
    extracted = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in target_files:
            if file in zip_ref.namelist():
                zip_ref.extract(file, extract_dir)
                extracted.append(extract_dir / file)
                print(f"Extracted {file}")
            else:
                print(f"Warning: {file} not found in zip archive.")

    return extracted

def clip_raster_to_bbox(input_path, output_path, bbox):
    """Clip a raster to a bounding box and save as new GeoTIFF."""
    print(f"Clipping {input_path.name}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    west, south, east, north = bbox

    with rasterio.open(input_path) as src:
        # Create a window from bounds
        window = from_bounds(west, south, east, north, src.transform)

        # Read data using the window
        data = src.read(window=window)

        # Update transform
        new_transform = src.window_transform(window)

        # Update metadata
        kwargs = src.meta.copy()
        kwargs.update({
            'height': window.height,
            'width': window.width,
            'transform': new_transform
        })

        # Write to new file
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            dst.write(data)

        print("\nClipping Summary:")
        print(f"File: {output_path.name}")
        print(f"Original size: {os.path.getsize(input_path) / (1024 * 1024):.2f} MB")
        print(f"Clipped size: {os.path.getsize(output_path) / (1024 * 1024):.2f} MB")
        print(f"Shape: {data.shape}")
        print(f"CRS: {src.crs}\n")

def main():
    session = get_session()
    zip_path = DATA_RAW / "wc2.1_2.5m_bio.zip"

    try:
        if not zip_path.exists():
            download_file(session, WORLDCLIM_URL, zip_path)
        else:
            print(f"{zip_path} already exists, skipping download.")

        # Target variables: 1 (Annual Mean Temp), 12 (Annual Precipitation)
        target_files = ["wc2.1_2.5m_bio_1.tif", "wc2.1_2.5m_bio_12.tif"]
        extracted_paths = extract_target_files(zip_path, DATA_RAW, target_files)

        for input_path in extracted_paths:
            output_path = DATA_PROCESSED / input_path.name
            clip_raster_to_bbox(input_path, output_path, INDONESIA_BBOX)

        # Clean up zip file
        print(f"Removing {zip_path}...")
        zip_path.unlink()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
