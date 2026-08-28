# Implementation Plan — TaniScope MVP

---

## 0. Pilot Scope: Provinces & Crops

| Province | Why it's in the pilot |
|---|---|
| **Lampung** | Strong on all three target crops: major Robusta coffee producer, large modern sugarcane estates (e.g. Gunung Madu, Sweet Indolampung), and meaningful cocoa presence. The best single "all-rounder" validation province |
| **South Sulawesi** | National leader in cocoa production (Luwu/Luwu Utara); home to Toraja Arabica, a globally known coffee specialty region; some sugar milling activity (Bone/Takalar) |
| **East Java** | Indonesia's #1 tobacco-producing province and historic sugarcane heartland (colonial-era sugar mills, active Madura expansion); newly in the **top 10 nationally for cocoa** and growing fast; some coffee (Ijen/Kayumas Robusta) |

**Crop choice: Coffee, Cocoa, Sugarcane** (dropping Rubber from the original pilot). Rubber production is concentrated almost entirely in Sumatra/Kalimantan and has negligible presence in East Java, so it stopped being a meaningful comparison crop once East Java entered the pilot. Sugarcane is a better fit — it's strong in two of the three provinces (Lampung, East Java) and gives the model a genuinely useful technical test: **Sugarcane is an annual crop, unlike the two perennials (coffee, cocoa)**, so proving the scoring framework handles it correctly is good early evidence the approach generalizes beyond tree crops — a Phase 6 stretch goal pulled forward into the MVP itself.

Each crop now has at least two of the three provinces as a strong validation case:
- **Coffee** → Lampung (major), South Sulawesi (Toraja)
- **Cocoa** → South Sulawesi (national leader), East Java (fast-growing top-10)
- **Sugarcane** → Lampung (major estates), East Java (historic heartland)

---

## 1. Tech Stack

All choices are free, open-source, and the current market leader in their category — chosen to fit a solo backend/data-strong developer, on Linux, using Antigravity IDE + GitHub.

| Layer | Choice | Why |
|---|---|---|
| Data processing / ETL | **Python 3.11+**, GeoPandas, Rasterio, Shapely, `rasterstats` | The standard geospatial data science stack; plays to your backend/data strength |
| Database | **PostgreSQL 16 + PostGIS 3.4** | The industry-standard open-source spatial database. Everything else in this stack is built to talk to it |
| Backend API | **FastAPI** (Python) + SQLAlchemy/GeoAlchemy2 | Modern, fast, auto-generates API docs, easiest framework for a Python-strong dev to pick up |
| Vector tile server | **Martin** (Rust, open source) | Serves PostGIS tables directly as vector tiles with near-zero config — pairs natively with MapLibre |
| Frontend map rendering | **MapLibre GL JS** | The open-source fork of Mapbox GL JS, now the de facto market-leading open web map renderer. Has a **built-in `heatmap` layer type** — this gives you the smooth gradient look you asked for with no custom interpolation code needed |
| Frontend framework | **React + Vite + TypeScript** | Market-standard, huge ecosystem, easiest to eventually hire/collaborate around |
| Styling | **Tailwind CSS** | Fast to build clean UI without deep frontend design skill |
| Containerization | **Docker + Docker Compose** | Reproducible dev/prod environments, easy to hand off or scale later |
| CI/CD | **GitHub Actions** | Free for public repos, integrates directly with your existing GitHub workflow |
| Version control | **Git + GitHub** | Already your choice |

**Simpler alternative to note:** if React feels like too much new surface area early on, you could ship v1's frontend as plain HTML + vanilla JS + MapLibre GL JS (no build step at all). It's a valid MVP shortcut — but since this is meant to grow into a multi-layer platform, React now will save a rewrite later. Your call; the backend/data/scoring work (the hard, defensible part) is identical either way.

---

## 2. System Architecture

```
┌─────────────────────┐
│   Open Data Sources   │  (HDX, SoilGrids, WorldClim, SRTM, OSM, Ditjenbun)
└──────────┬───────────┘
           │  (one-time / periodic ETL, Phase 1-2)
           ▼
┌─────────────────────┐
│  Python ETL Pipeline  │  GeoPandas + Rasterio + rasterstats
│  (zonal stats +       │
│   suitability scoring)│
└──────────┬───────────┘
           │  writes
           ▼
┌─────────────────────┐
│  PostgreSQL + PostGIS │  villages table + suitability_scores table
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌──────────┐
│ FastAPI  │  │  Martin   │   (both read from the same PostGIS DB)
│ (JSON)   │  │ (vector   │
│          │  │  tiles)   │
└────┬─────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            ▼
   ┌──────────────────┐
   │  React + MapLibre  │  (heatmap layer, crop filter, click-for-detail)
   │     Frontend        │
   └──────────────────┘
```

- **FastAPI** serves village detail + score breakdown for the click/hover panel (regular JSON).
- **Martin** serves the same data as vector tiles for fast map rendering at any zoom level — this is what makes a nationwide-eventually map performant instead of shipping one giant GeoJSON file.
- Both sit in front of the same PostGIS database; no data duplication.

