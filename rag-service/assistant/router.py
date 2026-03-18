from fastapi import APIRouter, HTTPException, Depends, Request
from assistant.schemas import AssistantRequest, AssistantResponse
from assistant.service import assistant_service
from core.security import verify_premium_subscription, get_current_user_with_db
from core.db import get_async_db
import asyncpg

router = APIRouter()

@router.post("/ask/premium", response_model=AssistantResponse)
async def ask_premium(
    payload: AssistantRequest,
    subscription=Depends(verify_premium_subscription),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Premium AI assistant that can use more context or advanced models.
    """
    try:
        # Get user from subscription object (it has user info)
        user_id = subscription.get("user_id")
        
        # For premium, we might use a different model or more context (top_k)
        result = await assistant_service(
            question=payload.question,
            top_k=max(payload.top_k, 10), # Always use more context for premium
            book_ids=payload.book_ids,
            user_id=user_id,
            db=db
        )

        return AssistantResponse(
            question=payload.question,
            answer=f"✨ [PREMIUM ANSWER] {result['answer']}",
            books=result["books"]
        )

    except Exception as e:
        print("❌ Premium assistant error:", e)
        raise HTTPException(
            status_code=500,
            detail="Premium assistant failed"
        )

@router.post("/ask", response_model=AssistantResponse)
async def ask(
    payload: AssistantRequest,
    request: Request,
    db: asyncpg.Connection = Depends(get_async_db)
):
    try:
        # Try to get user if authenticated (optional for basic ask)
        user_id = None
        try:
            user = await get_current_user_with_db(request, db=db)
            user_id = user.get("id")
        except:
            pass

        result = await assistant_service(
            question=payload.question,
            top_k=payload.top_k,
            book_ids=payload.book_ids,
            user_id=user_id,
            db=db
        )

        return AssistantResponse(
            question=payload.question,
            answer=result["answer"],
            books=result["books"]
        )

    except Exception as e:
        print("❌ Assistant error:", e)
        raise HTTPException(
            status_code=500,
            detail="Assistant failed"
        )