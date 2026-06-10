"""
FastAPI backend — Logistics AI Algorithm Pipeline
DAA Semester 4

Run:
    cd logistics_ai_project
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULT_FILE = DATA_DIR / "current_result.json"

# ---------------------------------------------------------------------------
app = FastAPI(
    title="Logistics AI — Algorithm Pipeline",
    description="Backend to serve pre-calculated pipeline results from demo.py",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "2.1.0"}


@app.get("/result")
def get_result() -> dict:
    """
    Return the pre-calculated pipeline results saved by demo.py.
    """
    if not RESULT_FILE.exists():
        raise HTTPException(status_code=404, detail="Result file not found. Run demo.py first.")
    
    try:
        with open(RESULT_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Serve frontend (mount last so API routes take priority)
# ---------------------------------------------------------------------------
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
