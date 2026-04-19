"""
retrieval module - FAISS-based book retrieval
"""

from retrieval.retriever import search_books, get_collection_stats
from retrieval.faiss_client import get_faiss_collection, load_faiss_index

__all__ = [
    'search_books',
    'get_collection_stats',
    'get_faiss_collection',
    'load_faiss_index'
]