"""Vehicle ML Agent – FastAPI application entry point.

This application combines:
1. Image classification – detecting vehicle types using a pretrained MobileNetV2.
2. AI Agent – translating natural language questions to SQL queries using OpenAI GPT-4o-mini.

Run with:
    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import router as api_router
from app.classifier.service import classifier
from app.db.seed import seed_database
from app.limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting up – seeding database …")
    await seed_database()

    logger.info("Pre-loading classifier model …")
    classifier.load()

    logger.info("Application ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Vehicle ML Agent",
    description=(
        "Aplikacja łącząca klasyfikację obrazów pojazdów (MobileNetV2) "
        "z agentem AI tłumaczącym pytania w języku naturalnym na zapytania SQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS – allow all origins for demo (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)

# Mount static files for sample images
SAMPLE_DIR = BASE_DIR / "sample_images"
if SAMPLE_DIR.exists():
    app.mount("/sample_images", StaticFiles(directory=str(SAMPLE_DIR)), name="sample_images")


# ── Frontend serving ────────────────────────────────────────────────────────

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    # Production: serve React build from frontend/dist/
    logger.info("Serving React frontend from %s", FRONTEND_DIST)

    # Mount static assets (JS, CSS, images) under /assets
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA – return index.html for all non-API routes (client-side routing)."""
        # Try to serve static file first
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise return SPA entry point
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    # Development fallback: serve Jinja2 template
    logger.info("React build not found – serving Jinja2 fallback template")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Serve the legacy web UI."""
        return templates.TemplateResponse("index.html", {"request": request})

