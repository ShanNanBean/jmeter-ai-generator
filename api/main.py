"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.routes import generation, preview, validation, config
from api.middleware.error_handler import add_error_handler

app = FastAPI(
    title="JMeter AI Generator",
    version="0.1.0",
    description="AI-powered JMeter test script generator",
)

# CORS — open for iframe embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_error_handler(app)

app.include_router(generation.router, prefix="/api/v1/generation", tags=["generation"])
app.include_router(preview.router, prefix="/api/v1/preview", tags=["preview"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])

# Mount frontend static files if dist exists
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")
if os.path.exists(dist_dir):
    app.mount("/static", StaticFiles(directory=dist_dir, html=True), name="static")