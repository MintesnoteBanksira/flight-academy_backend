"""
Video and Category database models
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon name for Flutter
    color = Column(String(7), nullable=True)  # Hex color code
    order = Column(Integer, default=0)
    
    # Relationships
    videos = relationship("Video", back_populates="category")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File info
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    
    # Metadata
    is_premium = Column(Boolean, default=False)
    is_downloadable = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    
    # Categorization
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, default=list)  # List of tag strings
    
    # Instructor
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Stats
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    category = relationship("Category", back_populates="videos")
    instructor = relationship("User", back_populates="videos")
    progress = relationship("VideoProgress", back_populates="video")

    @property
    def duration_formatted(self) -> str:
        """Format duration as MM:SS or HH:MM:SS"""
        minutes, seconds = divmod(self.duration_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class VideoProgress(Base):
    __tablename__ = "video_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    # Progress tracking
    watched_seconds = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_watched_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    video = relationship("Video", back_populates="progress")
