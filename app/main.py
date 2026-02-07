"""
Flight Academy API - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .core.config import settings
from .core.database import create_tables
from .api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle - startup and shutdown events"""
    # Startup: Create database tables
    await create_tables()
    
    # Create upload directories
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "thumbnails"), exist_ok=True)
    
    print(f"🛫 {settings.APP_NAME} v{settings.APP_VERSION} started!")
    print(f"📚 API docs: http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    print("🛬 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for Flight Academy - A video training platform for pilots",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*",  # Allow all for development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for video/image serving
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
