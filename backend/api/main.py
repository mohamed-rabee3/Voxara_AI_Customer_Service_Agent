"""
FastAPI Main Application

Entry point for the Voara Voice Agent REST API.
Handles token generation and health checks.
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import token, health, rag
from rag import get_qdrant_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for resource management.
    """
    # Startup
    logger.info("Starting Voara Voice Agent API...")
    
    # Initialize Qdrant connection
    qdrant = get_qdrant_service()
    try:
        # Verify connection works
        exists = await qdrant.collection_exists()
        if exists:
            logger.info("Connected to Qdrant - collection exists")
        else:
            logger.warning("Qdrant collection does not exist - run ingestion script first")
    except Exception as e:
        logger.warning(f"Could not connect to Qdrant: {e}")
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voara Voice Agent API...")
    
    # Close Qdrant connection
    await qdrant.close()
    
    logger.info("API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Voara Voice Agent API",
    description="REST API for the Voara AI Voice Agent with LiveKit and RAG",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Local Next.js dev
        "http://127.0.0.1:3000",           # Alternative localhost
        "https://voxara-ai-customer-service-agent.vercel.app",  # Production Vercel
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # All Vercel preview deployments
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers
app.include_router(token.router, prefix="/api", tags=["Token"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Voara Voice Agent API",
        "version": "0.1.0",
        "docs": "/docs"
    }


def start():
    """Entry point for poetry script."""
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    start()
