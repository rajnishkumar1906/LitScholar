// src/services/books.js - Books service
import { ragApi, handleResponse } from './api';

// Helper to format book data consistently
const formatBook = (book) => {
  const genres = book.genres || book.book_details || "";
  let category = "General";

  if (genres) {
    if (typeof genres === 'string') {
      const cleaned = genres.replace(/[\[\]']/g, '').split(',')[0].trim();
      if (cleaned) category = cleaned;
    } else if (Array.isArray(genres) && genres.length > 0) {
      category = genres[0];
    }
  }

  return {
    ...book,
    id: book.book_id || book.id,
    title: book.title || book.book_title,
    image_url: book.image_url || book.cover_image_url,
    category,
    rating: book.rating || 4.5
  };
};

export const booksService = {
  // Search books with AI assistant
  async searchBooks(query, topK = 10, isPremium = false) {
    const endpoint = isPremium ? "/assistant/ask/premium" : "/assistant/ask";
    
    const result = await handleResponse(
      ragApi.post(endpoint, {
        question: query,
        top_k: topK,
      })
    );
    
    if (result.success) {
      const { books = [], answer = "" } = result.data;
      return {
        success: true,
        books: books.map(formatBook),
        answer
      };
    }
    
    return result;
  },

  // Get book by ID
  async getBookById(bookId) {
    const result = await handleResponse(
      ragApi.get(`/books/${bookId}`)
    );
    
    if (result.success) {
      return {
        success: true,
        book: formatBook(result.data)
      };
    }
    
    return result;
  },

  // Get book summary
  async getBookSummary(bookId) {
    const result = await handleResponse(
      ragApi.get(`/books/${bookId}/summary`)
    );
    
    if (result.success) {
      return {
        success: true,
        summary: result.data.summary
      };
    }
    
    return result;
  },

  // List books with pagination
  async listBooks(page = 1, limit = 20) {
    const result = await handleResponse(
      ragApi.get('/books/', {
        params: { page, limit }
      })
    );
    
    if (result.success) {
      return {
        success: true,
        books: (result.data.books || []).map(formatBook),
        total: result.data.total || 0,
        page: result.data.page || page,
        hasMore: result.data.hasMore || false
      };
    }
    
    return result;
  },

  // Get books by genre
  async getBooksByGenre(genre, page = 1, limit = 20) {
    const result = await handleResponse(
      ragApi.get(`/books/by-genre/${encodeURIComponent(genre)}`, {
        params: { page, limit }
      })
    );
    
    if (result.success) {
      return {
        success: true,
        books: (result.data.books || []).map(formatBook),
        total: result.data.total || 0,
        genre
      };
    }
    
    return result;
  },

  // Ask follow-up question
  async askFollowUp(question, books = []) {
    const bookIds = books.map(b => b.id || b.book_id).filter(Boolean);
    const payload = { question };
    if (bookIds.length) payload.book_ids = bookIds;

    const result = await handleResponse(
      ragApi.post('/assistant/ask', payload)
    );
    
    return result;
  },

  // Get recommendations
  async getRecommendations(type = 'for-you', limit = 8, page = 1) {
    let endpoint = '/books/recommended/';
    
    switch(type) {
      case 'for-you':
        endpoint += 'for-you';
        break;
      case 'popular':
        endpoint += 'popular';
        break;
      case 'similar':
        endpoint += 'similar';
        break;
      case 'genre':
        endpoint += 'by-genre';
        break;
      default:
        endpoint += 'for-you';
    }
    
    const result = await handleResponse(
      ragApi.get(endpoint, {
        params: { limit, page }
      })
    );
    
    if (result.success) {
      const books = (result.data.books || []).map(formatBook);
      return {
        success: true,
        books,
        hasMore: result.data.hasMore || false,
        page: result.data.page || page
      };
    }
    
    return result;
  },

  // Track book view
  async trackBook(bookId) {
    return handleResponse(
      ragApi.post(`/books/track/${bookId}`)
    );
  },

  // Add book to user list
  async addUserBook(bookId, listType, rating = null, notes = null) {
    return handleResponse(
      ragApi.post('/books/user/books', {
        book_id: bookId,
        list_type: listType,
        rating,
        notes
      })
    );
  },

  // Mark book as finished
  async finishBook(bookId) {
    return handleResponse(
      ragApi.post('/books/finish', { book_id: bookId })
    );
  }
};