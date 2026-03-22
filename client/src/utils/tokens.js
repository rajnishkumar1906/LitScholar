// Token management using localStorage (with optional sessionStorage for more security)

const ACCESS_TOKEN_KEY = 'litscholar_access_token';
const REFRESH_TOKEN_KEY = 'litscholar_refresh_token';

export const tokenManager = {
  // Get access token
  getAccessToken: () => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  
  // Get refresh token
  getRefreshToken: () => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  
  // Set both tokens
  setTokens: (accessToken, refreshToken) => {
    if (accessToken) {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    }
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
  },
  
  // Set access token only
  setAccessToken: (token) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },
  
  // Set refresh token only
  setRefreshToken: (token) => {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  },
  
  // Clear all tokens
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
  
  // Check if authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem(ACCESS_TOKEN_KEY);
  }
};