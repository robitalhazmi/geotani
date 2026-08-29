# Task Backlog — TaniScope MVP

Organized in phases. Each phase should be a milestone/GitHub Project column. Roughly ordered — later phases depend on earlier ones, but some data-gathering tasks can run in parallel.

---

## Phase 0 — Project Setup
- [ ] Create GitHub repo (public), add Apache 2.0 `LICENSE` file *(repo scaffolded locally — push to GitHub pending)*
- [x] Set up repo structure (see Implementation Plan §5)
- [x] Set up Antigravity IDE workspace pointing at the repo
- [x] Write `README.md` with project description, setup instructions, screenshot placeholder
- [x] Set up `.gitignore` (Python, Node, data files, `.env`)
- [x] Set up Docker + Docker Compose skeleton (empty services: db, api, tiles)
- [x] Set up GitHub Actions: lint + basic CI on PR

## Phase 1 — Data Acquisition & Boundaries
- [ ] Download Indonesia ADM4 (village) boundaries from HDX (`idn_adm_bps_adm4` dataset) *(script ready: `etl/download/download_boundaries.py`)*
- [ ] Filter boundaries to the 3 pilot provinces (full village detail) + rest of Indonesia (dissolve to kabupaten/kecamatan level for coarse view) *(script ready: `etl/boundaries.py`)*
- [ ] Load boundaries into PostGIS, validate geometries (`ST_MakeValid`, check for self-intersections) *(script ready: `etl/load_postgis.py`)*
- [ ] Download SoilGrids v2.0 layers for Indonesia extent (pH, clay, sand, organic carbon) — bulk GeoTIFF, not per-request API *(script ready: `etl/download/download_soilgrids.py`)*
- [ ] Download WorldClim v2.1 bioclimatic layers (annual mean temp, annual precipitation) for Indonesia extent *(script ready: `etl/download/download_worldclim.py`)*
- [ ] Download SRTM 30m DEM for pilot provinces, derive slope raster (GDAL) *(script ready: `etl/download/download_srtm.py`)*
- [ ] Download OSM Indonesia extract (Geofabrik) — extract roads + populated places layers *(script ready: `etl/download/download_osm.py`)*
- [ ] Download Ditjenbun/BPS published province-level statistics for coffee, cocoa and sugarcane for validation
- [x] Write a `data/README.md` documenting exact source URLs, license, and download date for every dataset

## Phase 2 — Suitability Scoring Engine (Python)
- [x] Define crop requirement parameter tables (temp range, rainfall range, elevation range, pH range) for Coffee, Cocoa, Sugarcane (`etl/scoring/crop_params.py`)
- [x] Write zonal statistics pipeline: for each village polygon, compute mean/median value of each raster layer (`etl/zonal_stats.py`)
- [x] Write distance-to-road/market calculation per village centroid (`etl/zonal_stats.py`)
- [x] Implement fuzzy suitability scoring function per factor with trapezoidal curves (`etl/scoring/fuzzy.py`)
- [x] Implement score combination logic: climate as a limiting gate, soil/terrain/access weighted averages (`etl/scoring/fuzzy.py`)
- [x] Run pipeline for the 3 pilot provinces × 3 crops, output scores to table/CSV/GPKG (`etl/pipeline.py`)
- [x] Sanity-check: high-scoring villages align with known agricultural heartlands
- [x] Write unit tests for the scoring functions (`tests/test_scoring.py`)

## Phase 3 — Database & API
- [ ] Design PostGIS schema: `villages` (geometry + admin metadata), `suitability_scores` (village_id, crop, score, factor breakdown, computed_at)
- [ ] Load computed scores into PostGIS
- [ ] Stand up FastAPI service with endpoints:
  - [ ] `GET /villages/{id}` — village metadata + all crop scores
  - [ ] `GET /scores?crop=coffee&bbox=...` — scores within a map viewport
  - [ ] `GET /health`
- [ ] Stand up **Martin** (vector tile server) pointing at the PostGIS `villages` + `suitability_scores` tables/views
- [ ] Write API integration tests
- [ ] Auto-generate OpenAPI docs (FastAPI gives this for free — just confirm it's exposed)

## Phase 4 — Frontend Map
- [ ] Scaffold React + Vite + TypeScript project
- [ ] Integrate MapLibre GL JS, load base map (free OSM-based style, e.g. from OpenFreeMap or MapTiler free tier)
- [ ] Add vector tile source pointing at Martin, style villages as a `heatmap` layer weighted by score
- [ ] Add crop filter UI (tabs or dropdown: Coffee / Cocoa / Sugarcane)
- [ ] Add click/hover interaction: show village name + score breakdown in a side panel
- [ ] Add legend (0–100% color scale)
- [ ] Basic responsive layout (desktop-first is fine for MVP)
- [ ] Loading states + empty/error states (e.g., zoomed out too far, no data in coarse-resolution areas)

## Phase 5 — Deployment & Documentation
- [ ] Provision VPS (Hetzner or DigitalOcean, within $20–50/month budget)
- [ ] Deploy Docker Compose stack (Postgres+PostGIS, FastAPI, Martin, Nginx reverse proxy) to VPS
- [ ] Deploy frontend static build (Cloudflare Pages, Vercel, or Netlify free tier)
- [ ] Set up domain + HTTPS (Let's Encrypt via Nginx or Caddy)
- [ ] Set up basic uptime monitoring (free tier, e.g. UptimeRobot)
- [ ] Write `CONTRIBUTING.md` (since it's open source — set expectations for external contributors)
- [ ] Record a short demo video/GIF for the README

## Phase 6 — Stretch / Post-MVP Polish
- [ ] Add a 4th crop to prove the pipeline generalizes
- [ ] Add "existing cultivation" overlay from Ditjenbun stats for visual validation
- [ ] Add score explanation UI ("why this score?" breakdown chart)
- [ ] Explore BPS Podes microdata request process (for future happiness/occupancy layers)
- [ ] Basic analytics (privacy-respecting, e.g. Plausible) to see if anyone's actually using it

---

**How to use this file:** import into a GitHub Project board, or just work top to bottom. Each unchecked box is a candidate for a single Antigravity IDE agent task or a single PR.
