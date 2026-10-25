import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.sentry import init_sentry
from app.db.database import init_db
from app.api.routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("replylater")

# Initialize Sentry with AI Agent Tracing
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and pgvector extension are created
    logger.info("Initializing ReplyLater database...")
    await init_db()
    logger.info("ReplyLater backend ready to triage emails.")
    yield
    logger.info("Shutting down ReplyLater backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Local-first overnight email co-pilot built for Hacktoberfest DEV Challenge.",
    lifespan=lifespan,
)

# CORS middleware for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "project": "ReplyLater",
        "description": "Slow and Steady: Channel Your Inner Sloth - Overnight Email Co-Pilot",
        "privacy": "0 KB cloud egress for email bodies. All LLM inference runs locally via Ollama.",
        "docs_url": "/docs",
        "board_api": "/api/board",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
