from fastapi import APIRouter, Depends, HTTPException, Query
import asyncpg
from typing import Optional

from core.security import get_current_user_with_db
from core.db import get_async_db
from users.schemas import (
    UserReadingProfile, UserProfileUpdate, 
    FinishBookRequest, UserBookResponse, UserActivityResponse
)
from users.service import UserService

router = APIRouter()


async def get_user_service(
    db: asyncpg.Connection = Depends(get_async_db),
) -> UserService:
    return UserService(db)


@router.get("/me")
async def get_me(
    current_user=Depends(get_current_user_with_db),
    service: UserService = Depends(get_user_service),
):
    """Get current user details including bio and location"""
    # ✅ FIXED: Removed int() conversion
    user = await service.get_user_by_id(current_user["id"])
    return user


@router.get("/profile", response_model=UserReadingProfile)
async def get_profile(
    current_user=Depends(get_current_user_with_db),
    service: UserService = Depends(get_user_service),
):
    """Return the user's reading profile"""
    # ✅ FIXED: Removed int() conversion
    profile = await service.get_user_profile(current_user["id"])
    
    if not profile:
        return UserReadingProfile()
    
    # Safely handle categories_read which can be a JSON string, a list, or None
    categories = profile.get("categories_read")
    categories_value = []
    
    if categories:
        if isinstance(categories, str):
            try:
                import json
                parsed = json.loads(categories)
                if isinstance(parsed, list):
                    categories_value = [str(c) for c in parsed]
                else:
                    categories_value = [str(parsed)]
            except:
                categories_value = [categories]
        elif isinstance(categories, list):
            categories_value = [str(c) for c in categories]
        else:
            categories_value = [str(categories)]
    
    return UserReadingProfile(
        total_books_read=profile.get("total_books_read", 0),
        total_pages_read=profile.get("total_pages_read", 0),
        current_streak=profile.get("current_streak", 0),
        longest_streak=profile.get("longest_streak", 0),
        last_read_date=profile.get("last_read_date"),
        yearly_goal=profile.get("yearly_goal", 0),
        monthly_goal=profile.get("monthly_goal", 0),
        yearly_progress=profile.get("yearly_progress", 0),
        monthly_progress=profile.get("monthly_progress", 0),
        categories_read=categories_value,
    )


@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user=Depends(get_current_user_with_db),
    service: UserService = Depends(get_user_service),
):
    """Update user's reading profile"""
    # ✅ FIXED: Removed int() conversion
    user_id = current_user["id"]
    
    # Update user info
    await service.update_user_info(
        user_id=user_id,
        full_name=profile_data.full_name,
        bio=profile_data.bio,
        location=profile_data.location
    )
    
    # Update reading profile
    await service.update_reading_profile(
        user_id=user_id,
        yearly_goal=profile_data.yearly_goal,
        monthly_goal=profile_data.monthly_goal,
        categories_read=profile_data.categories_read
    )
    
    # Fetch and return updated profile
    profile = await service.get_user_profile(user_id)
    
    # Safely handle categories_read which can be a JSON string, a list, or None
    categories = profile.get("categories_read")
    categories_value = []
    
    if categories:
        if isinstance(categories, str):
            try:
                import json
                parsed = json.loads(categories)
                if isinstance(parsed, list):
                    categories_value = [str(c) for c in parsed]
                else:
                    categories_value = [str(parsed)]
            except:
                categories_value = [categories]
        elif isinstance(categories, list):
            categories_value = [str(c) for c in categories]
        else:
            categories_value = [str(categories)]
    
    return UserReadingProfile(
        total_books_read=profile.get("total_books_read", 0),
        total_pages_read=profile.get("total_pages_read", 0),
        current_streak=profile.get("current_streak", 0),
        longest_streak=profile.get("longest_streak", 0),
        last_read_date=profile.get("last_read_date"),
        yearly_goal=profile.get("yearly_goal", 0),
        monthly_goal=profile.get("monthly_goal", 0),
        yearly_progress=profile.get("yearly_progress", 0),
        monthly_progress=profile.get("monthly_progress", 0),
        categories_read=categories_value,
    )


@router.get("/books", response_model=list[UserBookResponse])
async def get_user_books(
    list_type: Optional[str] = Query(None, description="Filter by list type: finished, reading, wishlist"),
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user_with_db),
    service: UserService = Depends(get_user_service),
):
    """Get user's books with optional filtering by list_type"""
    # ✅ FIXED: Removed int() conversion
    books = await service.get_user_books(
        user_id=current_user["id"],
        list_type=list_type,
        limit=limit
    )
    return books


@router.get("/activity", response_model=list[UserActivityResponse])
async def get_user_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user_with_db),
    service: UserService = Depends(get_user_service),
):
    """Get user's recent activity"""
    # ✅ FIXED: Removed int() conversion
    activities = await service.get_user_activity(
        user_id=current_user["id"],
        limit=limit
    )
    return activities


@router.post("/books/finish")
async def finish_book(
    request: FinishBookRequest,
    current_user=Depends(get_current_user_with_db),
    service: UserService = Depends(get_user_service),
):
    """Mark a book as finished and update reading progress"""
    # ✅ FIXED: Removed int() conversion
    user_id = current_user["id"]
    
    try:
        result = await service.mark_book_as_finished(user_id, request.book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error finishing book: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark book as finished")
