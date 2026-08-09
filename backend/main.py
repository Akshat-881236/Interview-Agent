import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.interview import router as interview_router

app = FastAPI(
    title="The Interview Agent API · AI Cohort",
    description="Personalized technical interview agent for AI Cohort learners featuring RAG, 2-pass LLM pipeline, and real-time proctoring.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(interview_router)

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "The Interview Agent API",
        "version": "2.1.0"
    }

# Serve Frontend static directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
