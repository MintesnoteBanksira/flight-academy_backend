"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Flight Academy API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    # For development (SQLite), for production use DATABASE_URL env var
    DATABASE_URL: str = "sqlite+aiosqlite:///./flight_academy.db"
    
    @property
    def async_database_url(self) -> str:
        """Convert DATABASE_URL to async version if needed"""
        url = self.DATABASE_URL
        # Handle PostgreSQL URLs from Render or Aiven
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Remove sslmode from URL as asyncpg handles SSL differently
        if "?sslmode=" in url:
            url = url.split("?sslmode=")[0]
        elif "&sslmode=" in url:
            url = url.replace("&sslmode=require", "").replace("&sslmode=prefer", "")
        return url
    
    @property
    def is_production(self) -> bool:
        """Check if running in production (PostgreSQL)"""
        return "postgresql" in self.DATABASE_URL or "postgres" in self.DATABASE_URL
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB for videos
    ALLOWED_VIDEO_TYPES: list = ["video/mp4", "video/quicktime", "video/x-msvideo"]
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]
    
    # PythonAnywhere specific
    PYTHONANYWHERE_USERNAME: Optional[str] = None
    
    # Firebase Cloud Messaging
    FCM_SERVER_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
