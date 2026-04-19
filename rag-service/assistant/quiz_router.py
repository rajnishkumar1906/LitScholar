from fastapi import APIRouter, HTTPException, Depends, Request
from llm.gemini_client import ask_gemini
import json
import re
from core.security import get_current_user_with_db

router = APIRouter()

@router.get("/generate/{book_id}")
async def generate_quiz(book_id: str):
    """
    Generate 5 MCQs for a given book using Gemini.
    """
    # Note: In a real scenario, you'd fetch book details from the DB first.
    # For now, we'll ask Gemini to generate questions based on the book_id (assuming it's a known book)
    # or just use the book_id to find context.
    
    # Let's try to get some book context first if possible.
    # Since we don't have the book title here easily without a DB call, 
    # we'll assume the caller might provide it or we'll fetch it.
    
    # Actually, the frontend has the book object, so it can send the title.
    # Let's change this to a POST request to receive book details.
    pass

@router.post("/generate")
async def generate_quiz_post(
    payload: dict,
    request: Request,
    current_user: dict = Depends(get_current_user_with_db)
):
    book_title = payload.get("title")
    book_author = payload.get("author")
    
    if not book_title:
        raise HTTPException(status_code=400, detail="Book title is required")
        
    prompt = f"""
    Generate 5 multiple-choice questions (MCQs) for the book "{book_title}" by {book_author}.
    Each question must have exactly 4 options.
    One of the options MUST be the correct answer.
    Provide the output in a strict JSON format like this:
    {{
        "quiz": [
            {{
                "question": "Question text?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A"
            }},
            ...
        ]
    }}
    The "correct_answer" MUST be a string that exactly matches one of the strings in the "options" array.
    Ensure the questions are challenging but fair.
    Only return the JSON object, no other text.
    """
    
    try:
        response_text = ask_gemini(prompt)
        # Extract JSON if Gemini adds markdown formatting
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            quiz_data = json.loads(json_match.group())
            return quiz_data
        else:
            # Fallback if no JSON found
            raise ValueError("Could not parse JSON from Gemini response")
            
    except Exception as e:
        print(f"❌ Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")
