import os
import sys
import math
import netrc
import zipfile
import subprocess
from pathlib import Path
from getpass import getpass
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "elevation" / "tiles"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "elevation"
SRTM_BASE_URL = "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/"

PILOT_PROVINCES = {
    "lampung": {"west": 104, "east": 106, "south": -6, "north": -4},
    "east_java": {"west": 110, "east": 115, "south": -9, "north": -7},
    "south_sulawesi": {"west": 119, "east": 122, "south": -7, "north": -2},
}

def get_earthdata_credentials():
    """Get Earthdata credentials from env, netrc, or prompt."""
    user = os.environ.get("EARTHDATA_USER")
    password = os.environ.get("EARTHDATA_PASS")
    
    if user and password:
        return user, password
        
    try:
        secrets = netrc.netrc()
        auth = secrets.authenticators("urs.earthdata.nasa.gov")
        if auth:
            return auth[0], auth[2]
    except (FileNotFoundError, netrc.NetrcParseError):
        pass
        
    print("NASA Earthdata credentials required to download SRTM data.")
    print("Register at https://urs.earthdata.nasa.gov if you don't have an account.")
    user = input("Username: ")
    password = getpass("Password: ")
    return user, password

def get_tile_filename(lat, lon):
    """Generate SRTM tile filename for given lat/lon (bottom-left corner)."""
    lat_prefix = 'N' if lat >= 0 else 'S'
    lon_prefix = 'E' if lon >= 0 else 'W'
    
    # SRTM names use the absolute value of the lower-left coordinate
    return f"{lat_prefix}{abs(lat):02d}{lon_prefix}{abs(lon):03d}.SRTMGL1.hgt.zip"

def generate_tile_list(bbox):
    """Generate list of tile filenames for a bounding box."""
    # SRTM tiles are 1x1 degree, named by their lower-left (south-west) corner
    tiles = []
    # Floor to get the lower-left integer coordinates
    min_lon = math.floor(bbox["west"])
    max_lon = math.ceil(bbox["east"]) - 1
    min_lat = math.floor(bbox["south"])
    max_lat = math.ceil(bbox["north"]) - 1
    
    for lat in range(min_lat, max_lat + 1):
        for lon in range(min_lon, max_lon + 1):
            tiles.append(get_tile_filename(lat, lon))
            
    return tiles

class SessionWithHeaderRedirection(requests.Session):
    """Session class that handles authentication through Earthdata redirects."""
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

    # Overrides from the library to keep headers when redirected to or from
    # the NASA auth host.
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url
        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != 'urs.earthdata.nasa.gov':
                del headers['Authorization']

def check_gdal_installed():
    try:
        subprocess.run(["gdal_merge.py", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["gdaldem", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def download_and_process_srtm():
    if not check_gdal_installed():
        print("Error: GDAL (gdal_merge.py, gdaldem) must be installed and in PATH.")
        sys.exit(1)

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    user, password = get_earthdata_credentials()
    session = SessionWithHeaderRedirection(user, password)
    
    for province, bbox in PILOT_PROVINCES.items():
        print(f"\nProcessing {province.upper()}...")
        tiles = generate_tile_list(bbox)
        downloaded_hgt_files = []
        
        for i, tile_zip in enumerate(tiles, 1):
            tile_hgt = tile_zip.replace('.zip', '')
            hgt_path = DATA_RAW / tile_hgt
            zip_path = DATA_RAW / tile_zip
            
            if hgt_path.exists():
                print(f"[{i}/{len(tiles)}] {tile_hgt} already exists. Skipping download.")
                downloaded_hgt_files.append(str(hgt_path))
                continue
                
            url = f"{SRTM_BASE_URL}{tile_zip}"
            print(f"[{i}/{len(tiles)}] Downloading {tile_zip}...")
            
            try:
                response = session.get(url, stream=True)
                
                if response.status_code == 404:
                    print(f"[{i}/{len(tiles)}] Tile not found (likely ocean). Skipping.")
                    continue
                    
                response.raise_for_status()
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                # Extract
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extract(tile_hgt, DATA_RAW)
                    
                # Clean up zip
                zip_path.unlink()
                downloaded_hgt_files.append(str(hgt_path))
                
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {tile_zip}: {e}")
            except zipfile.BadZipFile:
                print(f"Downloaded file {tile_zip} is not a valid zip file. Auth issue?")
                if zip_path.exists():
                    zip_path.unlink()
        
        if not downloaded_hgt_files:
            print(f"No tiles found/downloaded for {province}.")
            continue
            
        dem_output = DATA_PROCESSED / f"{province}_dem.tif"
        slope_output = DATA_PROCESSED / f"{province}_slope.tif"
        
        # Merge
        print(f"Merging {len(downloaded_hgt_files)} tiles for {province}...")
        merge_cmd = ["gdal_merge.py", "-o", str(dem_output), "-co", "COMPRESS=DEFLATE"] + downloaded_hgt_files
        try:
            subprocess.run(merge_cmd, check=True, capture_output=True)
            print(f"Saved DEM to {dem_output}")
        except subprocess.CalledProcessError as e:
            print(f"Error merging tiles: {e.stderr.decode()}")
            continue
            
        # Slope
        print(f"Generating slope for {province}...")
        slope_cmd = ["gdaldem", "slope", str(dem_output), str(slope_output), "-co", "COMPRESS=DEFLATE"]
        try:
            subprocess.run(slope_cmd, check=True, capture_output=True)
            print(f"Saved Slope to {slope_output}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating slope: {e.stderr.decode()}")

    print("\nSRTM download and processing completed.")

if __name__ == "__main__":
    download_and_process_srtm()
