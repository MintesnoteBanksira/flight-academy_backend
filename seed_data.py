"""
Seed database with initial data for testing
"""
import asyncio
from app.core.database import async_session, create_tables
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.video import Category, Video


async def seed_database():
    """Seed the database with initial test data"""
    await create_tables()
    
    async with async_session() as db:
        # Check if data already exists
        from sqlalchemy import select
        result = await db.execute(select(User))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping...")
            return
        
        # Create categories
        categories = [
            Category(name="Pre-Flight", description="Pre-flight procedures and checks", icon="checklist", color="#4CAF50", order=1),
            Category(name="Takeoff", description="Takeoff procedures and techniques", icon="flight_takeoff", color="#2196F3", order=2),
            Category(name="Cruise", description="Cruise flight operations", icon="flight", color="#9C27B0", order=3),
            Category(name="Approach", description="Approach and landing preparation", icon="trending_down", color="#FF9800", order=4),
            Category(name="Landing", description="Landing techniques and procedures", icon="flight_land", color="#F44336", order=5),
            Category(name="Emergency", description="Emergency procedures and handling", icon="warning", color="#E91E63", order=6),
            Category(name="Systems", description="Aircraft systems knowledge", icon="settings", color="#00BCD4", order=7),
            Category(name="Navigation", description="Navigation and flight planning", icon="map", color="#795548", order=8),
        ]
        
        for cat in categories:
            db.add(cat)
        await db.flush()
        
        # Create instructor user
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
        
        # Create student user
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
        
        # Create admin user
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
        
        # Create sample videos
        videos = [
            Video(
                title="Pre-Flight Inspection Walkthrough",
                description="Complete walkthrough of the pre-flight inspection process. Learn what to check before every flight.",
                video_url="/uploads/videos/sample1.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",
                duration_seconds=1245,
                category_id=1,
                instructor_id=instructor.id,
                view_count=1250,
                is_published=True,
            ),
            Video(
                title="Takeoff Procedures - Normal Operations",
                description="Standard takeoff procedures for normal conditions. Covers V-speeds, rotation, and initial climb.",
                video_url="/uploads/videos/sample2.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1559628233-100c798642d4?w=800",
                duration_seconds=1830,
                category_id=2,
                instructor_id=instructor.id,
                view_count=980,
                is_published=True,
            ),
            Video(
                title="Emergency Engine Failure After Takeoff",
                description="Critical procedures for handling engine failure after takeoff. Memory items and decision making.",
                video_url="/uploads/videos/sample3.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1540962351504-03099e0a754b?w=800",
                duration_seconds=2150,
                category_id=6,
                instructor_id=instructor.id,
                view_count=2300,
                is_premium=True,
                is_published=True,
            ),
            Video(
                title="ILS Approach Step by Step",
                description="Detailed guide to flying an ILS approach. From approach briefing to landing.",
                video_url="/uploads/videos/sample4.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1474302770737-173ee21bab63?w=800",
                duration_seconds=2400,
                category_id=4,
                instructor_id=instructor.id,
                view_count=1800,
                is_published=True,
            ),
            Video(
                title="Understanding FMS Navigation",
                description="Flight Management System basics. Programming routes and using navigation features.",
                video_url="/uploads/videos/sample5.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?w=800",
                duration_seconds=1920,
                category_id=8,
                instructor_id=instructor.id,
                view_count=750,
                is_published=True,
            ),
            Video(
                title="Crosswind Landing Techniques",
                description="Master crosswind landings with proper crab and sideslip techniques.",
                video_url="/uploads/videos/sample6.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1529432067142-4c2ea0c15b94?w=800",
                duration_seconds=1650,
                category_id=5,
                instructor_id=instructor.id,
                view_count=2100,
                is_published=True,
            ),
            Video(
                title="Hydraulic System Deep Dive",
                description="Understanding aircraft hydraulic systems. Components, operation, and failure modes.",
                video_url="/uploads/videos/sample7.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
                duration_seconds=2700,
                category_id=7,
                instructor_id=instructor.id,
                view_count=450,
                is_premium=True,
                is_published=True,
            ),
            Video(
                title="Cruise Flight Optimization",
                description="Optimizing cruise performance. Cost index, step climbs, and fuel management.",
                video_url="/uploads/videos/sample8.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800",
                duration_seconds=1380,
                category_id=3,
                instructor_id=instructor.id,
                view_count=620,
                is_published=True,
            ),
        ]
        
        for video in videos:
            db.add(video)
        
        await db.commit()
        
        print("✅ Database seeded successfully!")
        print("📧 Test accounts:")
        print("   Instructor: captain@flightacademy.com / password123")
        print("   Student: student@flightacademy.com / password123")
        print("   Admin: admin@flightacademy.com / admin123")


if __name__ == "__main__":
    asyncio.run(seed_database())
