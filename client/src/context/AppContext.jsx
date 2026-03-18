import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import LogoutConfirmModal from '../components/LogoutConfirmModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const AppContext = createContext();

const api = axios.create({
  baseURL: config.AUTH_API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

const ragApi = axios.create({
  baseURL: config.RAG_API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Request interceptor for both
const addRequestInterceptor = (instance) => {
  instance.interceptors.request.use(
    (config) => {
      console.log("📡 Request to:", config.url);
      return config;
    },
    (error) => Promise.reject(error)
  );
};

addRequestInterceptor(api);
addRequestInterceptor(ragApi);

// Response interceptor with token refresh
const addResponseInterceptor = (instance) => {
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (!error.response) {
        return Promise.reject(error);
      }

      const status = error.response.status;
      const url = originalRequest?.url || '';

      // Only attempt refresh for 401 errors on protected endpoints
      if (
        status === 401 &&
        !originalRequest._retry &&
        !url.includes('/auth/login') &&
        !url.includes('/auth/register') &&
        !url.includes('/auth/refresh')
      ) {
        originalRequest._retry = true;

        try {
          console.log("🔄 Attempting to refresh token...");
          await axios.post(`${config.AUTH_API_URL}/auth/refresh`, {}, {
            withCredentials: true
          });
          console.log("✅ Token refreshed successfully");
          return instance(originalRequest);
        } catch (refreshError) {
          console.log("❌ Token refresh failed");
          if (!window.location.pathname.includes('/login') && 
              !window.location.pathname.includes('/register')) {
            window.location.href = '/login';
          }
          return Promise.reject(refreshError);
        }
      }
      return Promise.reject(error);
    }
  );
};

addResponseInterceptor(api);
addResponseInterceptor(ragApi);

export const AppProvider = ({ children }) => {
  const navigate = useNavigate();

  // Auth state
  const [user, setUser] = useState(null);
  const [subscription, setSubscription] = useState({ is_active: false });
  const [loading, setLoading] = useState(true);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  // Search state
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [lastQuery, setLastQuery] = useState('');

  // Profile state
  const [profileStats, setProfileStats] = useState(null);

  // Dashboard state (to persist across navigation)
  const [forYouBooks, setForYouBooks] = useState([]);
  const [popularBooks, setPopularBooks] = useState([]);
  const [genreBooks, setGenreBooks] = useState([]);
  const [similarBooks, setSimilarBooks] = useState([]);
  const [similarHasMore, setSimilarHasMore] = useState(true);
  const [similarPage, setSimilarPage] = useState(1);

  // Cache refs
  const dashboardCacheRef = useRef({
    forYou: { data: null, timestamp: 0 },
    popular: { data: null, timestamp: 0 },
    genre: { data: null, timestamp: 0 },
    similar: { pages: {}, timestamp: 0 }
  });
  const recommendedCacheRef = useRef({});
  const sectionsCacheRef = useRef(null);

  // ============ HELPERS ============
  const formatBook = (book) => {
    const genres = book.genres || book.book_details || "";
    let category = "General";

    if (genres) {
      // Try to extract the first genre if it's a string representation of a list
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

  // ============ AUTH FUNCTIONS ============
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      const response = await api.get('/users/me');
      const userData = response.data;
      setUser(userData);
      console.log("✅ User authenticated:", userData);
      
      // Also check subscription status
      try {
        const subResponse = await axios.get(`${config.PAYMENT_API_URL}/subscription/${userData.id}`, {
          withCredentials: true
        });
        setSubscription(subResponse.data);
      } catch (subError) {
        console.log("⚠️ Could not fetch subscription status");
      }
    } catch (error) {
      if (error.response?.status === 401) {
        console.log("ℹ️ User not authenticated");
        setUser(null);
      } else {
        console.error("❌ Auth check failed:", error);
      }
    } finally {
      setLoading(false);
      setAuthChecked(true);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      await checkAuth(); // This will set the user
      toast.success("Welcome back! You're logged in 🎉");
      navigate('/dashboard');
      return { success: true, data: response.data };
    } catch (error) {
      const msg = error.response?.data?.detail || 'Login failed';
      toast.error(msg);
      return { success: false, error: msg };
    }
  };

  const register = async (email, password) => {
    try {
      const response = await api.post('/auth/register', { email, password });
      await checkAuth(); // This will set the user
      toast.success("Account created successfully! 🎉");
      navigate('/dashboard');
      return { success: true, data: response.data };
    } catch (error) {
      const msg = error.response?.data?.detail || 'Registration failed';
      toast.error(msg);
      return { success: false, error: msg };
    }
  };

  const googleLogin = () => {
    window.location.href = `${config.API_URL}/auth/google/login`;
  };

  const logout = () => {
    setShowLogoutConfirm(true);
  };

  const confirmLogout = async () => {
    try {
      await api.post('/auth/logout');
      setUser(null);
      setShowLogoutConfirm(false);
      // Clear all caches
      dashboardCacheRef.current = {
        forYou: { data: null, timestamp: 0 },
        popular: { data: null, timestamp: 0 },
        genre: { data: null, timestamp: 0 },
        similar: { pages: {}, timestamp: 0 }
      };
      setForYouBooks([]);
      setPopularBooks([]);
      setGenreBooks([]);
      setSimilarBooks([]);
      setSimilarPage(1);
      setSimilarHasMore(true);
      
      recommendedCacheRef.current = {};
      sectionsCacheRef.current = null;
      setProfileStats(null);
      setSearchResults([]);
      navigate('/');
      toast.success('Logged out successfully');
    } catch (error) {
      console.error("Logout failed:", error);
      // Still clear user state even if API fails
      setUser(null);
      setShowLogoutConfirm(false);
      navigate('/');
    }
  };

  const cancelLogout = () => {
    setShowLogoutConfirm(false);
  };

  const isAuthenticated = () => !!user;

  // ============ BOOK SEARCH & ASSISTANT ============
  const searchBooks = async (query, topK = 6) => {
    setIsSearching(true);
    setLastQuery(query);

    try {
      const endpoint = subscription.is_active ? "/assistant/ask/premium" : "/assistant/ask";
      const response = await ragApi.post(endpoint, {
        question: query,
        top_k: topK,
      });

      const { books = [], answer = "" } = response.data;

      const formattedBooks = books.map((book) => ({
        ...formatBook(book),
        answer,
      }));

      setSearchResults(formattedBooks);
      return { success: true, books: formattedBooks };
    } catch (error) {
      console.error("Search failed:", error);
      
      // Don't show toast for 401 errors (handled by interceptor)
      if (error.response?.status !== 401) {
        toast.error(error?.response?.data?.detail || "Search failed. Please try again.");
      }
      
      return { success: false };
    } finally {
      setIsSearching(false);
    }
  };

  const getBookById = async (bookId) => {
    try {
      const response = await ragApi.get(`/books/${bookId}`);
      return { success: true, book: response.data };
    } catch (error) {
      console.error('Error fetching book by id:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch book',
      };
    }
  };

  const getBookSummary = async (bookId) => {
    try {
      const response = await ragApi.get(`/books/${bookId}/summary`);
      return { success: true, summary: response.data.summary };
    } catch (error) {
      console.error('Error fetching book summary:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch summary',
      };
    }
  };

  const askFollowUp = async (question, books = []) => {
    try {
      const bookIds = books.map((b) => b.id || b.book_id).filter(Boolean);
      const payload = { question };
      if (bookIds.length) payload.book_ids = bookIds;

      const response = await ragApi.post('/assistant/ask', payload);
      return {
        success: true,
        answer: response.data.answer,
        citations: response.data.citations,
      };
    } catch (error) {
      console.error('Follow-up question failed:', error);
      
      if (error.response?.status !== 401) {
        toast.error('Failed to get answer. Please try again.');
      }
      
      return {
        success: false,
        error: error.response?.data?.detail || 'Follow-up failed',
      };
    }
  };

  // ============ RECOMMENDATION FUNCTIONS (4 Core) ============

  /**
   * 1. FOR YOU - Personalized recommendations
   */
  const fetchForYouBooks = async (limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };

    // Use cache if available and not expired
    if (!forceRefresh && dashboardCacheRef.current.forYou.data) {
      const age = Date.now() - dashboardCacheRef.current.forYou.timestamp;
      if (age < 5 * 60 * 1000) {
        return { success: true, books: dashboardCacheRef.current.forYou.data };
      }
    }

    try {
      console.log("📡 Fetching For You recommendations");
      const response = await ragApi.get('/books/recommended/for-you', {
        params: { limit }
      });
      
      const books = (response.data.books || []).map(formatBook);
      
      // Update state and cache
      setForYouBooks(books);
      dashboardCacheRef.current.forYou = { data: books, timestamp: Date.now() };
      
      return { success: true, books };
    } catch (error) {
      console.error('Error fetching For You books:', error);
      return { success: false, books: [], error: error.response?.data?.detail || 'Failed to load For You books' };
    }
  };

  /**
   * 2. POPULAR - Trending books
   */
  const fetchPopularBooks = async (limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };

    if (!forceRefresh && dashboardCacheRef.current.popular.data) {
      const age = Date.now() - dashboardCacheRef.current.popular.timestamp;
      if (age < 5 * 60 * 1000) {
        return { success: true, books: dashboardCacheRef.current.popular.data };
      }
    }

    try {
      console.log("📡 Fetching Popular books");
      const response = await ragApi.get('/books/recommended/popular', {
        params: { limit }
      });
      
      const books = (response.data.books || []).map(formatBook);
      
      setPopularBooks(books);
      dashboardCacheRef.current.popular = { data: books, timestamp: Date.now() };
      
      return { success: true, books };
    } catch (error) {
      console.error('Error fetching Popular books:', error);
      return { success: false, books: [], error: error.response?.data?.detail || 'Failed to load Popular books' };
    }
  };

  /**
   * 3. BY GENRE - Books grouped by genre
   */
  const fetchGenreBooks = async (limit = 4, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };

    if (!forceRefresh && dashboardCacheRef.current.genre.data) {
      const age = Date.now() - dashboardCacheRef.current.genre.timestamp;
      if (age < 5 * 60 * 1000) {
        return { success: true, books: dashboardCacheRef.current.genre.data };
      }
    }

    try {
      console.log("📡 Fetching Genre books");
      const response = await ragApi.get('/books/recommended/by-genre', {
        params: { limit }
      });
      
      const genreData = (response.data.books || []).map(section => ({
        ...section,
        books: (section.books || []).map(formatBook)
      }));
      
      setGenreBooks(genreData);
      dashboardCacheRef.current.genre = { data: genreData, timestamp: Date.now() };
      
      return { success: true, books: genreData };
    } catch (error) {
      console.error('Error fetching Genre books:', error);
      return { success: false, books: [], error: error.response?.data?.detail || 'Failed to load Genre books' };
    }
  };

  /**
   * 4. SIMILAR - Similar books with pagination
   */
  const fetchSimilarBooks = async (page = 1, limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [], hasMore: false, page };

    const cacheKey = `page-${page}`;
    
    if (!forceRefresh && dashboardCacheRef.current.similar.pages[cacheKey]) {
      return { 
        success: true, 
        books: dashboardCacheRef.current.similar.pages[cacheKey].books,
        hasMore: dashboardCacheRef.current.similar.pages[cacheKey].hasMore,
        page
      };
    }

    try {
      console.log(`📡 Fetching Similar books - page ${page}, limit ${limit}`);
      const response = await ragApi.get('/books/recommended/similar', {
        params: { page, limit }
      });

      const books = (response.data.books || []).map(formatBook);
      const hasMore = response.data.hasMore || false;

      // Update state: append if it's a new page
      if (page === 1) {
        setSimilarBooks(books);
      } else {
        setSimilarBooks(prev => [...prev, ...books]);
      }
      
      setSimilarHasMore(hasMore);
      setSimilarPage(page);

      // Update cache
      dashboardCacheRef.current.similar.pages[cacheKey] = { books, hasMore };
      dashboardCacheRef.current.similar.timestamp = Date.now();

      return { success: true, books, hasMore, page };
    } catch (error) {
      console.error('Error fetching Similar books:', error);
      return { success: false, books: [], hasMore: false, error: error.response?.data?.detail || 'Failed to load Similar books' };
    }
  };

  /**
   * Get all recommendation sections at once (for dashboard)
   */
  const fetchRecommendedSections = async (forceRefresh = false) => {
    // Don't fetch if not authenticated
    if (!user) {
      console.log("⏳ Skipping sections fetch - user not authenticated");
      return { 
        success: false, 
        for_you: [], 
        popular: [], 
        by_genre: [] 
      };
    }

    // Check cache (5 minutes)
    if (!forceRefresh && sectionsCacheRef.current) {
      const cacheAge = Date.now() - sectionsCacheRef.current.timestamp;
      if (cacheAge < 5 * 60 * 1000) {
        console.log("📦 Using cached sections");
        return { success: true, ...sectionsCacheRef.current.data };
      }
    }

    try {
      console.log("📡 Fetching recommended sections");
      const response = await ragApi.get('/books/recommended/sections');

      const data = {
        for_you: response.data.for_you || [],
        popular: response.data.popular || [],
        by_genre: response.data.by_genre || [],
      };

      sectionsCacheRef.current = {
        data,
        timestamp: Date.now()
      };

      return { success: true, ...data };
    } catch (error) {
      console.error('Error fetching recommended sections:', error);

      if (sectionsCacheRef.current) {
        return { success: true, ...sectionsCacheRef.current.data };
      }

      return {
        success: false,
        for_you: [],
        popular: [],
        by_genre: [],
        error: error.response?.data?.detail || 'Failed to load recommendations',
      };
    }
  };

  // ============ USER BOOK INTERACTIONS ============

  const trackBook = async (bookId) => {
    if (!user) return { success: false };
    
    try {
      await ragApi.post(`/books/track/${bookId}`);
      console.log(`📘 Book ${bookId} tracked`);
      return { success: true };
    } catch (error) {
      console.log('Error tracking book:', error);
      return { success: false };
    }
  };

  const addUserBook = async (bookId, listType, rating = null, notes = null) => {
    if (!user) {
      toast.error('Please login to add books');
      return { success: false };
    }

    try {
      const response = await ragApi.post('/books/user/books', {
        book_id: bookId,
        list_type: listType,
        rating,
        notes
      });

      if (response.data.success) {
        toast.success(`Book added to ${listType} list!`);
        if (listType === 'finished') await loadProfile();
        return { success: true, data: response.data };
      }
      return { success: false, error: 'Failed to add book' };
    } catch (error) {
      console.error('Error adding user book:', error);
      if (error.response?.status === 400 && error.response?.data?.message?.includes('already')) {
        toast.info('Book already in this list');
      } else if (error.response?.status !== 401) {
        toast.error(error.response?.data?.message || 'Failed to add book');
      }
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to add book',
      };
    }
  };

  const finishBook = async (bookId) => {
    if (!user) {
      toast.error('Please login to mark books as finished');
      return { success: false };
    }

    try {
      const response = await ragApi.post('/books/finish', { book_id: bookId });

      if (response.data.success) {
        toast.success('📚 Book marked as finished!');
        await loadProfile();
        return { success: true, data: response.data };
      }
      return { success: false, error: 'Failed to mark book as finished' };
    } catch (error) {
      console.error('Error finishing book:', error);

      if (error.response?.status === 400) {
        toast.error('Invalid request');
      } else if (error.response?.status === 404) {
        toast.error('Book not found');
      } else if (error.response?.status !== 401) {
        toast.error(error.response?.data?.detail || 'Failed to mark book as finished');
      }

      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to mark book as finished',
      };
    }
  };

  // ============ PROFILE FUNCTIONS ============

  const loadProfile = useCallback(async () => {
    if (!user) return { success: false };

    try {
      const [profileRes, userRes] = await Promise.all([
        api.get('/users/profile'),
        api.get('/users/me')
      ]);

      const profileData = {
        ...profileRes.data,
        user: userRes.data
      };

      setProfileStats(profileData);
      return { success: true, profile: profileRes.data, user: userRes.data };
    } catch (error) {
      console.error('Error loading profile:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load profile');
      }
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load profile',
      };
    }
  }, [user]);

  const updateProfile = async (profileData) => {
    if (!user) return { success: false };

    try {
      const response = await api.put('/users/profile', profileData);
      if (response.data) {
        setProfileStats(prev => ({
          ...prev,
          ...response.data,
          user: prev?.user || response.data.user
        }));
      }
      toast.success('Profile updated successfully!');
      return { success: true, profile: response.data };
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(error.response?.data?.detail || 'Failed to update profile');
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update profile',
      };
    }
  };

  const fetchUserBooks = useCallback(async (listType = 'finished', limit = 10) => {
    if (!user) return { success: false, books: [] };

    try {
      const response = await api.get(`/users/books?list_type=${listType}&limit=${limit}`);
      const formattedBooks = (response.data || []).map(formatBook);
      return { success: true, books: formattedBooks };
    } catch (error) {
      console.error('Error fetching user books:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load your books');
      }
      return { success: false, books: [] };
    }
  }, [user]);

  const fetchUserActivity = useCallback(async (limit = 10) => {
    if (!user) return { success: false, activities: [] };

    try {
      const response = await api.get(`/users/activity?limit=${limit}`);
      const formattedActivities = (response.data || []).map(activity => ({
        ...activity,
        book: activity.book_title ? formatBook({
          book_id: activity.book_id,
          book_title: activity.book_title,
          // activity data might not have all fields, but formatBook handles defaults
        }) : null
      }));
      return { success: true, activities: formattedActivities };
    } catch (error) {
      console.error('Error fetching user activity:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load activity');
      }
      return { success: false, activities: [] };
    }
  }, [user]);

  // ============ CONTEXT VALUE ============
  const value = {
    // Auth
    user,
    subscription,
    loading,
    authChecked,
    login,
    register,
    logout,
    googleLogin,
    isAuthenticated,
    showLogoutConfirm,
    confirmLogout,
    cancelLogout,

    // Search & Assistant
    searchResults,
    isSearching,
    lastQuery,
    searchBooks,
    getBookById,
    getBookSummary,
    askFollowUp,
    setSearchResults,

    // Recommendations (4 Core)
    forYouBooks,
    popularBooks,
    genreBooks,
    similarBooks,
    similarHasMore,
    similarPage,
    fetchForYouBooks,
    fetchPopularBooks,
    fetchGenreBooks,
    fetchSimilarBooks,
    fetchRecommendedSections,

    // Book Interactions
    trackBook,
    addUserBook,
    finishBook,

    // Profile
    profileStats,
    loadProfile,
    updateProfile,
    fetchUserBooks,
    fetchUserActivity,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
      <LogoutConfirmModal
        isOpen={showLogoutConfirm}
        onConfirm={confirmLogout}
        onCancel={cancelLogout}
      />
      <ToastContainer
        position="top-right"
        autoClose={2500}
        theme="dark"
        limit={4}
        newestOnTop
        pauseOnHover
      />
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};
