import os
import zipfile
import time
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "boundaries"
HDX_DATASET_URL = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-idn"

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

def get_hdx_download_url(session):
    """Get the download URL from the HDX CKAN API."""
    try:
        response = session.get(HDX_DATASET_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            resources = data.get("result", {}).get("resources", [])
            for res in resources:
                fmt = res.get("format", "").upper()
                name = res.get("name", "").lower()
                if fmt == "SHP" or "shp" in name:
                    return res.get("url")
    except Exception as e:
        print(f"Error getting download URL from API: {e}")
    
    # Fallback to direct URL if API fails
    print("Falling back to direct URL...")
    return "https://data.humdata.org/dataset/cod-ab-idn/resource/shp/download/idn_adm_bps_20200401_shp.zip"

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
    session = get_session()
    
    print("Finding resource URL...")
    download_url = get_hdx_download_url(session)
    if not download_url:
        print("Failed to find download URL.")
        return
        
    zip_path = DATA_RAW / "boundaries.zip"
    
    try:
        download_file(session, download_url, zip_path)
        extract_zip(zip_path, DATA_RAW)
        
        # Clean up zip file
        print(f"Removing {zip_path}...")
        zip_path.unlink()
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
