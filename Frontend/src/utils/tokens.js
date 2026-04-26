// utils/tokens.js

import { tokenCookies } from './cookies';

let accessToken = null;

export const tokenManager = {

  // ===== Access Token (memory only) =====
  getAccessToken: () => accessToken,

  setAccessToken: (token) => {
    accessToken = token || null;
  },

  // ===== Refresh Token (cookie) =====
  getRefreshToken: () => tokenCookies.getRefreshToken(),

  setRefreshToken: (token) => {
    tokenCookies.setRefreshToken(token);
  },

  // ===== Clear =====
  clear: () => {
    accessToken = null;
    tokenCookies.clear();

    localStorage.removeItem('litscholar_access_token');
    localStorage.removeItem('litscholar_refresh_token');
  },

  // ===== Check =====
  isAuthenticated: () => !!accessToken,
};