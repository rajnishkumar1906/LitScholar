from fastapi import APIRouter, HTTPException
from assistant.schemas import AssistantRequest, AssistantResponse
from retrieval.retriever import search_books
from retrieval.supabase_fetch import fetch_books_by_ids
from assistant.librarian import librarian_answer

router = APIRouter()

@router.post("/ask", response_model=AssistantResponse)
def ask(payload: AssistantRequest):
    try:
        print(f"[/ask] Received question: '{payload.question}' | top_k={payload.top_k}")

        if payload.book_ids:
            books = fetch_books_by_ids(payload.book_ids)
            print(f"[/ask] Using provided book_ids: {payload.book_ids}")
        else:
            results = search_books(payload.question, top_k=payload.top_k)
            print(f"[/ask] Retrieval returned {len(results)} candidates")

            if not results:
                print("[/ask] No relevant books found → returning fallback")
                return AssistantResponse(
                    question=payload.question,
                    answer="I don’t have enough information from the available books to answer this question.",
                    citations={},
                    sources=[]
                )

            book_ids = [r["book_id"] for r in results]
            books = fetch_books_by_ids(book_ids)
            print(f"[/ask] Fetched full book data for {len(books)} books")

        if not books:
            print("[/ask] No books after fetch → returning fallback")
            return AssistantResponse(
                question=payload.question,
                answer="I don't have enough information from the available books to answer this question.",
                citations={},
                sources=[]
            )

        # Print the actual books that would go to the LLM
        print("\n[DEBUG] Top matching books that would be sent to LLM:")
        print("Rank | Book ID     | Title (if available) | Score")
        for idx, book in enumerate(books, 1):
            title = book.get('title', 'Unknown title')
            score = next((r['score'] for r in results if r['book_id'] == book['book_id']), 'N/A')
            print(f"{idx:4} | {book['book_id']} | {title[:60]:60} | {score}")

        # Call LLM with the new format that returns citations
        llm_result = librarian_answer(payload.question, books)

        # Temporary response so you see the books
        return AssistantResponse(
            question=payload.question,
            answer=llm_result["answer"],
            citations=llm_result["citations"],
            sources=books   # ← this will go to frontend
        )

    except Exception as e:
        print(f"[ERROR in /ask] {str(e)}")
        raise