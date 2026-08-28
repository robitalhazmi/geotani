"""TaniScope API — FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TaniScope API",
    description="Open-source land suitability mapping for Indonesian agriculture",
    version="0.1.0",
)

# Allow frontend dev server to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Liveness check."""
    return {"status": "ok", "service": "taniscope-api"}
