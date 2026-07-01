import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.api import health, chat

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to validate configuration and build RAG indices on startup."""
    logger.info("Starting up SHL Assessment Recommender application...")
    
    # 1. Validate environment configuration
    try:
        settings.validate_keys()
        logger.info("Environment configuration validated successfully.")
    except ValueError as e:
        logger.error(f"Configuration Validation Error: {e}")
        # In a real production system we might let the app crash. 
        # For our developer sandbox, we print a warning and let the server run 
        # so they can debug or upload keys later.
        logger.warning("Application running without valid API credentials. Verify requests will fail.")
        
    # 2. Trigger FAISS Indexing at startup (pre-loads and builds index)
    try:
        from app.core.retriever import AssessmentRetriever
        # Initializing retriever forces catalog loading and FAISS construction
        AssessmentRetriever()
        logger.info("RAG vector index built and loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize FAISS index at startup: {e}")
        
    yield
    
    logger.info("Shutting down SHL Assessment Recommender application...")

# Initialize FastAPI with lifespan management
app = FastAPI(
    title="SHL Assessment Recommender API",
    description="Stateless Conversational agent helping recruiters match candidates with SHL tests.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware (crucial for local testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, tags=["monitoring"])
app.include_router(chat.router, tags=["chat"])

# Serve frontend static assets (css, js, assets)
frontend_dir = os.path.join(settings.BASE_DIR, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    logger.info(f"Mounted frontend assets from {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found at: {frontend_dir}. Root serving disabled.")

# Serve the main index.html dashboard file on the root URL
@app.get("/")
async def serve_dashboard():
    """Serves the main HTML5 frontend dashboard page."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to SHL Recommender API. Frontend folder is missing."}
