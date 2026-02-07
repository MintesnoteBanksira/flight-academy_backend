"""
Video API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import os
import aiofiles
from datetime import datetime
import uuid

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..models.video import Video, Category, VideoProgress
from ..schemas.video import (
    VideoResponse, VideoListResponse, VideoCreate, VideoUpdate,
    VideoUploadResponse, ProgressUpdate, ProgressResponse,
    CategoryResponse, CategoryCreate
)
from .deps import get_current_user, get_current_instructor, get_current_user_optional

router = APIRouter(prefix="/videos", tags=["Videos"])


# ============== PUBLIC ENDPOINTS ==============

@router.get("", response_model=List[VideoListResponse])
async def list_videos(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all published videos with optional filtering"""
    query = select(Video).where(Video.is_published == True)
    
    if category_id:
        query = query.where(Video.category_id == category_id)
    
    if search:
        query = query.where(Video.title.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit).order_by(Video.created_at.desc())
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    response = []
    for video in videos:
        # Get instructor name
        instructor_result = await db.execute(select(User).where(User.id == video.instructor_id))
        instructor = instructor_result.scalar_one_or_none()
        
        # Get category name
        category_name = ""
        if video.category_id:
            category_result = await db.execute(select(Category).where(Category.id == video.category_id))
            category = category_result.scalar_one_or_none()
            category_name = category.name if category else ""
        
        response.append(VideoListResponse(
            id=video.id,
            title=video.title,
            thumbnail_url=video.thumbnail_url,
            duration_formatted=video.duration_formatted,
            instructor_name=instructor.full_name if instructor else "Unknown",
            category_id=video.category_id,
            category_name=category_name,
            is_premium=video.is_premium,
            view_count=video.view_count,
        ))
    
    return response


@router.get("/featured", response_model=List[VideoListResponse])
async def get_featured_videos(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get featured/popular videos"""
    query = select(Video).where(
        Video.is_published == True
    ).order_by(Video.view_count.desc()).limit(limit)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    response = []
    for video in videos:
        instructor_result = await db.execute(select(User).where(User.id == video.instructor_id))
        instructor = instructor_result.scalar_one_or_none()
        
        category_name = ""
        if video.category_id:
            category_result = await db.execute(select(Category).where(Category.id == video.category_id))
            category = category_result.scalar_one_or_none()
            category_name = category.name if category else ""
        
        response.append(VideoListResponse(
            id=video.id,
            title=video.title,
            thumbnail_url=video.thumbnail_url,
            duration_formatted=video.duration_formatted,
            instructor_name=instructor.full_name if instructor else "Unknown",
            category_id=video.category_id,
            category_name=category_name,
            is_premium=video.is_premium,
            view_count=video.view_count,
        ))
    
    return response


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get video details by ID"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    if not video.is_published and (not current_user or current_user.id != video.instructor_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Increment view count
    video.view_count += 1
    await db.commit()
    
    # Get instructor
    instructor_result = await db.execute(select(User).where(User.id == video.instructor_id))
    instructor = instructor_result.scalar_one_or_none()
    
    # Get category
    category_name = ""
    if video.category_id:
        category_result = await db.execute(select(Category).where(Category.id == video.category_id))
        category = category_result.scalar_one_or_none()
        category_name = category.name if category else ""
    
    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        video_url=video.video_url,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        duration_formatted=video.duration_formatted,
        file_size_bytes=video.file_size_bytes,
        category_id=video.category_id,
        category_name=category_name,
        tags=video.tags,
        is_premium=video.is_premium,
        is_downloadable=video.is_downloadable,
        is_published=video.is_published,
        view_count=video.view_count,
        like_count=video.like_count,
        instructor_id=video.instructor_id,
        instructor_name=instructor.full_name if instructor else "Unknown",
        created_at=video.created_at,
        published_at=video.published_at,
    )


# ============== INSTRUCTOR ENDPOINTS ==============

@router.post("", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    is_premium: bool = Form(False),
    is_downloadable: bool = Form(True),
    video_file: UploadFile = File(...),
    thumbnail_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new video (instructor only)"""
    # Create upload directory if not exists
    upload_dir = os.path.join(settings.UPLOAD_DIR, "videos")
    thumbnail_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    # Generate unique filenames
    video_ext = os.path.splitext(video_file.filename)[1]
    video_filename = f"{uuid.uuid4()}{video_ext}"
    video_path = os.path.join(upload_dir, video_filename)
    
    # Save video file
    async with aiofiles.open(video_path, 'wb') as f:
        content = await video_file.read()
        await f.write(content)
    
    file_size = len(content)
    video_url = f"/uploads/videos/{video_filename}"
    
    # Save thumbnail if provided
    thumbnail_url = None
    if thumbnail_file:
        thumb_ext = os.path.splitext(thumbnail_file.filename)[1]
        thumb_filename = f"{uuid.uuid4()}{thumb_ext}"
        thumb_path = os.path.join(thumbnail_dir, thumb_filename)
        
        async with aiofiles.open(thumb_path, 'wb') as f:
            await f.write(await thumbnail_file.read())
        
        thumbnail_url = f"/uploads/thumbnails/{thumb_filename}"
    
    # Create video record
    new_video = Video(
        title=title,
        description=description,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        file_size_bytes=file_size,
        category_id=category_id,
        is_premium=is_premium,
        is_downloadable=is_downloadable,
        instructor_id=current_user.id,
        is_published=True,
        published_at=datetime.utcnow(),
    )
    
    db.add(new_video)
    await db.commit()
    await db.refresh(new_video)
    
    return VideoUploadResponse(
        id=new_video.id,
        title=new_video.title,
        video_url=new_video.video_url,
        thumbnail_url=new_video.thumbnail_url,
    )


@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Update video details (instructor only, own videos)"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    if video.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own videos",
        )
    
    update_data = video_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)
    
    await db.commit()
    await db.refresh(video)
    
    # Get instructor and category for response
    instructor_result = await db.execute(select(User).where(User.id == video.instructor_id))
    instructor = instructor_result.scalar_one_or_none()
    
    category_name = ""
    if video.category_id:
        category_result = await db.execute(select(Category).where(Category.id == video.category_id))
        category = category_result.scalar_one_or_none()
        category_name = category.name if category else ""
    
    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        video_url=video.video_url,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        duration_formatted=video.duration_formatted,
        file_size_bytes=video.file_size_bytes,
        category_id=video.category_id,
        category_name=category_name,
        tags=video.tags,
        is_premium=video.is_premium,
        is_downloadable=video.is_downloadable,
        is_published=video.is_published,
        view_count=video.view_count,
        like_count=video.like_count,
        instructor_id=video.instructor_id,
        instructor_name=instructor.full_name if instructor else "Unknown",
        created_at=video.created_at,
        published_at=video.published_at,
    )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Delete a video (instructor only, own videos)"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    if video.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own videos",
        )
    
    await db.delete(video)
    await db.commit()


