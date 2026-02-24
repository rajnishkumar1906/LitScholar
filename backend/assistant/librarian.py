from typing import List, Dict
from llm.gemini_client import ask_gemini
import re  # Add this import

def clean_llm_output(text):
    """
    Remove unwanted characters from LLM response
    """
    # Remove markdown symbols
    text = re.sub(r'[*_#`]', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\']', '', text)
    
    # Fix common issues
    text = text.replace(' .', '.').replace(' ,', ',')
    
    return text.strip()

def build_books_context(books: List[Dict]) -> str:
    return "\n".join(
        f"{i}. {b['title']} | {b['author']} | {b.get('genres', '')}"
        for i, b in enumerate(books, 1)
    )

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
    context_lines = []
    citation_map = {}
    
    for i, b in enumerate(books, 1):
        context_lines.append(f"[{i}] {b['title']} | {b['author']} | {b.get('genres', '')}")
        citation_map[f"[{i}]"] = b["book_id"]
    
    context = "\n".join(context_lines)
    
    prompt = f"""Answer using ONLY the books below. Cite each claim with [1],[2], etc. If you cannot answer from these books, say exactly:
"I don't have enough information from the available books to answer this question."

BOOKS:
{context}

Q: {user_question}
A:"""

    raw_answer = ask_gemini(prompt).strip()
    
    # 👇 ADD CLEANING HERE - right after getting response
    cleaned_answer = clean_llm_output(raw_answer)
    print(f"Raw answer: {raw_answer}")
    print(f"Cleaned answer: {cleaned_answer}")
    
    # Hard hallucination check
    if "enough information" in cleaned_answer.lower():
        return {
            "answer": "I don't have enough information from the available books to answer this question.",
            "citations": {}
        }
    
    # Validate citations
    used_citations = {
        c: citation_map[c]
        for c in citation_map
        if c in cleaned_answer
    }
    
    return {
        "answer": cleaned_answer,  # 👈 Return cleaned version
        "citations": used_citations
    }