from typing import List, Dict
from llm.gemini_client import ask_gemini
from utils.keyword_extractor import build_mini_context

def build_books_context(books: List[Dict]) -> tuple[str, Dict]:
    """
    Returns:
    - context string with numbered books
    - citation map { "[1]": book_id, ... }
    """
    context_lines = []
    citation_map = {}
    
    for i, b in enumerate(books, 1):
        # Build minimal context using keywords only
        mini_context = build_mini_context(b, num_keywords=5)
        context_lines.append(f"[{i}] {mini_context}")
        citation_map[f"[{i}]"] = b["book_id"]
        
        # Debug - see what's being sent
        print(f"Book {i} context: {mini_context}")
    
    return "\n".join(context_lines), citation_map

def librarian_answer(user_question: str, books: List[Dict]) -> Dict:
    """
    Returns:
    {
        "answer": str,
        "citations": { "[1]": book_id, ... }
    }
    """
    
    if not books:
        return {
            "answer": "I don't have enough information from the available books to answer this question.",
            "citations": {}
        }
    
    # Build context with citations
    context, citation_map = build_books_context(books)
    
    prompt = f"""You are a knowledgeable librarian recommending books to a reader who asked: "{user_question}"

Based on these books, write a friendly, varied recommendation (2-3 sentences):

BOOKS:
{context}

Write like a human librarian would speak:
- DO NOT repeat the same phrase for each book
- Mention 2-3 books with different describing words
- Explain what makes each book special or unique
- Add citations like [1] after book titles
- No bullet points, no markdown

Example of good response:
"If you're looking for epic fantasy with magic, David Eddings's Castle of Wizardry [1] delivers classic quest fantasy with memorable characters. For something darker, Andrzej Sapkowski's Baptism of Fire [5] offers gritty Witcher adventures. V.E. Schwab's A Darker Shade of Magic [6] takes a unique twist with parallel universes and forbidden magic."

Your recommendation:"""

    answer = ask_gemini(prompt).strip()
    print(f"Answer given by gemini : {answer}")
    
    # Hard hallucination check
    if "enough information" in answer.lower():
        return {
            "answer": "I don't have enough information from the available books to answer this question.",
            "citations": {}
        }
    
    # Validate citations
    used_citations = {
        c: citation_map[c]
        for c in citation_map
        if c in answer
    }
    
    return {
        "answer": answer,
        "citations": used_citations
    }