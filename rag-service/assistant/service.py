from typing import List, Dict, Optional
import asyncpg
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from retrieval.retriever import search_books
from retrieval.neon_fetch import fetch_books_by_ids
from assistant.librarian import librarian_answer


def normalize_books(books: List[Dict]) -> List[Dict]:
    """Clean and standardize book data for the assistant context."""
    return [
        {
            "book_id": b.get("book_id"),
            "title": b.get("title"),
            "author": b.get("author"),
            "genres": b.get("genres"),
            "image_url": b.get("image_url"),
            "summary": b.get("summary") or b.get("description"),
        }
        for b in books
    ]


# Natural greetings and casual response patterns
GREETING_PATTERNS = [
    "hi", "hello", "hey", "hii", "heyy", "hi there", "hello there",
    "good morning", "good afternoon", "good evening",
    "how are you", "how r u", "how you doing",
    "who are you", "what can you do", "what do you do",
    "thanks", "thank you", "thx", "ty",
    "great", "good", "awesome", "nice", "cool", "wonderful",
    "welcome", "well done", "good job",
    "bye", "goodbye", "see you", "take care"
]


def get_similarity_score(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts using TF-IDF."""
    try:
        vectorizer = TfidfVectorizer().fit([text1, text2])
        vectors = vectorizer.transform([text1, text2])
        return cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    except:
        return 0.0


def get_predefined_answer(question: str, books: List[Dict] = None) -> Optional[str]:
    """
    Smart predefined responses with fuzzy matching using cosine similarity.
    Bypasses the LLM for common interactions to increase responsiveness.
    """
    q = question.lower().strip()
    clean_q = re.sub(r'[^\w\s]', '', q)

    if not clean_q:
        return None

    # 1. Greeting & Casual Talk Detection (Fuzzy Matching)
    best_match = None
    max_sim = 0
    
    for pattern in GREETING_PATTERNS:
        sim = get_similarity_score(clean_q, pattern)
        if sim > max_sim:
            max_sim = sim
            best_match = pattern

    if max_sim > 0.75:
        if "how are you" in best_match:
            return "I'm doing great, thank you! Always happy to talk about books. How about you?"
        elif any(x in best_match for x in ["who are you", "what can you do", "what do you do"]):
            return "I'm your friendly AI Librarian! I can help you understand books, suggest similar reads, discuss themes, and answer almost anything about literature."
        elif any(x in best_match for x in ["thanks", "thank you", "thx", "ty"]):
            return "You're very welcome! Glad I could help. 😊"
        elif any(x in best_match for x in ["great", "good", "awesome", "nice", "cool", "wonderful"]):
            return "Thank you! I'm happy you're enjoying the experience. What else would you like to know?"
        elif any(x in best_match for x in ["bye", "goodbye", "see you", "take care"]):
            return "Goodbye! It was lovely chatting with you. Come back anytime you want book recommendations! 📖"
        else:
            return "Hello! I'm your AI Librarian. Ask me anything about books — summaries, themes, similar reads, or even mood-based suggestions!"

    # 2. Context-aware simple answers (for single book context)
    if books and len(books) == 1:
        book = books[0]
        title = book.get("title", "this book")
        author = book.get("author", "the author")
        
        book_queries = {
            "author": f"The author of \"{title}\" is {author}.",
            "who wrote": f"\"{title}\" was written by {author}.",
            "who is the author": f"The author is {author}.",
            "title": f"The title is \"{title}\".",
            "what is the title": f"This book is called \"{title}\".",
            "genre": f"\"{title}\" is in the {book.get('genres', 'various')} genre.",
        }
        
        for key, response in book_queries.items():
            if key in clean_q:
                return response

    return None


async def log_chat_history(
    user_id: int, 
    db: asyncpg.Connection, 
    question: str, 
    answer: str, 
    context_books: List[Dict]
):
    """Save conversation to database for analytics and user history."""
    if not user_id or not db:
        return
        
    try:
        cited_ids = [b.get("book_id") for b in context_books if b.get("book_id")]
        await db.execute("""
            INSERT INTO assistant_chats (user_id, question, answer, context_book_ids, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, user_id, question, answer, cited_ids)
        print(f"✅ Chat logged for user {user_id}")
    except Exception as e:
        print(f"⚠️ Failed to log chat: {e}")


async def assistant_service(
    question: str, 
    top_k: int = 5, 
    book_ids: Optional[List[str]] = None,
    user_id: Optional[int] = None,
    db: Optional[asyncpg.Connection] = None
) -> Dict:
    """
    Main AI Librarian service pipeline.
    Combines fuzzy-matched quick replies with deep LLM book analysis.
    """

    print(f"💬 User query: \"{question}\"")

    # 1. Check for quick predefined responses (Greetings/Casual)
    predefined = get_predefined_answer(question)
    if predefined:
        print("✨ Responded with predefined message")
        if user_id and db:
            await log_chat_history(user_id, db, question, predefined, [])
        return {
            "answer": predefined,
            "books": [],
            "citations": {}
        }

    # 2. Fetch relevant book context
    books = []
    if book_ids:
        # Specific context (e.g., from Book Detail page)
        print(f"📖 Loading specific book(s): {book_ids}")
        books = await fetch_books_by_ids(book_ids)
    else:
        # General search context
        print(f"🔍 Searching books for: \"{question}\"")
        results = search_books(question, top_k=top_k)
        if not results:
            answer = "I couldn't find any matching books. Could you tell me more about what you're looking for?"
            if user_id and db:
                await log_chat_history(user_id, db, question, answer, [])
            return {"answer": answer, "books": [], "citations": {}}

        search_ids = [r["book_id"] for r in results]
        books = await fetch_books_by_ids(search_ids)

    if not books:
        answer = "I'm sorry, I found some potential matches but couldn't retrieve their details right now."
        if user_id and db:
            await log_chat_history(user_id, db, question, answer, [])
        return {"answer": answer, "books": [], "citations": {}}

    books = normalize_books(books)
    print(f"📚 {len(books)} book(s) retrieved as context")

    # 3. Check for context-aware quick replies (e.g., "who is the author")
    predefined = get_predefined_answer(question, books)
    if predefined:
        print("✨ Used context-aware quick reply")
        if user_id and db:
            await log_chat_history(user_id, db, question, predefined, books)
        return {"answer": predefined, "books": [], "citations": {}}

    # 4. Generate thoughtful AI response using the Librarian model
    try:
        print("🧠 Generating AI response...")
        llm_result = librarian_answer(question, books)
        answer = llm_result.get("answer", "I'd love to help, but I'm having trouble forming a response right now.")
        citations = llm_result.get("citations", {})
    except Exception as e:
        print(f"❌ AI Librarian error: {e}")
        answer = "I found some great books, but I'm having trouble putting my thoughts together. Mind trying again?"
        citations = {}

    # 5. Log final conversation
    if user_id and db:
        await log_chat_history(user_id, db, question, answer, books)

    # 6. Format minimal book data for frontend
    minimal_books = [
        {
            "book_id": b["book_id"],
            "title": b["title"],
            "author": b["author"],
            "genres": b["genres"],
            "image_url": b["image_url"],
        }
        for b in books
    ]

    return {
        "answer": answer,
        "books": minimal_books,
        "citations": citations
    }
