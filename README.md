# 🌾 TaniScope

**Open-source land suitability mapping for Indonesian agriculture — village-level precision, zero cost.**

> *"tani" (🇮🇩) = farmer • "scope" = lens / view*

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Status](https://img.shields.io/badge/status-MVP%20in%20progress-orange.svg)

---

## What is TaniScope?

TaniScope is a free, open-source, map-based decision tool that shows **how suitable a location is for a specific crop** — rendered as a smooth heatmap across Indonesia at the village (desa/kelurahan) level.

Think of it as an "Open Source Palantir" for agriculture: layer data on a map, filter by crop, and decide where to invest.

### MVP Scope

| Dimension | Scope |
|---|---|
| **Crops** | Coffee (Robusta), Cocoa, Sugarcane |
| **Geography** | 3 pilot provinces: Lampung, South Sulawesi, East Java (village-level); rest of Indonesia at coarser resolution |
| **Output** | 0–100% suitability score per village, per crop |
| **Access** | Open to everyone, no login required |

### Screenshot

*Coming soon — heatmap screenshot will go here.*

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data processing | Python 3.12, GeoPandas, Rasterio, rasterstats |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Backend API | FastAPI |
| Vector tiles | Martin |
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Map renderer | MapLibre GL JS |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+ (via nvm)

### Run locally

```bash
# Clone the repo
git clone https://github.com/robitalhazmi/taniscope.git
cd taniscope

# Copy environment variables
cp .env.example .env

# Start database + API + tile server
docker compose up -d

# Set up Python environment (for ETL/scoring work)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start frontend dev server
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and the API at `http://localhost:8000`.

---

## Documentation

- [Walkthrough](docs/01_WALKTHROUGH.md) — Vision, MVP scope, user journey
- [Tasks](docs/02_TASKS.md) — Phased task backlog
- [Implementation Plan](docs/03_IMPLEMENTATION_PLAN.md) — Architecture, scoring methodology, data sources

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and contribution guidelines.

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
