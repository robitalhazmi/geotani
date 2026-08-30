# Task Backlog — GeoTani MVP

Organized in phases. Each phase represents a major milestone.

---

## Phase 0 — Project Setup
- [x] Create GitHub repo (public), add Apache 2.0 `LICENSE` file
- [x] Set up repo structure (`api/`, `etl/`, `frontend/`, `data/`, `docs/`, `tests/`)
- [x] Set up Antigravity IDE workspace pointing at the repo
- [x] Write `README.md` with project description, setup instructions, screenshot placeholder
- [x] Set up `.gitignore` (Python, Node, data files, `.env`)
- [x] Set up Docker + Docker Compose skeleton (PostGIS, FastAPI, Martin)
- [x] Set up GitHub Actions: lint + basic CI on PR

## Phase 1 — Data Acquisition & Boundaries
- [x] Download Indonesia ADM4 (village) boundaries from HDX (`etl/download/download_boundaries.py`)
- [x] Filter boundaries to 3 pilot provinces (village detail) + coarse nationwide regencies (`etl/boundaries.py`)
- [x] Load boundaries into PostGIS, validate geometries with `ST_MakeValid` (`etl/load_postgis.py`)
- [x] Download SoilGrids v2.0 layers for Indonesia: pH, clay, sand, SOC (`etl/download/download_soilgrids.py`)
- [x] Download WorldClim v2.1 bioclimatic layers: BIO1 temp, BIO12 rain (`etl/download/download_worldclim.py`)
- [x] Download 30m Global DEM & derive slope rasters for pilot provinces (`etl/download/download_srtm.py`)
- [x] Download OSM Indonesia extract — extract road networks & places (`etl/download/download_osm.py`)
- [x] Validate model output against known agricultural production benchmarks
- [x] Write `data/README.md` documenting exact source URLs, license, and download date

## Phase 2 — Suitability Scoring Engine (Python)
- [x] Define crop requirement parameter tables for Coffee, Cocoa, Sugarcane (`etl/scoring/crop_params.py`)
- [x] Write zonal statistics pipeline: compute median/mean of each raster layer per village (`etl/zonal_stats.py`)
- [x] Write distance-to-road calculation per village centroid via STRtree (`etl/zonal_stats.py`)
- [x] Implement fuzzy suitability scoring function with trapezoidal curves (`etl/scoring/fuzzy.py`)
- [x] Implement score combination logic: climate gate + soil/terrain/access weighted averages (`etl/scoring/fuzzy.py`)
- [x] Run pipeline for 3 pilot provinces × 3 crops, output scores to table/CSV/GPKG (`etl/pipeline.py`)
- [x] Sanity-check: high-scoring villages align with known agricultural heartlands
- [x] Write unit tests for scoring functions (`tests/test_scoring.py` — 100% pass)

## Phase 3 — Database & API
- [x] Design PostGIS schema: `villages` (geometry + admin metadata), `suitability_scores` (`etl/load_postgis.py`)
- [x] Load computed scores into PostGIS (44,259 records loaded into `suitability_scores`)
- [x] Stand up FastAPI service with complete endpoints:
  - [x] `GET /villages/{id}` & `GET /villages/by-pcode/{pcode}` — village metadata + all crop scores + factor breakdown
  - [x] `GET /scores?crop=...&bbox=...` — scores within a map viewport with spatial indexing
  - [x] `GET /crops` & `GET /crops/{id}` — crop parameter catalogue
  - [x] `GET /health` (database connectivity & record count verification)
- [x] Configure **Martin** (vector tile server) to serve PostGIS vector tiles (`/village_suitability/{z}/{x}/{y}`)
- [x] Write API integration tests (`tests/test_api.py` — 18/18 tests passing)
- [x] Auto-generate OpenAPI docs (FastAPI `/docs` exposed)

## Phase 4 — Frontend Map
- [x] Scaffold React + Vite + TypeScript project (`frontend/`)
- [x] Integrate MapLibre GL JS, load base map (OpenFreeMap positron in `frontend/src/components/MapComponent.tsx`)
- [x] Add vector tile source pointing at Martin, style villages as a choropleth/heatmap layer weighted by crop score
- [x] Add crop filter UI (tabs with icons for Coffee, Cocoa, Sugarcane in `Navbar.tsx`)
- [x] Add click/hover interaction: show village name tooltip on hover and full score breakdown in side panel (`VillageDetailPanel.tsx`)
- [x] Add legend (0–100% color scale + interactive min-score threshold filter slider in `Legend.tsx`)
- [x] Basic responsive layout (desktop-first with slide-in drawer and mobile responsiveness)
- [x] Quick-jump province selector (All Indonesia, East Java, Lampung, South Sulawesi)
- [x] Loading states + empty/error states and live database connectivity indicator

## Phase 5 — Deployment & Documentation
- [ ] Provision VPS (Hetzner or DigitalOcean, within $20–50/month budget)
- [ ] Deploy Docker Compose stack (Postgres+PostGIS, FastAPI, Martin, Nginx reverse proxy) to VPS
- [ ] Deploy frontend static build (Cloudflare Pages, Vercel, or Netlify free tier)
- [ ] Set up domain + HTTPS (Let's Encrypt via Nginx or Caddy)
- [ ] Set up basic uptime monitoring (free tier, e.g. UptimeRobot)
- [x] Write `CONTRIBUTING.md` (set expectations for external contributors)
- [ ] Record a short demo video/GIF for the README

## Phase 6 — Stretch / Post-MVP Polish
- [ ] Add a 4th crop to prove the pipeline generalizes
- [ ] Add "existing cultivation" overlay from Ditjenbun stats for visual validation
- [ ] Add score explanation UI ("why this score?" breakdown chart)
- [ ] Explore BPS Podes microdata request process (for future happiness/occupancy layers)
- [ ] Basic analytics (privacy-respecting, e.g. Plausible) to see if anyone's actually using it
