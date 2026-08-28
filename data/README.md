# Data Sources

This directory contains raw and processed geospatial data for TaniScope. **Raw data files are not tracked in Git** (they're too large). Use the ETL scripts to download them.

## Directory Structure

- `raw/` — Downloaded source datasets (gitignored)
- `processed/` — Cleaned, clipped, and transformed outputs (gitignored)

## Data Sources

| Dataset | Source | Format | Resolution | License | Download Script |
|---|---|---|---|---|---|
| Village boundaries (ADM4) | [HDX Indonesia Subnational Admin Boundaries](https://data.humdata.org/dataset/cod-ab-idn) | GeoPackage/SHP | Village-level vector | CC-BY (BPS) | TBD |
| Soil properties | [ISRIC SoilGrids v2.0](https://soilgrids.org) | GeoTIFF | 250m raster | CC-BY 4.0 | TBD |
| Climate normals | [WorldClim v2.1](https://worldclim.org) | GeoTIFF | ~1km (30 arc-sec) | Free for research | TBD |
| Elevation (DEM) | SRTM 30m (NASA/USGS) | GeoTIFF | 30m raster | Public domain | TBD |
| Roads / accessibility | [OpenStreetMap](https://download.geofabrik.de) (Geofabrik) | PBF/SHP | Vector | ODbL | TBD |
| Crop production stats | Ditjenbun / BPS | PDF/Excel | Province/Kabupaten | Open govt. | TBD |

## Reproduction

To reproduce the full dataset from scratch:

```bash
# TODO: Add download + processing commands once ETL scripts are implemented (Phase 1-2)
```

**Download date:** TBD (will be filled when data is first acquired)
