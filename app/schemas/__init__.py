"""
Pydantic schemas for API request/response validation
"""
from .user import (
    UserRole,
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    UserLogin,
    Token,
    PasswordChange,
)
from .video import (
    CategoryBase,
    CategoryCreate,
    CategoryResponse,
    VideoBase,
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoListResponse,
    ProgressUpdate,
    ProgressResponse,
    VideoUploadResponse,
)

__all__ = [
    "UserRole",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "UserLogin",
    "Token",
    "PasswordChange",
    "CategoryBase",
    "CategoryCreate",
    "CategoryResponse",
    "VideoBase",
    "VideoCreate",
    "VideoUpdate",
    "VideoResponse",
    "VideoListResponse",
    "ProgressUpdate",
    "ProgressResponse",
    "VideoUploadResponse",
]
