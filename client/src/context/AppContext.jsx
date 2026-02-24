// src/context/AppContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import { tokenCookies } from '../utils/cookies';
import LogoutConfirmModal from '../components/LogoutConfirmModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const AppContext = createContext();

// API instance
const api = axios.create({
  baseURL: config.API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ✅ Request interceptor (NO token logging)
api.interceptors.request.use(
  (config) => {
    const token = tokenCookies.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ✅ Response interceptor (removed sensitive logs)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = tokenCookies.getRefreshToken();
        if (refreshToken) {
          const response = await axios.post(`${config.API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          tokenCookies.setAccessToken(response.data.access_token);

          if (response.data.refresh_token) {
            tokenCookies.setRefreshToken(response.data.refresh_token);
          }

          api.defaults.headers.common.Authorization =
            `Bearer ${response.data.access_token}`;

          originalRequest.headers.Authorization =
            `Bearer ${response.data.access_token}`;

          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error("Token refresh failed");
        tokenCookies.clear();
        window.location.href = '/';
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

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has('access_token') || params.has('error')) {
      handleGoogleCallback();
    }
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      const accessToken = tokenCookies.getAccessToken();
      if (!accessToken) return;

      const response = await api.get('/users/me');
      setUser(response.data);
    } catch (error) {
      console.error("Auth check failed");

      if (error?.response?.status === 401 || error?.response?.status === 403) {
        tokenCookies.clear();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      toast.success("Welcome back! You're logged in 🎉");

      if (response.data.access_token) {
        tokenCookies.setTokens(
          response.data.access_token,
          response.data.refresh_token ?? tokenCookies.getRefreshToken()
        );
        await checkAuth();
      }

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
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };

  const googleLogin = () => {
    window.location.href = `${config.API_URL}/auth/google/login`;
  };

  const handleGoogleCallback = async () => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const error = params.get('error');
    const errorDesc = params.get('error_description');

    window.history.replaceState({}, document.title, window.location.pathname);

    if (error) {
      alert(`Google login failed: ${errorDesc || error}`);
      navigate('/login');
      return false;
    }

    if (!accessToken) {
      alert("Google login failed: No authentication token received");
      navigate('/login');
      return false;
    }

    tokenCookies.setTokens(accessToken, refreshToken ?? '');

    try {
      await checkAuth();
      navigate('/dashboard');
      toast.success("Welcome back! You're logged in 🎉");
      return true;
    } catch {
      tokenCookies.clear();
      alert("Session verification failed.");
      navigate('/login');
      return false;
    }
  };

  const logout = () => setShowLogoutConfirm(true);

  const confirmLogout = () => {
    tokenCookies.clear();
    setUser(null);
    setShowLogoutConfirm(false);
    navigate('/');
    toast.success('Logged out successfully');
  };

  const cancelLogout = () => setShowLogoutConfirm(false);

  const searchBooks = async (query, topK = 6) => {
    setIsSearching(true);
    setLastQuery(query);

    try {
      const response = await api.post('/assistant/ask', {
        question: query,
        top_k: topK,
      });

      const books = response.data.sources.map((source) => ({
        id: source.book_id,
        title: source.title,
        author: source.author,
        reason: source.description
          ? source.description.substring(0, 120) + '...'
          : 'No description available',
        category: source.genres?.split(',')[0]?.trim() || 'General',
        rating: 4.5,
        description: source.description,
        genres: source.genres,
        num_pages: source.num_pages,
        image_url: source.image_url,
        answer: response.data.answer,
        citations: response.data.citations,
      }));

      setSearchResults(books);
      return { success: true, books };
    } catch {
      return { success: false, error: 'Search failed' };
    } finally {
      setIsSearching(false);
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
    handleGoogleCallback,
    isAuthenticated: () => !!user,
    searchBooks,
    setSearchResults,
    showLogoutConfirm,
    confirmLogout,
    cancelLogout,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
      <LogoutConfirmModal />
      <ToastContainer position="top-right" autoClose={2500} theme="dark" limit={4}/>
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
};