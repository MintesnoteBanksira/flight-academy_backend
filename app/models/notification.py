"""
Notification models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..core.database import Base


class NotificationType(str, enum.Enum):
    NEW_VIDEO = "new_video"
    VIDEO_UPDATE = "video_update"
    SYSTEM = "system"
    ANNOUNCEMENT = "announcement"


class DeviceRegistration(Base):
    """Stores FCM tokens for push notifications"""
    __tablename__ = "device_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fcm_token = Column(String(500), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # 'ios' or 'android'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="devices")


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    new_videos = Column(Boolean, default=True)
    video_updates = Column(Boolean, default=True)
    announcements = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User", backref="notification_preferences")


class Notification(Base):
    """Stores notifications for in-app display"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(Text, nullable=True)  # JSON string with additional data (e.g., video_id)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", backref="notifications")
