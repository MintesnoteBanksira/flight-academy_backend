"""
Admin API endpoints - Database seeding and management
Version: 2.0 - Added clear and reset endpoints
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
async def seed_database(force: bool = False, db: AsyncSession = Depends(get_db)):
    """
    Seed the database with initial test data.
    WARNING: This will skip if data already exists unless force=True.
    """
    # Check if data already exists
    result = await db.execute(select(Category))
    existing_category = result.scalar_one_or_none()
    
    if existing_category and not force:
        return {
            "status": "skipped",
            "message": "Database already has categories. Use ?force=true to re-seed."
        }
    
    # Create tables if they don't exist
    await create_tables()
    
    # Create categories (check if each exists first)
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
    
    categories_created = 0
    for cat_data in categories_data:
        # Check if category already exists
        existing = await db.execute(select(Category).where(Category.name == cat_data["name"]))
        if not existing.scalar_one_or_none():
            category = Category(**cat_data)
            db.add(category)
            categories_created += 1
    
    await db.flush()
    
    # Create users (check if each exists first)
    users_created = 0
    
    existing_instructor = await db.execute(select(User).where(User.email == "captain@flightacademy.com"))
    if not existing_instructor.scalar_one_or_none():
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
        users_created += 1
    
    existing_student = await db.execute(select(User).where(User.email == "student@flightacademy.com"))
    if not existing_student.scalar_one_or_none():
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
        users_created += 1
    
    existing_admin = await db.execute(select(User).where(User.email == "admin@flightacademy.com"))
    if not existing_admin.scalar_one_or_none():
        admin = User(
            email="admin@flightacademy.com",
            hashed_password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_verified=True,
        )
        db.add(admin)
        users_created += 1
    
    await db.commit()
    
    # No demo videos - you'll upload real ones via the app
    
    return {
        "status": "success",
        "message": f"Database seeded! Created {categories_created} categories and {users_created} users.",
        "data": {
            "users_created": users_created,
            "categories_created": categories_created,
            "videos": 0,
        },
        "test_accounts": {
            "instructor": {"email": "captain@flightacademy.com", "password": "password123"},
            "student": {"email": "student@flightacademy.com", "password": "password123"},
            "admin": {"email": "admin@flightacademy.com", "password": "admin123"},
        },
        "note": "Upload your own videos via the instructor panel!"
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
