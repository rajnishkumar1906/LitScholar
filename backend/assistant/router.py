from fastapi import APIRouter, HTTPException

from assistant.schemas import AssistantRequest, AssistantResponse
from assistant.service import assistant_service

router = APIRouter()


@router.post("/ask", response_model=AssistantResponse)
async def ask(payload: AssistantRequest):

    try:
        result = await assistant_service(
            question=payload.question,
            top_k=payload.top_k
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