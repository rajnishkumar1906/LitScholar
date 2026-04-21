// src/services/auth.js - Authentication service (httpOnly cookie session + in-memory JWT for RAG)
import {
  authApi,
  handleResponse,
  setMemoryAccessToken,
  getMemoryAccessToken,
} from './api';
import { tokenManager } from '../utils/tokens';
import config from './config';

function applyAuthResponseBody(data) {
  if (data?.access_token) {
    setMemoryAccessToken(data.access_token);
  }
}

/**
 * Standalone helper to check authentication.
 * Checks for the presence of the in-memory access token.
 */
export const isAuthenticated = () => !!getMemoryAccessToken();

export const authService = {
  // Login user
  async login(email, password) {
    const result = await handleResponse(
      authApi.post('/auth/login', { email, password })
    );
    
    if (result.success) {
      applyAuthResponseBody(result.data);
      return { success: true, data: result.data };
    }
    
    return { success: false, error: result.error };
  },

  // Register user
  async register(email, password) {
    const result = await handleResponse(
      authApi.post('/auth/register', { email, password })
    );
    
    if (result.success) {
      applyAuthResponseBody(result.data);
      return { success: true, data: result.data };
    }
    
    return { success: false, error: result.error };
  },

  // Google OAuth login
  googleLogin() {
    window.location.href = `${config.AUTH_API_URL}/auth/google/login`;
  },

  // Google OAuth, identity-service redirects with Set-Cookie (no tokens in URL)
  handleGoogleCallback() {
    const params = new URLSearchParams(window.location.search);
    const error = params.get('error');
    if (error) {
      return { success: false, error };
    }
    if (params.get('oauth') === 'success') {
      window.history.replaceState({}, document.title, window.location.pathname);
      return { success: true };
    }
    return { success: false, error: 'OAuth callback not completed' };
  },

  // Logout user
  async logout() {
    try {
      await handleResponse(
        authApi.post('/auth/logout')
      );
    } catch (e) {
      console.error('Logout API call failed:', e);
    }
    
    setMemoryAccessToken(null);
    tokenManager.clear();
    
    // Clear any other client-side storage
    localStorage.clear();
    sessionStorage.clear();
    
    return { success: true };
  },

  // Check if user is authenticated (legacy; prefer AppContext user after checkAuth)
  isAuthenticated,

  // Get current user
  async getCurrentUser() {
    const result = await handleResponse(
      authApi.get('/users/me')
    );
    
    return result;
  },

  // Refresh token (uses httpOnly refresh_token cookie)
  async refreshToken() {
    const result = await handleResponse(
      authApi.post('/auth/refresh')
    );
    
    if (result.success && result.data.access_token) {
      applyAuthResponseBody(result.data);
      return { success: true };
    }
    
    return result;
  },

  /** After full page load, cookie session is valid but memory JWT is empty — refresh once for RAG Bearer. */
  async ensureRagAccessToken() {
    if (getMemoryAccessToken()) return { success: true };
    return this.refreshToken();
  },

  // Forgot password
  async forgotPassword(email) {
    const result = await handleResponse(
      authApi.post('/auth/forgot-password', { email })
    );
    
    if (result.success) {
      return { success: true, message: result.data.message };
    }
    
    return { success: false, error: result.error };
  },

  // Verify OTP
  async verifyOtp(email, otp) {
    const result = await handleResponse(
      authApi.post('/auth/verify-otp', { email, otp })
    );
    
    if (result.success) {
      return { success: true, message: result.data.message };
    }
    
    return { success: false, error: result.error };
  },

  // Reset password with OTP
  async resetPassword(email, otp, newPassword) {
    const result = await handleResponse(
      authApi.post('/auth/reset-password', { email, otp, new_password: newPassword })
    );
    
    if (result.success) {
      return { success: true, message: result.data.message };
    }
    
    return { success: false, error: result.error };
  }
};