@router.get("/instructor/my-videos", response_model=List[VideoListResponse])
async def get_my_videos(
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Get all videos uploaded by current instructor"""
    query = select(Video).where(
        Video.instructor_id == current_user.id
    ).order_by(Video.created_at.desc())
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    response = []
    for video in videos:
        category_name = ""
        if video.category_id:
            category_result = await db.execute(select(Category).where(Category.id == video.category_id))
            category = category_result.scalar_one_or_none()
            category_name = category.name if category else ""
        
        response.append(VideoListResponse(
            id=video.id,
            title=video.title,
            thumbnail_url=video.thumbnail_url,
            duration_formatted=video.duration_formatted,
            instructor_name=current_user.full_name,
            category_id=video.category_id,
            category_name=category_name,
            is_premium=video.is_premium,
            view_count=video.view_count,
        ))
    
    return response


# ============== PROGRESS TRACKING ==============

@router.post("/{video_id}/progress", response_model=ProgressResponse)
async def update_progress(
    video_id: int,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update watch progress for a video"""
    # Check video exists
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Get or create progress record
    progress_result = await db.execute(
        select(VideoProgress).where(
            VideoProgress.user_id == current_user.id,
            VideoProgress.video_id == video_id
        )
    )
    progress = progress_result.scalar_one_or_none()
    
    if not progress:
        progress = VideoProgress(
            user_id=current_user.id,
            video_id=video_id,
        )
        db.add(progress)
    
    # Update progress
    progress.watched_seconds = progress_data.watched_seconds
    progress.progress_percent = (progress_data.watched_seconds / video.duration_seconds * 100) if video.duration_seconds > 0 else 0
    progress.is_completed = progress_data.is_completed
    
    if progress_data.is_completed and not progress.completed_at:
        progress.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(progress)
    
    return ProgressResponse(
        video_id=progress.video_id,
        watched_seconds=progress.watched_seconds,
        progress_percent=progress.progress_percent,
        is_completed=progress.is_completed,
        last_watched_at=progress.last_watched_at,
    )


@router.get("/{video_id}/progress", response_model=ProgressResponse)
async def get_progress(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get watch progress for a video"""
    progress_result = await db.execute(
        select(VideoProgress).where(
            VideoProgress.user_id == current_user.id,
            VideoProgress.video_id == video_id
        )
    )
    progress = progress_result.scalar_one_or_none()
    
    if not progress:
        return ProgressResponse(
            video_id=video_id,
            watched_seconds=0,
            progress_percent=0.0,
            is_completed=False,
            last_watched_at=None,
        )
    
    return ProgressResponse(
        video_id=progress.video_id,
        watched_seconds=progress.watched_seconds,
        progress_percent=progress.progress_percent,
        is_completed=progress.is_completed,
        last_watched_at=progress.last_watched_at,
    )
