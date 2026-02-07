"""
Video Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    order: int

    class Config:
        from_attributes = True


# Video schemas
class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: List[str] = []
    is_premium: bool = False
    is_downloadable: bool = True


class VideoCreate(VideoBase):
    pass


class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    is_premium: Optional[bool] = None
    is_downloadable: Optional[bool] = None
    is_published: Optional[bool] = None


class VideoResponse(VideoBase):
    id: int
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: int
    duration_formatted: str
    file_size_bytes: int
    is_published: bool
    view_count: int
    like_count: int
    instructor_id: int
    instructor_name: str = ""
    category_name: str = ""
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    id: int
    title: str
    thumbnail_url: Optional[str] = None
    duration_formatted: str
    instructor_name: str
    category_name: str
    is_premium: bool
    view_count: int

    class Config:
        from_attributes = True


# Progress schemas
class ProgressUpdate(BaseModel):
    watched_seconds: int
    is_completed: bool = False


class ProgressResponse(BaseModel):
    video_id: int
    watched_seconds: int
    progress_percent: float
    is_completed: bool
    last_watched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Video upload response
class VideoUploadResponse(BaseModel):
    id: int
    title: str
    video_url: str
    thumbnail_url: Optional[str] = None
    message: str = "Video uploaded successfully"
