"""
Admin API endpoints - Database seeding and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db, create_tables
from ..core.security import get_password_hash
from ..models.user import User, UserRole
from ..models.video import Category, Video

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_database(db: AsyncSession = Depends(get_db)):
    """
    Seed the database with initial test data.
    WARNING: This will skip if data already exists.
    """
    # Check if data already exists
    result = await db.execute(select(User))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return {
            "status": "skipped",
            "message": "Database already has data. Skipping seed."
        }
    
    # Create tables if they don't exist
    await create_tables()
    
    # Create categories
    categories_data = [
        {"name": "Pre-Flight", "description": "Pre-flight procedures and checks", "icon": "checklist", "color": "#4CAF50", "order": 1},
        {"name": "Takeoff", "description": "Takeoff procedures and techniques", "icon": "flight_takeoff", "color": "#2196F3", "order": 2},
        {"name": "Cruise", "description": "Cruise flight operations", "icon": "flight", "color": "#9C27B0", "order": 3},
        {"name": "Approach", "description": "Approach and landing preparation", "icon": "trending_down", "color": "#FF9800", "order": 4},
        {"name": "Landing", "description": "Landing techniques and procedures", "icon": "flight_land", "color": "#F44336", "order": 5},
        {"name": "Emergency", "description": "Emergency procedures and handling", "icon": "warning", "color": "#E91E63", "order": 6},
        {"name": "Systems", "description": "Aircraft systems knowledge", "icon": "settings", "color": "#00BCD4", "order": 7},
        {"name": "Navigation", "description": "Navigation and flight planning", "icon": "map", "color": "#795548", "order": 8},
    ]
    
    categories = []
    for cat_data in categories_data:
        category = Category(**cat_data)
        db.add(category)
        categories.append(category)
    
    await db.flush()
    
    # Create users
    instructor = User(
        email="captain@flightacademy.com",
        hashed_password=get_password_hash("password123"),
        first_name="Captain",
        last_name="Smith",
        role=UserRole.INSTRUCTOR,
        rank="Captain",
        airline="Flight Academy",
        is_verified=True,
    )
    db.add(instructor)
    
    student = User(
        email="student@flightacademy.com",
        hashed_password=get_password_hash("password123"),
        first_name="John",
        last_name="Pilot",
        role=UserRole.STUDENT,
        rank="First Officer",
        airline="Flight Academy",
        is_verified=True,
    )
    db.add(student)
    
    admin = User(
        email="admin@flightacademy.com",
        hashed_password=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db.add(admin)
    
    await db.flush()
    
    # Create videos
    videos_data = [
        {
            "title": "Pre-Flight Inspection Walkthrough",
            "description": "Complete walkthrough of the pre-flight inspection process. Learn what to check before every flight.",
            "video_url": "/uploads/videos/sample1.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",
            "duration_seconds": 1245,
            "category_id": 1,
            "instructor_id": instructor.id,
            "view_count": 1250,
            "is_published": True,
        },
        {
            "title": "Takeoff Procedures - Normal Operations",
            "description": "Standard takeoff procedures for normal conditions. Covers V-speeds, rotation, and initial climb.",
            "video_url": "/uploads/videos/sample2.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1559628233-100c798642d4?w=800",
            "duration_seconds": 1830,
            "category_id": 2,
            "instructor_id": instructor.id,
            "view_count": 980,
            "is_published": True,
        },
        {
            "title": "Emergency Engine Failure After Takeoff",
            "description": "Critical procedures for handling engine failure after takeoff. Memory items and decision making.",
            "video_url": "/uploads/videos/sample3.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1540962351504-03099e0a754b?w=800",
            "duration_seconds": 2150,
            "category_id": 6,
            "instructor_id": instructor.id,
            "view_count": 2300,
            "is_premium": True,
            "is_published": True,
        },
        {
            "title": "ILS Approach Step by Step",
            "description": "Detailed guide to flying an ILS approach. From approach briefing to landing.",
            "video_url": "/uploads/videos/sample4.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1474302770737-173ee21bab63?w=800",
            "duration_seconds": 2400,
            "category_id": 4,
            "instructor_id": instructor.id,
            "view_count": 1800,
            "is_published": True,
        },
        {
            "title": "Understanding FMS Navigation",
            "description": "Flight Management System basics. Programming routes and using navigation features.",
            "video_url": "/uploads/videos/sample5.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?w=800",
            "duration_seconds": 1920,
            "category_id": 8,
            "instructor_id": instructor.id,
            "view_count": 750,
            "is_published": True,
        },
        {
            "title": "Crosswind Landing Techniques",
            "description": "Master crosswind landings with proper crab and sideslip techniques.",
            "video_url": "/uploads/videos/sample6.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1529432067142-4c2ea0c15b94?w=800",
            "duration_seconds": 1650,
            "category_id": 5,
            "instructor_id": instructor.id,
            "view_count": 2100,
            "is_published": True,
        },
        {
            "title": "Hydraulic System Deep Dive",
            "description": "Understanding aircraft hydraulic systems. Components, operation, and failure modes.",
            "video_url": "/uploads/videos/sample7.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
            "duration_seconds": 2700,
            "category_id": 7,
            "instructor_id": instructor.id,
            "view_count": 450,
            "is_premium": True,
            "is_published": True,
        },
        {
            "title": "Cruise Flight Optimization",
            "description": "Optimizing cruise performance. Cost index, step climbs, and fuel management.",
            "video_url": "/uploads/videos/sample8.mp4",
            "thumbnail_url": "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800",
            "duration_seconds": 1380,
            "category_id": 3,
            "instructor_id": instructor.id,
            "view_count": 620,
            "is_published": True,
        },
    ]
    
    for video_data in videos_data:
        video = Video(**video_data)
        db.add(video)
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "Database seeded successfully!",
        "data": {
            "users": 3,
            "categories": 8,
            "videos": 8,
        },
        "test_accounts": {
            "instructor": {"email": "captain@flightacademy.com", "password": "password123"},
            "student": {"email": "student@flightacademy.com", "password": "password123"},
            "admin": {"email": "admin@flightacademy.com", "password": "admin123"},
        }
    }


@router.get("/stats")
async def get_database_stats(db: AsyncSession = Depends(get_db)):
    """Get database statistics"""
    from sqlalchemy import func
    
    users_count = await db.execute(select(func.count(User.id)))
    videos_count = await db.execute(select(func.count(Video.id)))
    categories_count = await db.execute(select(func.count(Category.id)))
    
    return {
        "users": users_count.scalar() or 0,
        "videos": videos_count.scalar() or 0,
        "categories": categories_count.scalar() or 0,
    }


@router.delete("/clear-demo-videos")
async def clear_demo_videos(db: AsyncSession = Depends(get_db)):
    """
    Clear all demo/seed videos (those with sample URLs).
    Keeps real uploaded videos (those with R2 URLs).
    """
    from sqlalchemy import delete, or_
    
    # Delete videos that have demo URLs (not R2 URLs)
    result = await db.execute(
        delete(Video).where(
            or_(
                Video.video_url.like("/uploads/%"),
                Video.video_url.like("https://images.unsplash%"),
                Video.video_url == "",
                Video.video_url.is_(None),
                ~Video.video_url.like("%r2.dev%")  # Keep R2 videos
            )
        ).where(
            Video.video_url.notlike("%pub-915af40a190e4aaeae419a28034c0a3a.r2.dev%")
        )
    )
    
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Cleared demo videos",
        "deleted_count": result.rowcount
    }


@router.delete("/clear-all-videos")
async def clear_all_videos(db: AsyncSession = Depends(get_db)):
    """
    Clear ALL videos from the database.
    WARNING: This deletes everything!
    """
    from sqlalchemy import delete
    
    result = await db.execute(delete(Video))
    await db.commit()
    
    return {
        "status": "success",
        "message": "All videos cleared",
        "deleted_count": result.rowcount
    }


@router.post("/reset-database")
async def reset_database(db: AsyncSession = Depends(get_db)):
    """
    Reset database: Clear all videos and re-seed with just users and categories.
    Keeps your account but removes all videos.
    """
    from sqlalchemy import delete
    
    # Delete all videos
    await db.execute(delete(Video))
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "Database reset - all videos removed. Categories and users preserved.",
        "note": "You can now upload fresh videos."
    }
