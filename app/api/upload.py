"""
Video Upload API endpoints
Handles video and thumbnail uploads to Cloudflare R2
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.video import Video, Category
from app.core.r2_storage import upload_file, delete_file, get_presigned_upload_url, R2_PUBLIC_URL
from sqlalchemy import select
from .notifications import notify_new_video

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/video", summary="Upload a video file")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    duration_seconds: int = Form(0),
    is_premium: bool = Form(False),
    is_featured: bool = Form(False),
    tags: str = Form(""),  # Comma-separated tags
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a video file to R2 and create a video record.
    Only instructors and admins can upload videos.
    """
    # Check if user is instructor or admin
    if current_user.role not in ['instructor', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can upload videos"
        )
    
    # Validate file type
    allowed_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Check file size (limit to 500MB)
    max_size = 500 * 1024 * 1024  # 500MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 500MB"
        )
    
    # Upload to R2
    success, key, public_url = await upload_file(
        file_content=content,
        original_filename=file.filename,
        folder="videos",
        content_type=file.content_type
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {public_url}"
        )
    
    # Get category
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        # Delete uploaded file
        await delete_file(key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
    
    # Create video record
    video = Video(
        title=title,
        description=description,
        video_url=public_url,
        video_key=key,  # Store R2 key for later deletion
        thumbnail_url="",  # Will be updated when thumbnail is uploaded
        duration_seconds=duration_seconds,
        instructor_id=current_user.id,
        category_id=category_id,
        is_premium=is_premium,
        is_featured=is_featured,
        is_published=True,
        tags=tag_list,
    )
    
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    return {
        "status": "success",
        "message": "Video uploaded successfully",
        "video": {
            "id": video.id,
            "title": video.title,
            "video_url": video.video_url,
            "category": category.name,
            "instructor": current_user.full_name,
        }
    }


@router.post("/thumbnail/{video_id}", summary="Upload a thumbnail for a video")
async def upload_thumbnail(
    video_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a thumbnail image for a video"""
    # Get video
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check ownership
    if video.instructor_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own videos"
        )
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Upload to R2
    content = await file.read()
    success, key, public_url = await upload_file(
        file_content=content,
        original_filename=file.filename,
        folder="thumbnails",
        content_type=file.content_type
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload thumbnail"
        )
    
    # Delete old thumbnail if exists
    if video.thumbnail_key:
        await delete_file(video.thumbnail_key)
    
    # Update video
    video.thumbnail_url = public_url
    video.thumbnail_key = key
    await db.commit()
    
    return {
        "status": "success",
        "message": "Thumbnail uploaded successfully",
        "thumbnail_url": public_url
    }


@router.get("/presigned-url", summary="Get a presigned URL for direct upload")
async def get_upload_url(
    filename: str,
    folder: str = "videos",
    current_user: User = Depends(get_current_user)
):
    """
    Get a presigned URL for direct upload from client.
    This allows uploading directly to R2 without going through the server.
    """
    if current_user.role not in ['instructor', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can upload"
        )
    
    url, key = await get_presigned_upload_url(filename, folder)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )
    
    # Generate the public URL
    if R2_PUBLIC_URL:
        public_url = f"{R2_PUBLIC_URL}/{key}"
    else:
        public_url = ""
    
    return {
        "upload_url": url,
        "key": key,
        "public_url": public_url,
        "expires_in": 3600
    }


@router.post("/register", summary="Register a video uploaded via presigned URL")
async def register_video(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    video_key: str = Form(...),  # The R2 key returned from presigned URL
    video_url: str = Form(...),  # The public URL of the video
    duration_seconds: int = Form(0),
    is_premium: bool = Form(False),
    thumbnail_url: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a video that was uploaded directly to R2 using a presigned URL.
    Call this after successfully uploading to R2.
    """
    if current_user.role not in ['instructor', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can upload videos"
        )
    
    # Get category
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Create video record
    video = Video(
        title=title,
        description=description,
        video_url=video_url,
        video_key=video_key,
        thumbnail_url=thumbnail_url,
        duration_seconds=duration_seconds,
        instructor_id=current_user.id,
        category_id=category_id,
        is_premium=is_premium,
        is_published=True,
    )
    
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # Send push notification to students about new video
    try:
        await notify_new_video(db, video)
    except Exception as e:
        # Don't fail the upload if notification fails
        print(f"Failed to send notification: {e}")
    
    return {
        "status": "success",
        "message": "Video registered successfully",
        "video": {
            "id": video.id,
            "title": video.title,
            "video_url": video.video_url,
            "category": category.name,
            "instructor": current_user.full_name,
        }
    }


@router.delete("/video/{video_id}", summary="Delete a video")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a video and its files from R2"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check ownership
    if video.instructor_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own videos"
        )
    
    # Delete files from R2
    if video.video_key:
        await delete_file(video.video_key)
    if video.thumbnail_key:
        await delete_file(video.thumbnail_key)
    
    # Delete from database
    await db.delete(video)
    await db.commit()
    
    return {
        "status": "success",
        "message": "Video deleted successfully"
    }
