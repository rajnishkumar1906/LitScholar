// src/services/books.js

import { aiApi, userApi, handleResponse } from './api';
import { allowClientTrack } from '../utils/trackRateLimit';


// ===== Format Book =====
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


// ===== Books Service =====
export const booksService = {

  // ===== Search (AI) =====
  async searchBooks(query, topK = 10) {
    const res = await handleResponse(
      aiApi.post('/assistant/ask', { question: query, top_k: topK })
    );

    if (!res.success) return res;

    const { books = [], answer = "" } = res.data;

    return {
      success: true,
      books: books.map(formatBook),
      answer
    };
  },


  // ===== Book Details =====
  async getBookById(bookId) {
    const res = await handleResponse(aiApi.get(`/books/${bookId}`));
    if (!res.success) return res;

    return { success: true, book: formatBook(res.data) };
  },


  // ===== Summary =====
  async getBookSummary(bookId) {
    return await handleResponse(aiApi.get(`/books/${bookId}/summary`));
  },


  // ===== List =====
  async listBooks(page = 1, limit = 20) {
    const res = await handleResponse(
      aiApi.get('/books/', { params: { page, limit } })
    );

    if (!res.success) return res;

    return {
      success: true,
      books: (res.data.books || []).map(formatBook),
      total: res.data.total || 0,
      page: res.data.page || page,
      hasMore: res.data.hasMore || false
    };
  },


  // ===== Genre =====
  async getBooksByGenre(genre, page = 1, limit = 20) {
    const res = await handleResponse(
      aiApi.get(`/books/by-genre/${encodeURIComponent(genre)}`, { params: { page, limit } })
    );

    if (!res.success) return res;

    return {
      success: true,
      books: (res.data.books || []).map(formatBook),
      total: res.data.total || 0,
      genre
    };
  },


  // ===== Follow-up AI =====
  async askFollowUp(question, books = []) {
    const bookIds = books.map(b => String(b.id || b.book_id)).filter(Boolean);

    const payload = { question };
    if (bookIds.length) payload.book_ids = bookIds;

    const res = await handleResponse(aiApi.post('/assistant/ask', payload));

    if (!res.success) return res;

    return {
      success: true,
      answer: res.data.answer,
      books: (res.data.books || []).map(formatBook),
      citations: res.data.citations || {}
    };
  },

  // ===== Quiz (AI Service) =====
  async generateQuiz(title, author) {
    return handleResponse(
      aiApi.post('/quiz/generate', { title, author })
    );
  },


  // ===== Recommendations =====
  async getRecommendations(type = 'for-you', limit = 8, page = 1) {
    const endpoints = {
      'for-you': '/books/recommended/for-you',
      'popular': '/books/recommended/popular',
      'similar': '/books/recommended/similar',
      'genre': '/books/recommended/by-genre',
    };

    const res = await handleResponse(
      aiApi.get(endpoints[type] || endpoints['for-you'], { params: { limit, page } })
    );

    if (!res.success) return res;

    return {
      success: true,
      books: (res.data.books || []).map(formatBook),
      hasMore: res.data.hasMore || false,
      page: res.data.page || page
    };
  },


  // ===== Track =====
  async trackBook(bookId) {
    if (!allowClientTrack(bookId)) {
      return { success: true, skipped: true };
    }

    try {
      const res = await aiApi.post(`/books/track/${bookId}`);
      return { success: true, data: res.data };

    } catch (error) {
      if (error.status === 429) {
        return { success: true, skipped: true, rateLimited: true };
      }

      return {
        success: false,
        error: error.error || 'Error'
      };
    }
  },


  // ===== User Book Actions =====
  async addUserBook(bookId, listType, rating = null, notes = null) {
    return handleResponse(
      aiApi.post('/books/user/books', {
        book_id: bookId,
        list_type: listType,
        rating,
        notes
      })
    );
  },

  async finishBook(bookId) {
    return handleResponse(
      aiApi.post('/books/finish', { book_id: bookId })
    );
  },


  // ===== Quiz (User Service) =====
  async saveQuizScore(bookId, bookTitle, score, totalQuestions = 5, quizResults = null) {
    return handleResponse(
      userApi.post('/users/quiz/score', {
        book_id: bookId,
        book_title: bookTitle,
        score,
        total_questions: totalQuestions,
        quiz_results: quizResults
      })
    );
  },

  async getQuizHistory(limit = 10) {
    return handleResponse(
      userApi.get('/users/quiz/history', { params: { limit } })
    );
  },


  // ===== Profile (User Service) =====
  async getUserProfile() {
    return handleResponse(userApi.get('/users/profile'));
  },

  async updateUserProfile(data) {
    return handleResponse(userApi.put('/users/profile', data));
  },

  async getUserBooks(listType = 'finished', limit = 10) {
    return handleResponse(
      userApi.get('/users/books', { params: { list_type: listType, limit } })
    );
  },

  async getUserActivity(limit = 10) {
    return handleResponse(
      userApi.get('/users/activity', { params: { limit } })
    );
  },
};