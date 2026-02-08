"""
Statistics API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from ..core.database import get_db
from ..models.user import User
from ..models.video import Video, VideoProgress
from .deps import get_current_user, get_current_instructor

router = APIRouter(prefix="/stats", tags=["Statistics"])


# ============== STUDENT STATS ==============

@router.get("/my-progress")
async def get_my_progress_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's learning progress stats"""
    # Get all progress records for the user
    progress_result = await db.execute(
        select(VideoProgress).where(VideoProgress.user_id == current_user.id)
    )
    all_progress = progress_result.scalars().all()
    
    # Calculate stats
    completed_count = sum(1 for p in all_progress if p.is_completed)
    in_progress_count = sum(1 for p in all_progress if not p.is_completed and p.watched_seconds > 0)
    total_watch_seconds = sum(p.watched_seconds for p in all_progress)
    
    # Format watch time
    total_watch_hours = total_watch_seconds / 3600
    if total_watch_hours >= 1:
        watch_time_formatted = f"{total_watch_hours:.1f}h"
    else:
        watch_time_formatted = f"{total_watch_seconds // 60}m"
    
    return {
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "total_watch_seconds": total_watch_seconds,
        "watch_time_formatted": watch_time_formatted,
    }


@router.get("/my-videos-in-progress")
async def get_my_videos_in_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get videos that the user has started but not completed"""
    # Get in-progress videos
    progress_result = await db.execute(
        select(VideoProgress).where(
            VideoProgress.user_id == current_user.id,
            VideoProgress.is_completed == False,
            VideoProgress.watched_seconds > 0
        ).order_by(VideoProgress.last_watched_at.desc())
    )
    in_progress = progress_result.scalars().all()
    
    videos_with_progress = []
    for p in in_progress:
        video_result = await db.execute(select(Video).where(Video.id == p.video_id))
        video = video_result.scalar_one_or_none()
        if video and video.is_published:
            # Get instructor
            instructor_result = await db.execute(select(User).where(User.id == video.instructor_id))
            instructor = instructor_result.scalar_one_or_none()
            
            videos_with_progress.append({
                "video_id": video.id,
                "title": video.title,
                "thumbnail_url": video.thumbnail_url,
                "instructor_name": instructor.full_name if instructor else "Unknown",
                "progress_percent": p.progress_percent,
                "watched_seconds": p.watched_seconds,
                "last_watched_at": p.last_watched_at.isoformat() if p.last_watched_at else None,
            })
    
    return videos_with_progress


@router.get("/my-completed-videos")
async def get_my_completed_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get videos that the user has completed"""
    # Get completed videos
    progress_result = await db.execute(
        select(VideoProgress).where(
            VideoProgress.user_id == current_user.id,
            VideoProgress.is_completed == True
        ).order_by(VideoProgress.completed_at.desc())
    )
    completed = progress_result.scalars().all()
    
    videos = []
    for p in completed:
        video_result = await db.execute(select(Video).where(Video.id == p.video_id))
        video = video_result.scalar_one_or_none()
        if video:
            videos.append({
                "video_id": video.id,
                "title": video.title,
                "thumbnail_url": video.thumbnail_url,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            })
    
    return videos


# ============== INSTRUCTOR STATS ==============

@router.get("/instructor")
async def get_instructor_stats(
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Get instructor's dashboard stats"""
    # Get total videos count
    video_count_result = await db.execute(
        select(func.count()).select_from(Video).where(Video.instructor_id == current_user.id)
    )
    total_videos = video_count_result.scalar() or 0
    
    # Get total views across all videos
    views_result = await db.execute(
        select(func.sum(Video.view_count)).where(Video.instructor_id == current_user.id)
    )
    total_views = views_result.scalar() or 0
    
    # Get unique students who watched instructor's videos
    students_result = await db.execute(
        select(func.count(func.distinct(VideoProgress.user_id)))
        .select_from(VideoProgress)
        .join(Video, VideoProgress.video_id == Video.id)
        .where(Video.instructor_id == current_user.id)
    )
    active_students = students_result.scalar() or 0
    
    # Get average rating (we don't have ratings yet, so return 0)
    avg_rating = 0.0
    
    # Format views
    if total_views >= 1_000_000:
        views_formatted = f"{total_views / 1_000_000:.1f}M"
    elif total_views >= 1_000:
        views_formatted = f"{total_views / 1_000:.1f}K"
    else:
        views_formatted = str(total_views)
    
    return {
        "total_videos": total_videos,
        "total_views": total_views,
        "views_formatted": views_formatted,
        "active_students": active_students,
        "avg_rating": avg_rating,
    }


@router.get("/instructor/recent-activity")
async def get_instructor_recent_activity(
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """Get instructor's recent activity"""
    activities = []
    
    # Get recently uploaded videos
    recent_videos_result = await db.execute(
        select(Video).where(Video.instructor_id == current_user.id)
        .order_by(Video.created_at.desc()).limit(3)
    )
    recent_videos = recent_videos_result.scalars().all()
    
    for video in recent_videos:
        activities.append({
            "type": "upload",
            "message": f"Uploaded '{video.title}'",
            "timestamp": video.created_at.isoformat(),
            "icon": "upload",
        })
    
    # Get videos that reached view milestones
    milestone_videos_result = await db.execute(
        select(Video).where(
            Video.instructor_id == current_user.id,
            Video.view_count >= 100
        ).order_by(Video.view_count.desc()).limit(3)
    )
    milestone_videos = milestone_videos_result.scalars().all()
    
    for video in milestone_videos:
        if video.view_count >= 1000:
            views_str = f"{video.view_count // 1000}K"
        else:
            views_str = str(video.view_count)
        activities.append({
            "type": "milestone",
            "message": f"'{video.title}' reached {views_str} views",
            "timestamp": video.created_at.isoformat(),
            "icon": "visibility",
        })
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]


@router.get("/instructor/top-students")
async def get_instructor_top_students(
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db),
    limit: int = 5
):
    """Get top performing students for instructor's videos"""
    # Get students who watched instructor's videos, with their progress
    # This is a complex query - we need to aggregate progress per student
    from sqlalchemy import and_
    
    # Get all progress for instructor's videos
    progress_result = await db.execute(
        select(VideoProgress, Video, User)
        .join(Video, VideoProgress.video_id == Video.id)
        .join(User, VideoProgress.user_id == User.id)
        .where(Video.instructor_id == current_user.id)
    )
    all_progress = progress_result.all()
    
    # Aggregate by student
    student_stats = {}
    for progress, video, student in all_progress:
        if student.id not in student_stats:
            student_stats[student.id] = {
                "user_id": student.id,
                "name": student.full_name,
                "completed_count": 0,
                "watch_seconds": 0,
            }
        student_stats[student.id]["watch_seconds"] += progress.watched_seconds
        if progress.is_completed:
            student_stats[student.id]["completed_count"] += 1
    
    # Convert to list and sort by completed count
    students_list = list(student_stats.values())
    students_list.sort(key=lambda x: (x["completed_count"], x["watch_seconds"]), reverse=True)
    
    # Format and return top students
    result = []
    for student in students_list[:limit]:
        hours = student["watch_seconds"] / 3600
        result.append({
            "name": student["name"],
            "completed_count": student["completed_count"],
            "watch_hours": round(hours, 1),
        })
    
    return result
