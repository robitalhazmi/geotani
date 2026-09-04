# 🌾 GeoTani

**Open-source agricultural land suitability mapping & geospatial intelligence for Indonesia — village-level precision, zero cost.**

> *"geo" = spatial / mapping • "tani" (🇮🇩) = farmer / agriculture*

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Status](https://img.shields.io/badge/status-MVP%20in%20progress-orange.svg)

---

## What is GeoTani?

GeoTani is a free, open-source, map-based decision tool that shows **how suitable a location is for a specific crop** — rendered as a smooth heatmap across Indonesia at the village (*desa/kelurahan*) level.

An interactive geospatial intelligence platform for Indonesian agriculture: layer multi-criteria environmental data on a vector map, filter by crop suitability, and make data-driven agricultural decisions.

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
git clone https://github.com/robitalhazmi/geotani.git
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

### Production Deployment (VPS)

To deploy to production on a VPS (e.g. Rumahweb, Hetzner, DigitalOcean) with automated HTTPS on `geotani.cloud`:

```bash
# 1. Clone the repository on your server
git clone https://github.com/robitalhazmi/geotani.git /opt/geotani
cd /opt/geotani

# 2. Run the automated deployment script
./scripts/deploy.sh
```

#### Seeding Database on Fresh VPS

Since raw and processed geospatial datasets are not checked into Git, run the automated end-to-end data pipeline directly on the VPS to download boundaries, extract environmental factors, compute crop suitability scores, and load them into PostGIS:

```bash
# Run the complete automated ETL pipeline inside the API container:
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm api ./scripts/run_etl_pipeline.sh
```

---

### Share Live Demo on the Internet

To instantly generate a secure public HTTPS URL to share your live local map with external stakeholders:

```bash
# Option 1: Run the interactive share script
./scripts/share_demo.sh

# Option 2: Run via npm in frontend directory
cd frontend && npm run share

# Option 3: Run via ngrok
ngrok http 5173
```

---

## Documentation

- [Walkthrough](docs/01_WALKTHROUGH.md) — Vision, MVP scope, user journey
- [Tasks](docs/02_TASKS.md) — Phased task backlog & roadmap
- [Implementation Plan](docs/03_IMPLEMENTATION_PLAN.md) — Architecture, scoring methodology, data sources
- [Production Deployment Guide](docs/04_DEPLOYMENT_GUIDE.md) — VPS setup, automated HTTPS on `geotani.cloud`, and operations

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and contribution guidelines.

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
