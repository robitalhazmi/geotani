import zipfile
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "boundaries"
HDX_DATASET_URL = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-idn"

def get_session():
    """Create a requests session with retries."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_hdx_download_url(session):
    """Get the download URL from the HDX CKAN API."""
    try:
        response = session.get(HDX_DATASET_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            resources = data.get("result", {}).get("resources", [])
            for res in resources:
                fmt = res.get("format", "").upper()
                name = res.get("name", "").lower()
                if fmt == "SHP" or "shp" in name or ".shp.zip" in res.get("url", "").lower():
                    return res.get("url")
    except Exception as e:
        print(f"Error getting download URL from API: {e}")

    # Fallback to direct URL if API fails
    print("Falling back to direct URL...")
    return "https://data.humdata.org/dataset/84a1d98a-790b-4d66-9d14-bbfa48500802/resource/50b9aafa-47c5-483e-a361-826320bf75d5/download/idn_admin_boundaries.shp.zip"

def download_file(session, url, dest_path):
    """Download a file with progress reporting."""
    print(f"Downloading from: {url}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    response = session.get(url, stream=True, timeout=30)
    response.raise_for_status()

    chunk_size = 1024 * 1024  # 1 MB
    report_interval = 10 * 1024 * 1024  # 10 MB
    downloaded = 0
    last_report = 0

    temp_path = dest_path.with_suffix(".tmp")
    with open(temp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded - last_report >= report_interval:
                    print(f"Downloaded: {downloaded / (1024 * 1024):.1f} MB")
                    last_report = downloaded

    temp_path.replace(dest_path)
    print(f"Download complete! Total size: {downloaded / (1024 * 1024):.1f} MB")

def extract_zip(zip_path, extract_dir):
    """Extract a ZIP file and print a summary."""
    print(f"Extracting {zip_path} to {extract_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

        extracted_files = zip_ref.namelist()
        total_size = sum([zinfo.file_size for zinfo in zip_ref.filelist])

        print("\nExtraction Summary:")
        print(f"Total extracted size: {total_size / (1024 * 1024):.1f} MB")
        print("Files extracted:")
        for file in extracted_files:
            print(f" - {file}")

def main():
    # Check if shapefiles already exist and are non-empty
    existing_shp = list(DATA_RAW.glob("*.shp"))
    if existing_shp:
        print(f"✓ Found {len(existing_shp)} boundary shapefiles in {DATA_RAW}. Skipping download.")
        return

    session = get_session()

    print("Finding resource URL...")
    download_url = get_hdx_download_url(session)
    if not download_url:
        raise RuntimeError("Failed to find boundary download URL.")

    zip_path = DATA_RAW / "boundaries.zip"

    # Validate existing zip
    if zip_path.exists():
        if not zipfile.is_zipfile(zip_path) or zip_path.stat().st_size < 1000000:
            print(f"⚠️ Existing {zip_path} is invalid/corrupted. Deleting and re-downloading...")
            zip_path.unlink()

    if not zip_path.exists():
        download_file(session, download_url, zip_path)

    try:
        extract_zip(zip_path, DATA_RAW)
        # Clean up zip file
        print(f"Removing {zip_path}...")
        zip_path.unlink()
    except Exception as e:
        if zip_path.exists():
            zip_path.unlink()
        raise e

if __name__ == "__main__":
    main()
