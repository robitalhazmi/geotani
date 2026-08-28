# Data Sources

This directory contains raw and processed geospatial data for TaniScope. **Raw and processed data files are not tracked in Git** (they are large binaries). Use the ETL scripts in `etl/download/` and `etl/` to fetch and process them.

## Directory Structure

- `raw/` — Downloaded source datasets (gitignored)
  - `boundaries/` — Raw administrative boundary shapefiles from HDX
  - `climate/` — Raw bioclimatic variables from WorldClim
  - `osm/` — Regional OpenStreetMap shapefile extracts (Java, Sumatra, Sulawesi)
  - `elevation/tiles/` — Raw 1-arc-second SRTM HGT/ZIP tiles from NASA LP DAAC
- `processed/` — Cleaned, clipped, and transformed outputs (gitignored)
  - `boundaries/` — Filtered pilot villages + dissolved coarse boundaries (`taniscope_boundaries.gpkg`)
  - `climate/` — Clipped temperature (BIO1) and rainfall (BIO12) rasters for Indonesia
  - `soil/` — Clipped SoilGrids v2.0 rasters (pH, clay, sand, SOC at 0-5cm)
  - `elevation/` — Merged DEM and derived slope rasters for pilot provinces

---

## Data Sources & Acquisition Scripts

| Dataset | Source | Format | Resolution | License | Script | Notes |
|---|---|---|---|---|---|---|
| **Village Boundaries (ADM4)** | [HDX Indonesia Subnational Admin Boundaries](https://data.humdata.org/dataset/cod-ab-idn) | ESRI Shapefile in ZIP | Village (ADM4) & Regency (ADM2) | CC-BY (BPS / OCHA) | `python etl/download/download_boundaries.py` | Automatically queries HDX CKAN API |
| **Climate Normals** | [WorldClim v2.1](https://worldclim.org) | GeoTIFF | 2.5 arc-min (~4.5 km) | Free for research | `python etl/download/download_worldclim.py` | Extracts & clips BIO1 (temp) & BIO12 (rainfall) to Indonesia bbox |
| **Soil Properties** | [ISRIC SoilGrids v2.0](https://soilgrids.org) | GeoTIFF (via VRT) | 250m | CC-BY 4.0 | `python etl/download/download_soilgrids.py` | Uses GDAL `/vsicurl/` to stream-clip 0-5cm pH, clay, sand, and SOC |
| **Elevation & Slope (DEM)** | [NASA LP DAAC / USGS SRTM](https://e4ftl01.cr.usgs.gov/) | GeoTIFF / HGT | 30m (1 arc-sec) | Public domain | `python etl/download/download_srtm.py` | Downloads pilot province tiles (Lampung, East Java, South Sulawesi), merges & derives slope |
| **Roads & Places** | [Geofabrik OpenStreetMap](https://download.geofabrik.de/asia/indonesia.html) | Shapefile extracts | Vector | ODbL | `python etl/download/download_osm.py` | Extracts roads & places for Java, Sumatra, and Sulawesi |

---

## Step-by-Step Data Pipeline

### 1. Download Datasets
Ensure your virtual environment is active (`source .venv/bin/activate`):

```bash
# Download village and district boundaries
python etl/download/download_boundaries.py

# Download and clip climate rasters
python etl/download/download_worldclim.py

# Stream-clip SoilGrids rasters via GDAL
python etl/download/download_soilgrids.py

# Download SRTM elevation and compute slope rasters
# (Prompts for NASA Earthdata credentials or uses EARTHDATA_USER / EARTHDATA_PASS env vars)
python etl/download/download_srtm.py

# Download OSM road networks and settlements
python etl/download/download_osm.py
```

### 2. Process Boundaries
Filter villages for the 3 pilot provinces (Lampung, East Java, South Sulawesi) and dissolve other provinces into coarse regency (kabupaten) polygons:

```bash
python etl/boundaries.py
```
Output: `data/processed/boundaries/taniscope_boundaries.gpkg`

### 3. Ingest into PostGIS
Start the database service:

```bash
docker compose up -d db
```

Load the boundaries and initialize the tables:

```bash
python etl/load_postgis.py --drop
```
