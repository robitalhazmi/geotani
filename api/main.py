"""TaniScope FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import HealthResponse, SuitabilityScore, Village
from api.routers import crops, scores, villages

app = FastAPI(
    title="TaniScope API",
    version="0.1.0",
    description="Open-source agricultural land suitability analytics for Indonesia.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(crops.router)
app.include_router(villages.router)
app.include_router(scores.router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def healthcheck(db: Session = Depends(get_db)):
    """Healthcheck endpoint verifying database connectivity and records count."""
    try:
        db.execute(text("SELECT 1;"))
        db_status = "connected"
        total_villages = db.query(func.count(Village.id)).scalar() or 0
        total_scores = db.query(func.count(SuitabilityScore.id)).scalar() or 0
    except Exception as e:
        db_status = f"disconnected: {e}"
        total_villages = 0
        total_scores = 0

    return HealthResponse(
        status="healthy" if "connected" in db_status else "degraded",
        version="0.1.0",
        database=db_status,
        total_villages=total_villages,
        total_scores=total_scores,
    )
