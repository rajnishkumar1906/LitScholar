// src/services/books.js - Books service
import { ragApi } from './api';

export const booksService = {
  async searchBooks(query, topK = 10) {
    const response = await ragApi.post('/assistant/ask', {
      question: query,
      top_k: topK
    });
    return response.data;
  },

  async getBookById(bookId) {
    const response = await ragApi.get(`/books/${bookId}`);
    return response.data;
  },

  async listBooks(page = 1, limit = 20) {
    const response = await ragApi.get('/books/', {
      params: { page, limit }
    });
    return response.data;
  },

  async getBooksByGenre(genre, page = 1, limit = 20) {
    const response = await ragApi.get(`/books/by-genre/${genre}`, {
      params: { page, limit }
    });
    return response.data;
  },

  async askFollowUp(question, books) {
    const response = await ragApi.post('/assistant/ask', {
      question,
      top_k: books.length
    });
    return response.data;
  }
};
