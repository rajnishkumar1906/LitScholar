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
    
    # Use more context if we only have 1 or 2 books (likely a direct follow-up)
    max_detail_length = 1500 if len(books) <= 2 else 500

    for i, b in enumerate(books, 1):
        summary_text = b.get('summary') or b.get('description') or ''
        # Limit summary/description length for context window efficiency
        if len(summary_text) > max_detail_length:
            summary_text = summary_text[:max_detail_length] + "..."
        
        context_lines.append(f"[{i}] {b['title']} | {b['author']} | Genres: {b.get('genres', '')} | Details: {summary_text}")
        citation_map[f"[{i}]"] = b["book_id"]
    
    context = "\n".join(context_lines)
    
    # Check if this is a follow-up for a specific book
    is_single_book = len(books) == 1
    
    if is_single_book:
        prompt = f"""You are the LitScholar AI Librarian. You are helping a user with a specific book.
Answer the user's question about the book provided below. 
If the answer isn't in the text, use your internal knowledge about this book and author, but prioritize the provided details.
Be conversational, helpful, and insightful.

BOOK CONTEXT:
{context}

USER QUESTION: {user_question}
LIBRARIAN ANSWER:"""
    else:
        prompt = f"""You are the LitScholar AI Librarian. Answer the user's question using the books provided below as your primary source. 
Cite each claim using [1], [2], etc. based on the book index.
If you cannot answer from these books, you can use your general knowledge to provide a helpful response, but clearly state if you are going beyond the provided context.

BOOKS:
{context}

USER QUESTION: {user_question}
LIBRARIAN ANSWER:"""

    raw_answer = ask_gemini(prompt).strip()
    
    # 👇 CLEANING - right after getting response
    cleaned_answer = clean_llm_output(raw_answer)
    print(f"Librarian answer generated for: {user_question}")
    
    # Validate citations
    used_citations = {
        c: citation_map[c]
        for c in citation_map
        if c in cleaned_answer
    }
    
    return {
        "answer": cleaned_answer,
        "citations": used_citations
    }