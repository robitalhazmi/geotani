# 🌾 GeoTani

**Open-source agricultural land suitability mapping & geospatial intelligence for Indonesia — village-level precision, zero cost.**

> *"geo" = spatial / mapping • "tani" (🇮🇩) = farmer / agriculture*

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Status](https://img.shields.io/badge/status-MVP%20in%20progress-orange.svg)

---

## What is GeoTani?

GeoTani is a free, open-source, map-based decision tool that shows **how suitable a location is for a specific crop** — rendered as a smooth heatmap across Indonesia at the village (*desa/kelurahan*) level.

Think of it as an "Open Source Palantir" for Indonesian agriculture: layer multi-criteria environmental data on an interactive vector map, filter by crop, and decide where to invest.

### MVP Scope

| Dimension | Scope |
|---|---|
| **Crops** | Coffee (Robusta), Cocoa, Sugarcane |
| **Geography** | 3 pilot provinces: Lampung, Sulawesi Selatan, Jawa Timur (village-level); rest of Indonesia at coarser resolution |
| **Output** | 0–100% suitability score per village, per crop |
| **Access** | Open to everyone, no login required |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data processing | Python 3.12, GeoPandas, Rasterio, rasterstats |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Backend API | FastAPI |
| Vector tiles | Martin Vector Tile Server |
| Frontend | React 19 + Vite + TypeScript + Tailwind CSS |
| Map renderer | MapLibre GL JS |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### Run locally

```bash
# Clone the repo
git clone https://github.com/robitalhazmi/taniscope.git geotani
cd geotani

# Copy environment variables
cp .env.example .env

# Start database + API + tile server
docker compose up -d

# Set up Python environment (for ETL/scoring work)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Start frontend dev server
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and the API at `http://localhost:8000`.

---

## Documentation

- [Tasks](docs/02_TASKS.md) — Phased task backlog & roadmap
- [Contributing](CONTRIBUTING.md) — Contribution guidelines and development workflow

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
