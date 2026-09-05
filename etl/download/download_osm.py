import os
import zipfile
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "osm"
GEOFABRIK_URLS = {
    "java": "https://download.geofabrik.de/asia/indonesia/java-latest-free.shp.zip",
    "sumatra": "https://download.geofabrik.de/asia/indonesia/sumatra-latest-free.shp.zip",
    "sulawesi": "https://download.geofabrik.de/asia/indonesia/sulawesi-latest-free.shp.zip",
}

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

def extract_target_files(zip_path, extract_dir):
    """Extract roads and places shapefiles (with sidecars) from a ZIP."""
    print(f"Extracting specific files to {extract_dir}...")
    extract_dir.mkdir(parents=True, exist_ok=True)

    target_bases = ["gis_osm_roads_free_1", "gis_osm_places_free_1"]
    sidecars = [".shp", ".shx", ".dbf", ".prj", ".cpg"]

    # Build a set of all required filenames
    required_files = {f"{base}{ext}" for base in target_bases for ext in sidecars}
    extracted_files = []
    total_size = 0

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in required_files:
            if file in zip_ref.namelist():
                zip_ref.extract(file, extract_dir)
                extracted_files.append(file)
                total_size += os.path.getsize(extract_dir / file)
            else:
                print(f"Warning: {file} not found in zip archive.")

    return extracted_files, total_size

def main():
    session = get_session()

    for region, url in GEOFABRIK_URLS.items():
        print(f"\n--- Processing region: {region} ---")

        region_dir = DATA_RAW / region
        roads_file = region_dir / "gis_osm_roads_free_1.shp"
        if roads_file.exists() and roads_file.stat().st_size > 1000:
            print(f"✓ OSM road network for {region} already exists in {region_dir}. Skipping.")
            continue

        zip_path = DATA_RAW / f"{region}.zip"

        try:
            if not zip_path.exists():
                download_file(session, url, zip_path)
            else:
                print(f"✓ {zip_path} already downloaded. Extracting...")

            extracted_files, total_size = extract_target_files(zip_path, region_dir)

            print(f"\nSummary for {region}:")
            print(f"Total extracted size: {total_size / (1024 * 1024):.2f} MB")
            print("Files extracted:")
            for f in extracted_files:
                print(f" - {f}")

            # Clean up zip file
            if zip_path.exists():
                print(f"Removing {zip_path}...")
                zip_path.unlink()

        except Exception as e:
            print(f"An error occurred while processing {region}: {e}")

if __name__ == "__main__":
    main()
