from typing import List, Dict
from llm.gemini_client import ask_gemini

def clean_llm_output(text: str) -> str:
    """Clean and truncate LLM output to remove unnecessary content"""
    # Remove common prefixes
    prefixes_to_remove = [
        "LIBRARIAN ANSWER:",
        "Assistant:",
        "AI:",
        "Answer:",
        "Here's your answer:",
        "Sure, here's",
        "Certainly,",
        "Of course,",
    ]
    
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Remove markdown formatting
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove markdown headers
        if line.startswith('#') or line.startswith('---'):
            continue
        # Remove excessive bullet points
        if line.strip().startswith('*') or line.strip().startswith('-'):
            line = line.strip()[1:].strip()
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Truncate if too long (max 300 characters for answers)
    if len(text) > 300:
        text = text[:300] + "..."
    
    return text.strip()

def truncate_book_details(book: Dict) -> str:
    """Extract and truncate book details for context"""
    title = book.get('title', 'Unknown Title')
    author = book.get('author', 'Unknown Author')
    genres = book.get('genres', '')
    
    # Prioritize summary, then description, limit to 150 chars
    summary = book.get('summary') or book.get('description') or ''
    if len(summary) > 150:
        summary = summary[:150] + "..."
    
    return f"{title} by {author} | Genre: {genres} | {summary}"

def librarian_answer(user_question: str, books: List[Dict]) -> Dict:
    """
    Generate concise answers from books with citations
    
    Returns:
    {
        "answer": str (concise, max 300 chars),
        "citations": { "[1]": book_id, ... }
    }
    """
    
    if not books:
        return {
            "answer": "I don't have enough information to answer that question.",
            "citations": {}
        }
    
    # Build minimal context
    context_lines = []
    citation_map = {}
    
    for i, book in enumerate(books, 1):
        # Use truncated book details
        book_context = truncate_book_details(book)
        context_lines.append(f"[{i}] {book_context}")
        citation_map[f"[{i}]"] = book["book_id"]
    
    context = "\n".join(context_lines)
    
    # Determine question type for tailored response length
    question_lower = user_question.lower()
    
    # Very short answer for certain question types
    if any(word in question_lower for word in ['summary', 'summarize', 'about']):
        response_type = "Give a VERY brief summary in 1-2 sentences."
        max_length = 100
    elif any(word in question_lower for word in ['author', 'who wrote']):
        response_type = "Briefly name the author and one key fact."
        max_length = 80
    elif any(word in question_lower for word in ['genre', 'category', 'type']):
        response_type = "State the genre(s) concisely."
        max_length = 50
    elif any(word in question_lower for word in ['worth', 'good', 'recommend']):
        response_type = "Give a brief recommendation in 1 sentence."
        max_length = 100
    elif any(word in question_lower for word in ['similar', 'like', 'recommendations']):
        response_type = "Name 1-2 similar books or authors briefly."
        max_length = 120
    else:
        response_type = "Answer concisely in 1-2 sentences."
        max_length = 150
    
    # Single book vs multiple books prompt
    if len(books) == 1:
        prompt = f"""You are a helpful librarian. Answer the user's question about this book in 1-2 sentences only.
Keep it extremely concise. No greetings, no markdown, no explanations.

BOOK: {context}

USER: {user_question}
{response_type}

Your brief answer:"""
    else:
        prompt = f"""You are a helpful librarian. Answer using these books. Be extremely concise - 1-2 sentences max.

BOOKS:
{context}

USER: {user_question}
{response_type}

Your brief answer:"""

    raw_answer = ask_gemini(prompt).strip()
    
    # Clean and truncate
    cleaned_answer = clean_llm_output(raw_answer)
    
    # Enforce maximum length
    if len(cleaned_answer) > max_length:
        cleaned_answer = cleaned_answer[:max_length] + "..."
    
    print(f"📚 Librarian answer generated ({len(cleaned_answer)} chars)")
    
    # Find which citations were actually used
    used_citations = {}
    for ref, book_id in citation_map.items():
        if ref in cleaned_answer:
            used_citations[ref] = book_id
    
    return {
        "answer": cleaned_answer,
        "citations": used_citations
    }