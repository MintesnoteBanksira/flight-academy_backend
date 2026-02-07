"""
User Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


# Base schema with common fields
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.STUDENT
    rank: Optional[str] = None
    airline: Optional[str] = None


# Schema for creating a user (signup)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


# Schema for updating user profile
class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    rank: Optional[str] = None
    airline: Optional[str] = None
    license_number: Optional[str] = None


# Schema for user response (public data)
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    full_name: str
    initials: str

    class Config:
        from_attributes = True


# Schema for user profile (self view with more details)
class UserProfile(UserResponse):
    last_login: Optional[datetime] = None
    license_number: Optional[str] = None

    class Config:
        from_attributes = True


# Schema for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Schema for token response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Schema for password change
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