---

## 3. Data Sources

| Data | Source | Resolution | License | Notes |
|---|---|---|---|---|
| Village boundaries (ADM4) | [HDX — Indonesia Subnational Administrative Boundaries](https://data.humdata.org/dataset/cod-ab-idn) | Vector, village-level | CC-BY (attribute to BPS) | ~83,000 villages nationwide; also cross-check against `Alf-Anas/batas-administrasi-indonesia` on GitHub as a backup source |
| Soil properties (pH, clay/sand/organic carbon) | [ISRIC SoilGrids v2.0](https://soilgrids.org) | 250m raster | CC-BY 4.0 | Bulk-download GeoTIFFs for the Indonesia extent rather than hitting the point-query REST API repeatedly — the API is explicitly beta/no-uptime-guarantee |
| Climate (temperature, rainfall normals) | [WorldClim v2.1](https://worldclim.org) | ~1km (30 arc-sec) raster | Free for research/non-commercial use — **verify current license terms before commercial use** | Static climatology, simplest to start with. CHIRPS is the alternative if you later need historical time-series/drought analysis |
| Elevation & slope | SRTM 30m DEM (via OpenTopography or USGS EarthExplorer) | 30m raster | Public domain (NASA) | Derive slope with GDAL from the raw DEM |
| Roads / market access proxy | OpenStreetMap Indonesia extract (via Geofabrik) | Vector | ODbL (open, requires attribution + share-alike on the *data*, not your code) | Used to compute distance-to-nearest-road/settlement per village |
| Existing crop production — Coffee, Cocoa (validation only, not a model input) | [Statistik Perkebunan Indonesia, Ditjenbun/Kementan](https://ditjenbun.pertanian.go.id) | Province/kabupaten aggregate | Open government publication | Used to sanity-check the model, not to train it — it's not spatially precise enough to be an input |
| Existing crop production — Sugarcane (validation only) | BPS **"Statistik Tanaman Perkebunan Semusim"** (annual/seasonal plantation crop series — a separate publication from the perennial-crop series above, since BPS classifies sugarcane and tobacco separately from tree crops) | Province/kabupaten aggregate | Open government publication | Same caveat as above — validation only |
| (Future) Village socioeconomic detail | BPS Podes (Village Potential Census) | Village-level | **Restricted — requires formal data-use agreement with BPS** | Needed eventually for "happiness/occupancy" layers. Not an MVP blocker — flagged for later |

⚠️ **License note (not legal advice):** OSM data is ODbL, which has share-alike implications for the *derived data* (not your application code). WorldClim's terms should be re-checked at the moment you go commercial. Worth 30 minutes of reading before you rely on either for a paid product.

---

## 4. Suitability Scoring Methodology

This is the part that needs to be defensible, not just "a number." The approach follows FAO's land evaluation framework (the same conceptual basis used in national agro-ecological zoning studies) rather than inventing scoring from scratch.

### 4.1 Per-factor scoring (fuzzy suitability curves)

For each factor (temperature, rainfall, elevation, soil pH, slope), define a **trapezoidal membership function** per crop, using known agronomic tolerance ranges (sourced from the FAO Ecocrop database and plantation-crop agronomy literature):

```
Score
100 |        ______________
    |       /              \
    |      /                \
    |     /                  \
  0 |____/                    \____
    Min  OptLow          OptHigh  Max     → factor value
```

- Below `Min` or above `Max`: score = 0 (crop essentially can't grow there)
- Between `OptLow` and `OptHigh`: score = 100 (ideal range)
- Ramping in between: linear interpolation

Example starting parameters (to be refined during Phase 2 calibration — these are illustrative, not final):

| Crop | Annual Rainfall (mm) optimal | Annual Mean Temp (°C) optimal | Elevation (m) optimal | Soil pH optimal |
|---|---|---|---|---|
| Coffee (Robusta) | 1,500–3,000 | 21–24 | 100–800 | 5.5–6.5 |
| Cocoa | 1,500–2,500 | 21–32 | 0–600 | 6.0–7.5 |
| Sugarcane | 1,500–2,500 | 24–30 | 0–800 | 6.0–7.5 |

### 4.2 Combining factors into one score

Not all factors matter equally, and a single fatal factor shouldn't be averaged away by good scores elsewhere (a swamp with perfect soil pH is still a swamp). So:

```
ClimateGate  = min(TemperatureScore, RainfallScore) / 100
SoilTerrainAccess = weighted_average(SoilScore, TerrainScore, AccessScore)
FinalScore   = ClimateGate × SoilTerrainAccess
```

- **Climate acts as a gate**, not just one input among many — if climate is fundamentally wrong for the crop, the final score should be low regardless of soil quality.
- **Soil/terrain/access are weighted and averaged** within climatically viable areas, since these are more about "how good" rather than "possible at all." Starting weights: soil 40%, terrain 30%, access 30% — adjustable per crop during calibration.

### 4.3 Calibration

After computing scores for the 3 pilot provinces, cross-check: do villages/kabupaten with historically high production (from Ditjenbun statistics) score highly? If not, revisit weights or ranges before trusting the output. Document this check — it's your strongest credibility evidence when you show this to anyone.

---

## 5. Repository Structure

```
taniscope/
├── data/
│   ├── raw/              # downloaded source data (gitignored, large files)
│   ├── processed/        # cleaned/clipped intermediate outputs
│   └── README.md         # source URLs, license, download date for every dataset
├── etl/
│   ├── scoring/           # crop parameter tables + fuzzy scoring functions
│   ├── zonal_stats.py
│   └── pipeline.py        # orchestrates the full ETL → PostGIS load
├── api/
│   ├── main.py             # FastAPI app
│   ├── models.py
│   └── routers/
├── frontend/
│   ├── src/
│   └── vite.config.ts
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/workflows/
├── LICENSE
├── README.md
└── docs/
    ├── 01_WALKTHROUGH.md
    ├── 02_TASKS.md
    └── 03_IMPLEMENTATION_PLAN.md   (these three files)
```

---

## 6. Local Development Setup (Linux + Antigravity IDE)

1. Clone the repo, open it in Antigravity IDE.
2. Install Docker + Docker Compose (if not already installed):
   ```bash
   sudo apt update && sudo apt install docker.io docker-compose-plugin
   ```
3. `docker compose up -d` — brings up PostGIS, FastAPI, and Martin locally.
4. Python ETL work: use a virtualenv (`python -m venv .venv && source .venv/bin/activate`) rather than installing geospatial packages system-wide — GDAL/GeoPandas dependencies can get messy otherwise.
5. Frontend: `cd frontend && npm install && npm run dev`.
6. Since Antigravity IDE is agent-first: it's well-suited to delegating self-contained tasks from `02_TASKS.md` one at a time (e.g., "implement the zonal stats function for soil pH, with unit tests") rather than the whole pipeline at once — smaller, verifiable tasks give the agent a tighter feedback loop and give you a reviewable diff per task.

---

## 7. Database Schema (starting point)

```sql
CREATE TABLE villages (
    id SERIAL PRIMARY KEY,
    adm4_pcode TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    kecamatan TEXT,
    kabupaten TEXT,
    province TEXT,
    resolution TEXT NOT NULL,  -- 'village' or 'coarse'
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX idx_villages_geom ON villages USING GIST (geom);

CREATE TABLE suitability_scores (
    id SERIAL PRIMARY KEY,
    village_id INTEGER REFERENCES villages(id),
    crop TEXT NOT NULL,
    score NUMERIC(5,2) NOT NULL,
    climate_score NUMERIC(5,2),
    soil_score NUMERIC(5,2),
    terrain_score NUMERIC(5,2),
    access_score NUMERIC(5,2),
    computed_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(village_id, crop)
);
```

---

## 8. API Endpoints (draft)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/villages/{id}` | Village metadata + all crop scores + factor breakdown |
| GET | `/scores?crop=coffee&bbox=minx,miny,maxx,maxy` | Scores within a map viewport (fallback if not using vector tiles for some client) |
| GET | `/tiles/{z}/{x}/{y}.pbf` | Proxied/handled by Martin, not FastAPI |

---

## 9. Deployment Plan & Budget

Target: **$20–50/month**

| Component | Recommendation | Est. Cost |
|---|---|---|
| VPS (DB + API + tiles, via Docker Compose) | Hetzner CX22 or DigitalOcean equivalent | ~$5–12/mo |
| Frontend hosting | Cloudflare Pages or Vercel (free tier) | $0 |
| Domain name | Any registrar | ~$1–2/mo amortized |
| HTTPS | Let's Encrypt via Caddy or Nginx | $0 |
| Monitoring | UptimeRobot free tier | $0 |
| **Buffer for growth** (bigger VPS as data grows) | — | remaining budget |

**Zero-cost validation option before committing budget:** Supabase's free tier includes PostGIS-enabled Postgres and could host the pilot-province dataset for initial testing before you provision a paid VPS.

---

## 10. License & Governance Recommendation

- **License: Apache 2.0.** Permissive enough for commercial use (compatible with a future paid tier or "open core" model), and its explicit patent grant is a meaningful protection a growing startup benefits from that plain MIT doesn't provide. MIT remains a fine simpler alternative if you never expect patent concerns.
- **Auth: none for v1.** Fully public, anonymous, read-only map. Add authentication only when you introduce something that actually needs it (saved views, a paid tier, write access) — building it now would be speculative effort.

---

## 11. Open Questions / Risks (be upfront about these)

1. **Scoring model accuracy** — this is an environmental suitability index, not validated yield data. Must be framed honestly to users/investors as "where the land is a good match," not "guaranteed yield."
2. **OSM/WorldClim license terms** — re-verify before any commercial launch.
3. **National scale-up cost** — going from 3 provinces to all of Indonesia at true village resolution will significantly increase storage/compute; the coarse-resolution fallback is the intended bridge, not a permanent limitation.
4. **PODES access** — the richest official village-level dataset (needed for the "happiness/occupancy" pillars) requires a formal BPS data-use agreement; start that conversation early if you want those pillars sooner rather than later.
