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
- [ ] Download Indonesia ADM4 (village) boundaries from HDX (`idn_adm_bps_adm4` dataset)
- [ ] Filter boundaries to the 3 pilot provinces (full village detail) + rest of Indonesia (dissolve to kabupaten/kecamatan level for coarse view)
- [ ] Load boundaries into PostGIS, validate geometries (`ST_MakeValid`, check for self-intersections)
- [ ] Download SoilGrids v2.0 layers for Indonesia extent (pH, clay, sand, organic carbon) — bulk GeoTIFF, not per-request API
- [ ] Download WorldClim v2.1 bioclimatic layers (annual mean temp, annual precipitation) for Indonesia extent
- [ ] Download SRTM 30m DEM for Indonesia extent, derive slope raster (GDAL)
- [ ] Download OSM Indonesia extract (Geofabrik) — extract roads + populated places layers
- [ ] Download Ditjenbun/BPS published province-level statistics for coffee, cocoa (perennial crop series) and sugarcane (BPS's separate "Perkebunan Semusim" annual-crop series — different publication than coffee/cocoa) for later validation, not model input
- [ ] Write a `data/README.md` documenting exact source URLs, license, and download date for every dataset (critical for reproducibility and for an "open source" project's credibility)

## Phase 2 — Suitability Scoring Engine (Python)
- [ ] Define crop requirement parameter tables (temp range, rainfall range, elevation range, pH range) for Coffee, Cocoa, Sugarcane — sourced from FAO Ecocrop + agronomic literature (note: Sugarcane is an annual crop with a distinct growth profile from the two perennials — a useful early test that the scoring framework generalizes beyond tree crops)
- [ ] Write zonal statistics pipeline: for each village polygon, compute mean/median value of each raster layer (using `rasterstats` or `exactextract`)
- [ ] Write distance-to-road/market calculation per village centroid (using OSM roads + `geopandas`/`shapely`)
- [ ] Implement fuzzy suitability scoring function per factor (trapezoidal membership curve: 0 → ramp → 100 → ramp → 0)
- [ ] Implement score combination logic: climate as a limiting "gate," soil/terrain/access as weighted average within that gate
- [ ] Run pipeline for the 3 pilot provinces × 3 crops, output scores to a table/CSV
- [ ] Sanity-check: do high-scoring villages roughly align with provinces/kabupaten known for that crop (from Phase 1 statistics)? Document findings, adjust weights if wildly off
- [ ] Write unit tests for the scoring functions (this is the part investors/users will question most — needs to be trustworthy)

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
