// src/context/AppContext.jsx - Updated with tokenCookies
import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Services and utils
import { authService } from '../services/auth';
import { booksService } from '../services/books';
import { paymentService } from '../services/payments';
import { tokenCookies } from '../utils/cookies';
import config from '../services/config';

// Components
import LogoutConfirmModal from '../components/LogoutConfirmModal';

const AppContext = createContext();

// Cache duration
const CACHE_DURATION = config.CACHE_DURATION || 5 * 60 * 1000; // 5 minutes

export const AppProvider = ({ children }) => {
  const navigate = useNavigate();

  // ============ STATE ============
  // Auth state
  const [user, setUser] = useState(null);
  const [subscription, setSubscription] = useState({ is_active: false });
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // Search state
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [lastQuery, setLastQuery] = useState('');

  // Profile state
  const [profileStats, setProfileStats] = useState(null);

  // Dashboard state
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
  const sectionsCacheRef = useRef(null);

  // ============ AUTH FUNCTIONS ============
  
  // Check authentication on mount
  useEffect(() => {
    // Only check auth if we have a token
    if (tokenCookies.hasAccessToken()) {
      checkAuth();
    } else {
      setLoading(false);
      setAuthChecked(true);
    }
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    
    try {
      // Get current user
      const userResult = await authService.getCurrentUser();
      
      if (userResult.success) {
        setUser(userResult.data);
        
        // Get subscription status
        const subResult = await paymentService.getSubscriptionStatus(userResult.data.id);
        setSubscription(subResult);
      } else {
        setUser(null);
        setSubscription({ is_active: false });
        // Clear cookies if user fetch fails
        tokenCookies.clear();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setSubscription({ is_active: false });
      tokenCookies.clear();
    } finally {
      setLoading(false);
      setAuthChecked(true);
    }
  };

  const login = async (email, password) => {
    const result = await authService.login(email, password);
    
    if (result.success) {
      await checkAuth(); // Refresh user data
      toast.success("Welcome back! You're logged in 🎉");
      navigate('/dashboard');
    } else {
      toast.error(result.error || 'Login failed');
    }
    
    return result;
  };

  const register = async (email, password) => {
    const result = await authService.register(email, password);
    
    if (result.success) {
      await checkAuth(); // Refresh user data
      toast.success("Account created successfully! 🎉");
      navigate('/dashboard');
    } else {
      toast.error(result.error || 'Registration failed');
    }
    
    return result;
  };

  const googleLogin = () => {
    authService.googleLogin();
  };

  // Handle Google OAuth callback (call this from your callback page)
  const handleGoogleCallback = () => {
    const result = authService.handleGoogleCallback();
    if (result.success) {
      checkAuth();
      navigate('/dashboard');
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
    
    // Clear all state
    setUser(null);
    setSubscription({ is_active: false });
    setShowLogoutConfirm(false);
    
    // Clear caches
    dashboardCacheRef.current = {
      forYou: { data: null, timestamp: 0 },
      popular: { data: null, timestamp: 0 },
      genre: { data: null, timestamp: 0 },
      similar: { pages: {}, timestamp: 0 }
    };
    sectionsCacheRef.current = null;
    
    // Clear state
    setForYouBooks([]);
    setPopularBooks([]);
    setGenreBooks([]);
    setSimilarBooks([]);
    setSimilarPage(1);
    setSimilarHasMore(true);
    setProfileStats(null);
    setSearchResults([]);
    
    toast.success('Logged out successfully');
    navigate('/');
  };

  const cancelLogout = () => {
    setShowLogoutConfirm(false);
  };

  const isAuthenticated = () => !!user;

  // ============ SEARCH FUNCTIONS ============
  
  const searchBooks = async (query, topK = 6) => {
    setIsSearching(true);
    setLastQuery(query);

    try {
      const result = await booksService.searchBooks(query, topK, subscription.is_active);
      
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

  const getBookById = async (bookId) => {
    return booksService.getBookById(bookId);
  };

  const getBookSummary = async (bookId) => {
    return booksService.getBookSummary(bookId);
  };

  const askFollowUp = async (question, books = []) => {
    return booksService.askFollowUp(question, books);
  };

  // ============ RECOMMENDATION FUNCTIONS ============

  const fetchForYouBooks = async (limit = 8, forceRefresh = false) => {
    if (!user) return { success: false, books: [] };

    // Check cache
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
      return { 
        success: true, 
        books: cache.pages[cacheKey].books,
        hasMore: cache.pages[cacheKey].hasMore,
        page
      };
    }

    const result = await booksService.getRecommendations('similar', limit, page);
    
    if (result.success) {
      if (page === 1) {
        setSimilarBooks(result.books);
      } else {
        setSimilarBooks(prev => [...prev, ...result.books]);
      }
      
      setSimilarHasMore(result.hasMore);
      setSimilarPage(page);

      dashboardCacheRef.current.similar.pages[cacheKey] = { 
        books: result.books, 
        hasMore: result.hasMore 
      };
      dashboardCacheRef.current.similar.timestamp = Date.now();
    }
    
    return result;
  };

  const fetchRecommendedSections = async (forceRefresh = false) => {
    if (!user) {
      return { for_you: [], popular: [], by_genre: [] };
    }

    if (!forceRefresh && sectionsCacheRef.current) {
      const cacheAge = Date.now() - sectionsCacheRef.current.timestamp;
      if (cacheAge < CACHE_DURATION) {
        return sectionsCacheRef.current.data;
      }
    }

    // Fetch all sections in parallel
    const [forYou, popular, genre] = await Promise.all([
      fetchForYouBooks(8, forceRefresh),
      fetchPopularBooks(8, forceRefresh),
      fetchGenreBooks(4, forceRefresh)
    ]);

    const data = {
      for_you: forYou.books || [],
      popular: popular.books || [],
      by_genre: genre.books || []
    };

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

  // ============ PROFILE FUNCTIONS ============

  const loadProfile = useCallback(async () => {
    if (!user) return { success: false };

    try {
      // This would be replaced with actual profile API calls
      const profileData = {
        reading_stats: {
          books_finished: 0,
          total_pages: 0,
          favorite_genres: []
        },
        user: user
      };
      
      setProfileStats(profileData);
      return { success: true, profile: profileData };
    } catch (error) {
      console.error('Error loading profile:', error);
      return { success: false, error: 'Failed to load profile' };
    }
  }, [user]);

  const updateProfile = async (profileData) => {
    if (!user) return { success: false };

    // This would be replaced with actual profile update API
    setProfileStats(prev => ({ ...prev, ...profileData }));
    toast.success('Profile updated successfully!');
    
    return { success: true };
  };

  const fetchUserBooks = useCallback(async (listType = 'finished', limit = 10) => {
    if (!user) return { success: false, books: [] };

    // This would be replaced with actual API call
    return { success: true, books: [] };
  }, [user]);

  const fetchUserActivity = useCallback(async (limit = 10) => {
    if (!user) return { success: false, activities: [] };

    // This would be replaced with actual API call
    return { success: true, activities: [] };
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
    handleGoogleCallback,
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

    // Recommendations
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