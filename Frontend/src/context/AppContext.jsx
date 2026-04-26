// src/context/AppContext.jsx
import  { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { authService } from '../services/auth';
import { booksService } from '../services/books';
import { tokenManager } from '../utils/tokens';  // Changed from tokenCookies
import config from '../services/config';

import LogoutConfirmModal from '../components/LogoutConfirmModal';

const AppContext = createContext();

const CACHE_DURATION = config.CACHE_DURATION || 5 * 60 * 1000;

export const AppProvider = ({ children }) => {
  const navigate = useNavigate();

  // ============ STATE ============
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [lastQuery, setLastQuery] = useState('');

  const [profileStats, setProfileStats] = useState(null);

  const [forYouBooks, setForYouBooks] = useState([]);
  const [popularBooks, setPopularBooks] = useState([]);
  const [genreBooks, setGenreBooks] = useState([]);
  const [similarBooks, setSimilarBooks] = useState([]);
  const [similarHasMore, setSimilarHasMore] = useState(true);
  const [similarPage, setSimilarPage] = useState(1);

  const dashboardCacheRef = useRef({
    forYou: { data: null, timestamp: 0 },
    popular: { data: null, timestamp: 0 },
    genre: { data: null, timestamp: 0 },
    similar: { pages: {}, timestamp: 0 }
  });
  const sectionsCacheRef = useRef(null);

  // ============ AUTH ============

  useEffect(() => {
    // Session is httpOnly cookies on identity-service; always probe /users/me
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      const userResult = await authService.getCurrentUser();
      if (userResult.success) {
        await authService.ensureRagAccessToken();
        setUser(userResult.data);
      } else {
        setUser(null);
        tokenManager.clear();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      tokenManager.clear();
    } finally {
      setLoading(false);
      setAuthChecked(true);
    }
  };



  const login = async (email, password) => {
    const result = await authService.login(email, password);
    if (result.success) {
      // Re-run checkAuth to populate user state from tokens
      await checkAuth();
      setAuthChecked(true);
      toast.success("Welcome back! You're logged in 🎉");
      navigate('/dashboard', { replace: true });
    } else {
      toast.error(result.error || 'Login failed');
    }
    return result;
  };

  const register = async (email, password) => {
    const result = await authService.register(email, password);
    if (result.success) {
      // Re-run checkAuth to populate user state from tokens
      await checkAuth();
      setAuthChecked(true);
      toast.success("Account created successfully! 🎉");
      navigate('/dashboard', { replace: true });
    } else {
      toast.error(result.error || 'Registration failed');
    }
    return result;
  };

  const googleLogin = () => { 
    authService.googleLogin(); 
  };

  const handleGoogleCallback = async () => {
    const result = authService.handleGoogleCallback();
    if (result.success) {
      await checkAuth();
      navigate('/dashboard', { replace: true });
    } else {
      toast.error(result.error || 'Google login failed');
      navigate('/');
    }
  };

  const logout = () => { 
    setShowLogoutConfirm(true); 
  };

  const confirmLogout = async () => {
    await authService.logout();
    setUser(null);
    setShowLogoutConfirm(false);
    
    // Clear all caches
    dashboardCacheRef.current = {
      forYou: { data: null, timestamp: 0 },
      popular: { data: null, timestamp: 0 },
      genre: { data: null, timestamp: 0 },
      similar: { pages: {}, timestamp: 0 }
    };
    sectionsCacheRef.current = null;
    
    // Reset all state
    setForYouBooks([]);
    setPopularBooks([]);
    setGenreBooks([]);
    setSimilarBooks([]);
    setSimilarPage(1);
    setSimilarHasMore(true);
    setProfileStats(null);
    setSearchResults([]);
    
    toast.success('Logged out successfully');
    navigate('/', { replace: true });
  };

  const cancelLogout = () => { 
    setShowLogoutConfirm(false); 
  };
  
  const isAuthenticated = () => !!user;

  // ============ SEARCH ============

  const searchBooks = async (query, topK = 6) => {
    setIsSearching(true);
    setLastQuery(query);
    try {
      const result = await booksService.searchBooks(query, topK);
      if (result.success) {
        setSearchResults(result.books);
        return { success: true, books: result.books, answer: result.answer };
      } else {
        if (!result.error?.includes('401')) {
          toast.error(result.error || "Search failed. Please try again.");
        }
        return { success: false };
      }
    } catch (error) {
      console.error("Search failed:", error);
      return { success: false };
    } finally {
      setIsSearching(false);
    }
  };

  const getBookById = async (bookId) => booksService.getBookById(bookId);
  const getBookSummary = async (bookId) => booksService.getBookSummary(bookId);
  const askFollowUp = async (question, books = []) => booksService.askFollowUp(question, books);
  
  // Quiz methods
  const generateQuiz = async (title, author) => booksService.generateQuiz(title, author);
  const saveQuizScore = async (bookId, bookTitle, score, quizResults) => booksService.saveQuizScore(bookId, bookTitle, score, 5, quizResults);
  const getQuizHistory = async (limit = 10) => booksService.getQuizHistory(limit);

  // ============ RECOMMENDATIONS ============

  const fetchForYouBooks = async (limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };
    const cache = dashboardCacheRef.current.forYou;
    if (!forceRefresh && cache.data && (Date.now() - cache.timestamp) < CACHE_DURATION) {
      return { success: true, books: cache.data };
    }
    const result = await booksService.getRecommendations('for-you', limit);
    if (result.success) {
      setForYouBooks(result.books);
      dashboardCacheRef.current.forYou = { data: result.books, timestamp: Date.now() };
    }
    return result;
  };

  const fetchPopularBooks = async (limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };
    const cache = dashboardCacheRef.current.popular;
    if (!forceRefresh && cache.data && (Date.now() - cache.timestamp) < CACHE_DURATION) {
      return { success: true, books: cache.data };
    }
    const result = await booksService.getRecommendations('popular', limit);
    if (result.success) {
      setPopularBooks(result.books);
      dashboardCacheRef.current.popular = { data: result.books, timestamp: Date.now() };
    }
    return result;
  };

  const fetchGenreBooks = async (limit = 4, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };
    const cache = dashboardCacheRef.current.genre;
    if (!forceRefresh && cache.data && (Date.now() - cache.timestamp) < CACHE_DURATION) {
      return { success: true, books: cache.data };
    }
    const result = await booksService.getRecommendations('genre', limit);
    if (result.success) {
      setGenreBooks(result.books);
      dashboardCacheRef.current.genre = { data: result.books, timestamp: Date.now() };
    }
    return result;
  };

  const fetchSimilarBooks = async (page = 1, limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [], hasMore: false };
    const cacheKey = `page-${page}`;
    const cache = dashboardCacheRef.current.similar;
    if (!forceRefresh && cache.pages[cacheKey]) {
      return { success: true, books: cache.pages[cacheKey].books, hasMore: cache.pages[cacheKey].hasMore, page };
    }
    const result = await booksService.getRecommendations('similar', limit, page);
    if (result.success) {
      if (page === 1) setSimilarBooks(result.books);
      else setSimilarBooks(prev => [...prev, ...result.books]);
      setSimilarHasMore(result.hasMore);
      setSimilarPage(page);
      dashboardCacheRef.current.similar.pages[cacheKey] = { books: result.books, hasMore: result.hasMore };
      dashboardCacheRef.current.similar.timestamp = Date.now();
    }
    return result;
  };

  const fetchRecommendedSections = async (forceRefresh = false) => {
    if (!user) return { for_you: [], popular: [], by_genre: [] };
    if (!forceRefresh && sectionsCacheRef.current) {
      if ((Date.now() - sectionsCacheRef.current.timestamp) < CACHE_DURATION) {
        return sectionsCacheRef.current.data;
      }
    }
    const [forYou, popular, genre] = await Promise.all([
      fetchForYouBooks(8, forceRefresh),
      fetchPopularBooks(8, forceRefresh),
      fetchGenreBooks(4, forceRefresh)
    ]);
    const data = { for_you: forYou.books || [], popular: popular.books || [], by_genre: genre.books || [] };
    sectionsCacheRef.current = { data, timestamp: Date.now() };
    return data;
  };

  // ============ BOOK INTERACTIONS ============

  const trackBook = async (bookId) => {
    if (!user) return { success: false };
    return booksService.trackBook(bookId);
  };

  const addUserBook = async (bookId, listType, rating = null, notes = null) => {
    if (!user) {
      toast.error('Please login to add books');
      return { success: false };
    }
    const result = await booksService.addUserBook(bookId, listType, rating, notes);
    if (result.success) {
      toast.success(`Book added to ${listType} list!`);
      if (listType === 'finished') await loadProfile();
    } else if (result.error?.includes('already')) {
      toast.info('Book already in this list');
    } else if (!result.error?.includes('401')) {
      toast.error(result.error || 'Failed to add book');
    }
    return result;
  };

  const finishBook = async (bookId) => {
    if (!user) {
      toast.error('Please login to mark books as finished');
      return { success: false };
    }
    const result = await booksService.finishBook(bookId);
    if (result.success) {
      toast.success('📚 Book marked as finished!');
      await loadProfile();
    } else if (!result.error?.includes('401')) {
      toast.error(result.error || 'Failed to mark book as finished');
    }
    return result;
  };

  // ============ PROFILE ============

  const loadProfile = useCallback(async () => {
    if (!user) return { success: false };
    try {
      const result = await booksService.getUserProfile();

      if (result.success) {
        setProfileStats(result.data);
        return { success: true, profile: result.data, user };
      }

      // Fallback: return empty profile so UI doesn't crash
      const fallback = {
        total_books_read: 0,
        total_pages_read: 0,
        current_streak: 0,
        longest_streak: 0,
        yearly_goal: 12,
        monthly_goal: 0,
        yearly_progress: 0,
        monthly_progress: 0,
        categories_read: []
      };
      setProfileStats(fallback);
      return { success: true, profile: fallback, user };
    } catch (error) {
      console.error('Error loading profile:', error);
      return { success: false, error: 'Failed to load profile' };
    }
  }, [user]);

  const updateProfile = async (profileData) => {
    if (!user) return { success: false };
    try {
      const result = await booksService.updateUserProfile(profileData);
      if (result.success) {
        setProfileStats(prev => ({ ...prev, ...result.data }));
        return { success: true };
      }
      return { success: false, error: result.error };
    } catch (error) {
      console.error('Error updating profile:', error);
      return { success: false, error: 'Failed to update profile' };
    }
  };

  const fetchUserBooks = useCallback(async (listType = 'finished', limit = 10) => {
    if (!user) return { success: false, books: [] };
    try {
      const result = await booksService.getUserBooks(listType, limit);
      return result;
    } catch (error) {
      console.error('Error fetching user books:', error);
      return { success: false, books: [] };
    }
  }, [user]);

  const fetchUserActivity = useCallback(async (limit = 10) => {
    if (!user) return { success: false, activities: [] };
    try {
      const result = await booksService.getUserActivity(limit);
      return result;
    } catch (error) {
      console.error('Error fetching user activity:', error);
      return { success: false, activities: [] };
    }
  }, [user]);

  // ============ CONTEXT VALUE ============
  const value = {
    user,
    loading,
    authChecked,

    login,
    register,
    logout,
    googleLogin,
    handleGoogleCallback,
    checkAuth,

    showLogoutConfirm,
    confirmLogout,
    cancelLogout,

    isSearching,
    lastQuery,
    searchResults,
    searchBooks,
    setSearchResults,
    askFollowUp,
    generateQuiz,
    saveQuizScore,
    getQuizHistory,

    getBookById,
    getBookSummary,
    trackBook,
    addUserBook,
    finishBook,

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

    profileStats,
    loadProfile,
    updateProfile,
    fetchUserBooks,
    fetchUserActivity,


    isAuthenticated
  };

  return (
    <AppContext.Provider value={value}>
      {children}
      <LogoutConfirmModal
        isOpen={showLogoutConfirm}
        onConfirm={confirmLogout}
        onCancel={cancelLogout}
      />
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
};