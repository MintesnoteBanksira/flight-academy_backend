"""
Category API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..core.database import get_db
from ..models.user import User
from ..models.video import Category
from ..schemas.video import CategoryResponse, CategoryCreate
from .deps import get_current_instructor

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all categories"""
    result = await db.execute(select(Category).order_by(Category.order, Category.name))
    categories = result.scalars().all()
    
    return [
        CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            icon=cat.icon,
            color=cat.color,
            order=cat.order,
        )
        for cat in categories
    ]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Get category by ID"""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        icon=category.icon,
        color=category.color,
        order=category.order,
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category (instructor only)"""
    # Check if category name already exists
    result = await db.execute(select(Category).where(Category.name == category_data.name))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )
    
    # Get max order
    result = await db.execute(select(Category))
    all_categories = result.scalars().all()
    max_order = max((c.order for c in all_categories), default=0)
    
    new_category = Category(
        name=category_data.name,
        description=category_data.description,
        icon=category_data.icon,
        color=category_data.color,
        order=max_order + 1,
    )
    
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    
    return CategoryResponse(
        id=new_category.id,
        name=new_category.name,
        description=new_category.description,
        icon=new_category.icon,
        color=new_category.color,
        order=new_category.order,
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_instructor),
    db: AsyncSession = Depends(get_db)
):
    """Delete a category (instructor only)"""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    await db.delete(category)
    await db.commit()
