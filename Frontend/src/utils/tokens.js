// Token management using cookies (was using localStorage)
import { tokenCookies } from './cookies';

export const tokenManager = {
  // Get access token
  getAccessToken: () => {
    return tokenCookies.getAccessToken();
  },
  
  // Get refresh token
  getRefreshToken: () => {
    return tokenCookies.getRefreshToken();
  },
  
  // Set both tokens
  setTokens: (accessToken, refreshToken) => {
    if (accessToken) {
      tokenCookies.setAccessToken(accessToken);
    }
    if (refreshToken) {
      tokenCookies.setRefreshToken(refreshToken);
    }
  },
  
  // Set access token only
  setAccessToken: (token) => {
    tokenCookies.setAccessToken(token);
  },
  
  // Set refresh token only
  setRefreshToken: (token) => {
    tokenCookies.setRefreshToken(token);
  },
  
  // Clear all tokens
  clear: () => {
    tokenCookies.clear();
    // Also clear localStorage just in case of old data
    localStorage.removeItem('litscholar_access_token');
    localStorage.removeItem('litscholar_refresh_token');
  },
  
  // Check if authenticated
  isAuthenticated: () => {
    return !!tokenCookies.getAccessToken();
  }
};