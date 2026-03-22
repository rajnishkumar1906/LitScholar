// // src/services/auth.js - Authentication service
// import { authApi, handleResponse } from './api';
// import { tokenCookies } from '../utils/cookies';
// import config from './config';

// export const authService = {
//   // Login user
//   async login(email, password) {
//     const result = await handleResponse(
//       authApi.post('/auth/login', { email, password })
//     );
    
//     if (result.success) {
//       // Server sets HTTP-only cookies, but we track auth status
//       tokenCookies.setTokens('authenticated', 'authenticated');
//       return { success: true, data: result.data };
//     }
    
//     return { success: false, error: result.error };
//   },

//   // Register user
//   async register(email, password) {
//     const result = await handleResponse(
//       authApi.post('/auth/register', { email, password })
//     );
    
//     if (result.success) {
//       tokenCookies.setTokens('authenticated', 'authenticated');
//       return { success: true, data: result.data };
//     }
    
//     return { success: false, error: result.error };
//   },

//   // Google OAuth login
//   googleLogin() {
//     window.location.href = `${config.AUTH_API_URL}/auth/google/login`;
//   },

//   // Handle Google OAuth callback
//   handleGoogleCallback() {
//     const params = new URLSearchParams(window.location.search);
//     const accessToken = params.get('access_token');
//     const refreshToken = params.get('refresh_token');
//     const error = params.get('error');

//     if (error) {
//       return { success: false, error };
//     }

//     if (accessToken) {
//       // Store tokens in cookies
//       tokenCookies.setTokens(accessToken, refreshToken || '');
//       return { success: true };
//     }
    
//     return { success: false, error: 'No access token received' };
//   },

//   // Logout user
//   async logout() {
//     const result = await handleResponse(
//       authApi.post('/auth/logout', {})
//     );
    
//     // Clear cookies regardless of API response
//     tokenCookies.clear();
    
//     // Clear any other client-side storage
//     localStorage.clear();
//     sessionStorage.clear();
    
//     return result;
//   },

//   // Check if user is authenticated
//   isAuthenticated() {
//     return tokenCookies.hasAccessToken();
//   },

//   // Get current user
//   async getCurrentUser() {
//     // If no token, return early
//     if (!tokenCookies.hasAccessToken()) {
//       return { success: false, error: 'Not authenticated' };
//     }
    
//     const result = await handleResponse(authApi.get('/users/me'));
//     return result;
//   },

//   // Refresh token
//   async refreshToken() {
//     const result = await handleResponse(
//       authApi.post('/auth/refresh', {})
//     );
//     return result;
//   }
// };


// src/services/auth.js - Authentication service
import { authApi, handleResponse } from './api';
import { tokenManager } from '../utils/tokens';
import config from './config';

export const authService = {
  // Login user
  async login(email, password) {
    const result = await handleResponse(
      authApi.post('/auth/login', { email, password })
    );
    
    if (result.success) {
      // Tokens come in response body, not cookies
      const { access_token, refresh_token } = result.data;
      if (access_token) {
        tokenManager.setTokens(access_token, refresh_token);
      }
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
      const { access_token, refresh_token } = result.data;
      if (access_token) {
        tokenManager.setTokens(access_token, refresh_token);
      }
      return { success: true, data: result.data };
    }
    
    return { success: false, error: result.error };
  },

  // Google OAuth login
  googleLogin() {
    window.location.href = `${config.AUTH_API_URL}/auth/google/login`;
  },

  // Handle Google OAuth callback (tokens come in URL fragment)
  handleGoogleCallback() {
    // Parse URL fragment (everything after #)
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const error = params.get('error');

    if (error) {
      return { success: false, error };
    }

    if (accessToken) {
      tokenManager.setTokens(accessToken, refreshToken || '');
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      return { success: true };
    }
    
    return { success: false, error: 'No access token received' };
  },

  // Logout user
  async logout() {
    const refreshToken = tokenManager.getRefreshToken();
    
    if (refreshToken) {
      await handleResponse(
        authApi.post('/auth/logout', { refresh_token: refreshToken })
      );
    }
    
    // Clear tokens regardless of API response
    tokenManager.clear();
    
    // Clear any other client-side storage
    localStorage.clear();
    sessionStorage.clear();
    
    return { success: true };
  },

  // Check if user is authenticated
  isAuthenticated() {
    return tokenManager.isAuthenticated();
  },

  // Get current user
  async getCurrentUser() {
    // If no token, return early
    if (!tokenManager.isAuthenticated()) {
      return { success: false, error: 'Not authenticated' };
    }
    
    const result = await handleResponse(authApi.get('/users/me'));
    return result;
  },

  // Refresh token
  async refreshToken() {
    const refreshToken = tokenManager.getRefreshToken();
    if (!refreshToken) {
      return { success: false, error: 'No refresh token' };
    }
    
    const result = await handleResponse(
      authApi.post('/auth/refresh', { refresh_token: refreshToken })
    );
    
    if (result.success && result.data.access_token) {
      tokenManager.setTokens(
        result.data.access_token,
        result.data.refresh_token || refreshToken
      );
      return { success: true };
    }
    
    return result;
  }
};