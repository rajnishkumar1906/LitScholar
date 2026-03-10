import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import LogoutConfirmModal from '../components/LogoutConfirmModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const AppContext = createContext();

const api = axios.create({
  baseURL: config.API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    console.log("📡 Request to:", config.url);
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!error.response) {
      return Promise.reject(error);
    }

    const status = error.response.status;
    const url = originalRequest?.url || '';

    if (
      status === 401 &&
      !originalRequest._retry &&
      !url.includes('/auth/refresh') &&
      !url.includes('/auth/login') &&
      !url.includes('/users/me')
    ) {
      originalRequest._retry = true;

      try {
        console.log("🔄 Attempting to refresh token...");
        await axios.post(`${config.API_URL}/auth/refresh`, {}, {
          withCredentials: true
        });

        console.log("✅ Token refreshed successfully");
        return api(originalRequest);

      } catch (refreshError) {
        console.log("❌ Token refresh failed - user needs to login");
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const AppProvider = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [lastQuery, setLastQuery] = useState('');
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const recommendedCacheRef = useRef({});
  const sectionsCacheRef = useRef(null);
  const [profileStats, setProfileStats] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      const response = await api.get('/users/me');
      setUser(response.data);
      console.log("✅ User authenticated:", response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        console.log("ℹ️ User not authenticated - this is normal");
        setUser(null);
      } else {
        console.error("❌ Auth check failed:", error);
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      await checkAuth();
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
      await checkAuth();
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

  const logout = async () => {
    setShowLogoutConfirm(true);
  };

  const confirmLogout = async () => {
    try {
      await api.post('/auth/logout');
      setUser(null);
      setShowLogoutConfirm(false);
      recommendedCacheRef.current = {};
      sectionsCacheRef.current = null;
      setProfileStats(null);
      navigate('/');
      toast.success('Logged out successfully');
    } catch (error) {
      console.error("Logout failed:", error);
      setUser(null);
      setShowLogoutConfirm(false);
      navigate('/');
    }
  };

  const cancelLogout = () => {
    setShowLogoutConfirm(false);
  };

  const searchBooks = async (query, topK = 6) => {
  setIsSearching(true);
  setLastQuery(query);

  try {
    const response = await api.post("/assistant/ask", {
      question: query,
      top_k: topK,
    });

    const { books = [], answer = "" } = response.data;

    const formattedBooks = books.map((book) => ({
      id: book.book_id,
      book_id: book.book_id,
      title: book.title,
      author: book.author,
      genres: book.genres,
      category: book.genres?.split(",")[0]?.trim() || "General",
      image_url: book.image_url,
      rating: 4.5,
      reason: "",

      answer,
    }));

    setSearchResults(formattedBooks);

    return {
      success: true,
      books: formattedBooks,
      
    };

  } catch (error) {
    console.error("Search failed:", error);

    toast.error(
      error?.response?.data?.detail ||
      "Search failed. Please try again."
    );

    return { success: false };

  } finally {
    setIsSearching(false);
  }
};

  const getBookById = async (bookId) => {
    try {
      const response = await api.get(`/books/${bookId}`);
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
      const response = await api.get(`/books/${bookId}/summary`);
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
      const bookIds = books
        .map((b) => b.id || b.book_id)
        .filter(Boolean);

      const payload = { question };
      if (bookIds.length) {
        payload.book_ids = bookIds;
      }

      const response = await api.post('/assistant/ask', payload);

      return {
        success: true,
        answer: response.data.answer,
        citations: response.data.citations,
      };
    } catch (error) {
      console.error('Follow-up question failed:', error);
      toast.error('Failed to get answer. Please try again.');
      return {
        success: false,
        error: error.response?.data?.detail || 'Follow-up failed',
      };
    }
  };

  const fetchRecommendedBooks = async (pageNumber = 1, limit = 8) => {
    const key = `${pageNumber}-${limit}`;
    
    // Check cache first (for 2 minutes)
    const cached = recommendedCacheRef.current[key];
    if (cached && Date.now() - cached.timestamp < 2 * 60 * 1000) {
      console.log(`📦 Using cached data for page ${pageNumber}`);
      return cached.data;
    }

    try {
      console.log(`📡 Fetching recommended books - page ${pageNumber}, limit ${limit}`);
      const response = await api.get(`/books/recommended?page=${pageNumber}&limit=${limit}`);

      const result = {
        success: true,
        books: response.data || [],
        hasMore: response.data.length === limit,
        page: pageNumber,
      };

      // Store in cache
      recommendedCacheRef.current[key] = {
        data: result,
        timestamp: Date.now()
      };

      console.log(`✅ Loaded ${response.data.length} books for page ${pageNumber}`);
      return result;
    } catch (error) {
      console.error('Error fetching recommended books:', error);
      
      // Return cached data if available
      if (cached) {
        console.log('📦 Using expired cache as fallback');
        return cached.data;
      }
      
      return {
        success: false,
        books: [],
        hasMore: false,
        error: error.response?.data?.detail || 'Failed to fetch recommendations',
      };
    }
  };

  const fetchRecommendedSections = async (forceRefresh = false) => {
    // Check cache first (for 5 minutes)
    if (!forceRefresh && sectionsCacheRef.current) {
      const cacheAge = Date.now() - sectionsCacheRef.current.timestamp;
      if (cacheAge < 5 * 60 * 1000) {
        console.log("📦 Using cached sections");
        return { success: true, ...sectionsCacheRef.current.data };
      }
    }

    try {
      console.log("📡 Fetching recommended sections");
      const response = await api.get('/books/recommended/sections');
      
      const data = {
        for_you: Array.isArray(response.data.for_you) ? response.data.for_you : [],
        popular: Array.isArray(response.data.popular) ? response.data.popular : [],
        by_genre: Array.isArray(response.data.by_genre) ? response.data.by_genre : [],
      };

      console.log(`✅ Sections loaded - For you: ${data.for_you.length}, Popular: ${data.popular.length}, Genres: ${data.by_genre.length}`);

      // Cache the data
      sectionsCacheRef.current = {
        data,
        timestamp: Date.now()
      };

      return { success: true, ...data };
    } catch (error) {
      console.error('Error fetching recommended sections:', error);
      
      // Return cached data if available
      if (sectionsCacheRef.current) {
        console.log('📦 Using cached sections as fallback');
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

  const trackBook = async (bookId) => {
    try {
      await api.post(`/books/track/${bookId}`);
      console.log(`📘 Book ${bookId} tracked`);
    } catch (error) {
      console.log('Error tracking book:', error);
    }
  };

  const loadProfile = useCallback(async () => {
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
  }, []);

  const updateProfile = async (profileData) => {
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
    try {
      const response = await api.get(`/users/books?list_type=${listType}&limit=${limit}`);
      return { success: true, books: response.data };
    } catch (error) {
      console.error('Error fetching user books:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load your books');
      }
      return { success: false, books: [] };
    }
  }, []);

  const fetchUserActivity = useCallback(async (limit = 10) => {
    try {
      const response = await api.get(`/users/activity?limit=${limit}`);
      return { success: true, activities: response.data };
    } catch (error) {
      console.error('Error fetching user activity:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load activity');
      }
      return { success: false, activities: [] };
    }
  }, []);

  const finishBook = async (bookId) => {
    try {
      const response = await api.post('/users/books/finish', { book_id: bookId });

      if (response.data.success) {
        toast.success('📚 Book marked as finished!');
        await loadProfile();
        return { success: true, data: response.data };
      }
      return { success: false, error: 'Failed to mark book as finished' };
    } catch (error) {
      console.error('Error finishing book:', error);
      if (error.response?.status === 400) {
        toast.error('Book already marked as finished');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to mark book as finished');
      }
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to mark book as finished',
      };
    }
  };

  const addUserBook = async (bookId, listType, rating = null, notes = null) => {
  try {
    const response = await api.post('/books/user/books', {
      book_id: bookId,
      list_type: listType,
      rating: rating,
      notes: notes
    });

    if (response.data.success) {
      toast.success(`Book added to ${listType} list!`);
      
      // Refresh user books if needed
      if (listType === 'finished') {
        await loadProfile();
      }
      
      return { success: true, data: response.data };
    }
    return { success: false, error: 'Failed to add book' };
  } catch (error) {
    console.error('Error adding user book:', error);
    if (error.response?.status === 400 && error.response?.data?.message?.includes('already')) {
      toast.info('Book already in this list');
    } else {
      toast.error(error.response?.data?.message || 'Failed to add book');
    }
    return {
      success: false,
      error: error.response?.data?.message || 'Failed to add book',
    };
  }
};

  const value = {
    user,
    loading,
    searchResults,
    isSearching,
    lastQuery,
    login,
    register,
    logout,
    googleLogin,
    isAuthenticated: () => !!user,
    searchBooks,
    getBookById,
    getBookSummary,
    askFollowUp,
    setSearchResults,
    showLogoutConfirm,
    confirmLogout,
    cancelLogout,
    fetchRecommendedBooks,
    fetchRecommendedSections,
    trackBook,
    profileStats,
    loadProfile,
    updateProfile,
    fetchUserBooks,
    fetchUserActivity,
    finishBook,
    addUserBook
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