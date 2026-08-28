# Contributing to TaniScope

Thank you for your interest in contributing! TaniScope is an open-source project and we welcome contributions of all kinds.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+ (recommend installing via [nvm](https://github.com/nvm-sh/nvm))
- Docker & Docker Compose
- Git

### Setup

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/taniscope.git
   cd taniscope
   ```
3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
4. Start services:
   ```bash
   docker compose up -d
   ```
5. Set up Python environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
6. Set up frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Branch Naming Convention

Create a branch from `main` with one of these prefixes:

- `feature/` — new features (e.g., `feature/crop-filter-ui`)
- `fix/` — bug fixes (e.g., `fix/score-calculation-overflow`)
- `data/` — data pipeline changes (e.g., `data/add-soilgrids-download`)
- `docs/` — documentation updates (e.g., `docs/update-readme`)
- `chore/` — tooling, CI, dependency updates (e.g., `chore/update-dependencies`)

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes in small, focused commits
3. Ensure all lints pass: `ruff check .` (Python) and `npm run lint` (frontend)
4. Ensure tests pass: `pytest` (Python)
5. Open a PR against `main` with a clear description of what changed and why
6. Wait for CI to pass and a review

## Code Style

### Python
- Formatter: [Black](https://github.com/psf/black) (default settings)
- Linter: [Ruff](https://github.com/astral-sh/ruff)
- Type hints encouraged but not strictly enforced in the MVP phase

### Frontend (TypeScript/React)
- ESLint with the default Vite + React configuration
- Prefer functional components and hooks

## Questions?

Open an issue on GitHub or start a discussion. We're happy to help!
