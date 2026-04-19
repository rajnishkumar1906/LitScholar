// src/services/books.js
import { ragApi, authApi, handleResponse } from './api';
import { allowClientTrack } from '../utils/trackRateLimit';

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
  async searchBooks(query, topK = 10) {
    const endpoint = "/assistant/ask";
    const result = await handleResponse(
      ragApi.post(endpoint, { question: query, top_k: topK })
    );
    if (result.success) {
      const { books = [], answer = "" } = result.data;
      return { success: true, books: books.map(formatBook), answer };
    }
    return result;
  },

  async getBookById(bookId) {
    const result = await handleResponse(ragApi.get(`/books/${bookId}`));
    if (result.success) return { success: true, book: formatBook(result.data) };
    return result;
  },

  async getBookSummary(bookId) {
    const result = await handleResponse(ragApi.get(`/books/${bookId}/summary`));
    if (result.success) return { success: true, summary: result.data.summary };
    return result;
  },

  async listBooks(page = 1, limit = 20) {
    const result = await handleResponse(ragApi.get('/books/', { params: { page, limit } }));
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

  async getBooksByGenre(genre, page = 1, limit = 20) {
    const result = await handleResponse(
      ragApi.get(`/books/by-genre/${encodeURIComponent(genre)}`, { params: { page, limit } })
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

  async askFollowUp(question, books = []) {
    const bookIds = books.map(b => String(b.id || b.book_id)).filter(Boolean);
    const payload = { question };
    if (bookIds.length) payload.book_ids = bookIds;
    const result = await handleResponse(ragApi.post('/assistant/ask', payload));
    if (result.success) {
      return {
        success: true,
        answer: result.data.answer,
        books: (result.data.books || []).map(formatBook),
        citations: result.data.citations || {}
      };
    }
    return result;
  },

  async getRecommendations(type = 'for-you', limit = 8, page = 1) {
    const endpoints = {
      'for-you': '/books/recommended/for-you',
      'popular':  '/books/recommended/popular',
      'similar':  '/books/recommended/similar',
      'genre':    '/books/recommended/by-genre',
    };
    const endpoint = endpoints[type] || '/books/recommended/for-you';
    const result = await handleResponse(ragApi.get(endpoint, { params: { limit, page } }));
    if (result.success) {
      return {
        success: true,
        books: (result.data.books || []).map(formatBook),
        hasMore: result.data.hasMore || false,
        page: result.data.page || page
      };
    }
    return result;
  },

  async trackBook(bookId) {
    if (!allowClientTrack(bookId)) {
      return { success: true, skipped: true };
    }
    try {
      const response = await ragApi.post(`/books/track/${bookId}`);
      return { success: true, data: response.data };
    } catch (error) {
      if (error.status === 429) {
        return { success: true, skipped: true, rateLimited: true };
      }
      return {
        success: false,
        error: error.error || 'An unexpected error occurred',
      };
    }
  },

  async addUserBook(bookId, listType, rating = null, notes = null) {
    return handleResponse(
      ragApi.post('/books/user/books', { book_id: bookId, list_type: listType, rating, notes })
    );
  },

  async finishBook(bookId) {
    return handleResponse(ragApi.post('/books/finish', { book_id: bookId }));
  },

  // Quiz methods
  async generateQuiz(title, author) {
    return handleResponse(ragApi.post('/quiz/generate', { title, author }));
  },

  async saveQuizScore(bookId, bookTitle, score, totalQuestions = 5, quizResults = null) {
    return handleResponse(authApi.post('/users/quiz/score', {
      book_id: bookId,
      book_title: bookTitle,
      score,
      total_questions: totalQuestions,
      quiz_results: quizResults
    }));
  },

  async getQuizHistory(limit = 10) {
    return handleResponse(authApi.get('/users/quiz/history', { params: { limit } }));
  },

  // ── User profile & activity (auth service — same base URL as authApi) ──────

  // GET /users/profile
  async getUserProfile() {
    const result = await handleResponse(authApi.get('/users/profile'));
    return result.success
      ? { success: true, data: result.data }
      : { success: false, error: result.error };
  },

  // PUT /users/profile
  async updateUserProfile(profileData) {
    const result = await handleResponse(authApi.put('/users/profile', profileData));
    return result.success
      ? { success: true, data: result.data }
      : { success: false, error: result.error };
  },

  // GET /users/books?list_type=finished&limit=10
  async getUserBooks(listType = 'finished', limit = 10) {
    const result = await handleResponse(
      authApi.get('/users/books', { params: { list_type: listType, limit } })
    );
    return result.success
      ? { success: true, books: result.data || [] }
      : { success: false, books: [] };
  },

  // GET /users/activity?limit=10
  async getUserActivity(limit = 10) {
    const result = await handleResponse(
      authApi.get('/users/activity', { params: { limit } })
    );
    return result.success
      ? { success: true, activities: result.data || [] }
      : { success: false, activities: [] };
  },
};