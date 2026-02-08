"""
Notification API endpoints
"""
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..core.database import get_db
from ..core.config import settings
from ..models import User, DeviceRegistration, NotificationPreference, Notification, NotificationType, Video
from .deps import get_current_user

router = APIRouter()


# --- Schemas ---

class DeviceRegistrationRequest(BaseModel):
    fcm_token: str
    platform: str  # 'ios' or 'android'


class NotificationPreferencesRequest(BaseModel):
    new_videos: Optional[bool] = None
    video_updates: Optional[bool] = None
    announcements: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    new_videos: bool
    video_updates: bool
    announcements: bool


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool
    created_at: datetime


class SendNotificationRequest(BaseModel):
    title: str
    body: str
    video_id: Optional[int] = None
    type: str = "announcement"  # 'new_video', 'video_update', 'announcement', 'system'


# --- Endpoints ---

@router.post("/register-device", status_code=status.HTTP_201_CREATED)
async def register_device(
    request: DeviceRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a device for push notifications"""
    # Check if token already exists
    result = await db.execute(
        select(DeviceRegistration).where(DeviceRegistration.fcm_token == request.fcm_token)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing registration
        existing.user_id = current_user.id
        existing.platform = request.platform
        existing.is_active = True
        await db.commit()
        return {"message": "Device registration updated"}
    
    # Create new registration
    device = DeviceRegistration(
        user_id=current_user.id,
        fcm_token=request.fcm_token,
        platform=request.platform,
        is_active=True
    )
    db.add(device)
    await db.commit()
    
    return {"message": "Device registered successfully"}


@router.delete("/unregister-device")
async def unregister_device(
    fcm_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unregister a device from push notifications"""
    await db.execute(
        delete(DeviceRegistration).where(
            and_(
                DeviceRegistration.fcm_token == fcm_token,
                DeviceRegistration.user_id == current_user.id
            )
        )
    )
    await db.commit()
    
    return {"message": "Device unregistered"}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's notification preferences"""
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        # Return defaults
        return NotificationPreferencesResponse(
            new_videos=True,
            video_updates=True,
            announcements=True
        )
    
    return NotificationPreferencesResponse(
        new_videos=prefs.new_videos,
        video_updates=prefs.video_updates,
        announcements=prefs.announcements
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    request: NotificationPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's notification preferences"""
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
    
    if request.new_videos is not None:
        prefs.new_videos = request.new_videos
    if request.video_updates is not None:
        prefs.video_updates = request.video_updates
    if request.announcements is not None:
        prefs.announcements = request.announcements
    
    await db.commit()
    await db.refresh(prefs)
    
    return NotificationPreferencesResponse(
        new_videos=prefs.new_videos,
        video_updates=prefs.video_updates,
        announcements=prefs.announcements
    )


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's notifications"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [
        NotificationResponse(
            id=n.id,
            type=n.type.value,
            title=n.title,
            body=n.body,
            data=json.loads(n.data) if n.data else None,
            is_read=n.is_read,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    await db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    notifications = result.scalars().all()
    
    for n in notifications:
        n.is_read = True
    
    await db.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    notifications = result.scalars().all()
    
    return {"unread_count": len(notifications)}


# --- Internal notification sending function ---

async def send_notification_to_user(
    db: AsyncSession,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    body: str,
    data: dict = None
):
    """Send a notification to a specific user"""
    # Save to database for in-app display
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        data=json.dumps(data) if data else None
    )
    db.add(notification)
    await db.flush()
    
    # Get user's device registrations
    result = await db.execute(
        select(DeviceRegistration).where(
            and_(
                DeviceRegistration.user_id == user_id,
                DeviceRegistration.is_active == True
            )
        )
    )
    devices = result.scalars().all()
    
    # Send push notification to all devices
    for device in devices:
        await _send_fcm_notification(device.fcm_token, title, body, data)
    
    return notification


async def notify_new_video(db: AsyncSession, video: Video):
    """Send notification to all students about a new video"""
    # Get all student device registrations
    from ..models import UserRole
    
    # Get students who have new_videos enabled (or no preference record = enabled by default)
    result = await db.execute(
        select(DeviceRegistration, NotificationPreference)
        .outerjoin(NotificationPreference, DeviceRegistration.user_id == NotificationPreference.user_id)
        .join(User, DeviceRegistration.user_id == User.id)
        .where(
            and_(
                User.role == UserRole.STUDENT,
                DeviceRegistration.is_active == True
            )
        )
    )
    rows = result.all()
    
    title = "New Training Video!"
    body = f"'{video.title}' is now available"
    data = {"video_id": str(video.id), "type": "new_video"}
    
    # Get unique user IDs for in-app notifications
    user_ids_notified = set()
    
    for device, prefs in rows:
        # Check preferences (if no prefs record, default is enabled)
        if prefs is None or prefs.new_videos:
            await _send_fcm_notification(device.fcm_token, title, body, data)
            user_ids_notified.add(device.user_id)
    
    # Create in-app notifications for each user
    for user_id in user_ids_notified:
        notification = Notification(
            user_id=user_id,
            type=NotificationType.NEW_VIDEO,
            title=title,
            body=body,
            data=json.dumps(data)
        )
        db.add(notification)
    
    await db.commit()
    
    return len(user_ids_notified)


async def _send_fcm_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """Send FCM push notification using Firebase HTTP v1 API"""
    # For simplicity, we'll use the legacy HTTP API which doesn't require OAuth
    # In production, you should use the v1 API with proper service account auth
    
    fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
    if not fcm_server_key:
        return False
    
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Authorization": f"key={fcm_server_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": fcm_token,
        "notification": {
            "title": title,
            "body": body,
            "sound": "default"
        },
        "data": data or {}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code == 200
    except Exception as e:
        print(f"FCM notification error: {e}")
        return False
