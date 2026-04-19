from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from assistant.schemas import AssistantRequest, AssistantResponse
from assistant.service import assistant_service
from core.security import get_current_user_with_db, security
from core.db import get_async_db
import asyncpg

router = APIRouter()

@router.post("/ask", response_model=AssistantResponse)
async def ask(
    payload: AssistantRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_async_db)
):
    try:
        # Try to get user if authenticated (optional for basic ask)
        user_id = None
        try:
            user = await get_current_user_with_db(request, credentials, db=db)
            user_id = user.get("id")
            print(f"[DEBUG] Assistant request from user: {user_id}")
        except Exception as auth_err:
            print(f"[DEBUG] Assistant auth skipped: {auth_err}")
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
            books=result["books"],
            citations=result.get("citations")
        )

    except Exception as e:
        print("❌ Assistant error:", e)
        raise HTTPException(
            status_code=500,
            detail="Assistant failed"
        )