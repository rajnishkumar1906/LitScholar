// src/services/auth.js

import {
  userApi,
  handleResponse,
  setMemoryAccessToken,
  getMemoryAccessToken,
} from './api';

import { tokenManager } from '../utils/tokens';
import config from './config';


// ===== Helpers =====
const applyToken = (data) => {
  if (data?.access_token) {
    setMemoryAccessToken(data.access_token);
    tokenManager.setAccessToken(data.access_token);
  }
};

export const isAuthenticated = () => !!getMemoryAccessToken();


// ===== Auth Service =====
export const authService = {

  // ===== Login =====
  async login(email, password) {
    const res = await handleResponse(
      userApi.post('/auth/login', { email, password })
    );

    if (res.success) applyToken(res.data);
    return res;
  },

  // ===== Register =====
  async register(email, password) {
    const res = await handleResponse(
      userApi.post('/auth/register', { email, password })
    );

    if (res.success) applyToken(res.data);
    return res;
  },

  // ===== Google Login =====
  googleLogin() {
    window.location.href = `${config.USER_API_URL}/auth/google/login`;
  },

  // ===== OAuth Callback =====
  handleGoogleCallback() {
    const params = new URLSearchParams(window.location.search);
    const error = params.get('error');

    if (error) return { success: false, error };

    if (params.get('oauth') === 'success') {
      window.history.replaceState({}, document.title, window.location.pathname);
      return { success: true };
    }

    return { success: false, error: 'OAuth not completed' };
  },

  // ===== Logout =====
  async logout() {
    try {
      await handleResponse(userApi.post('/auth/logout'));
    } catch (e) {
      console.error('Logout failed:', e);
    }

    setMemoryAccessToken(null);
    tokenManager.clear();

    localStorage.clear();
    sessionStorage.clear();

    return { success: true };
  },

  // ===== Current User =====
  async getCurrentUser() {
    return await handleResponse(
      userApi.get('/users/me')
    );
  },

  // ===== Refresh Token =====
  async refreshToken() {
    const res = await handleResponse(
      userApi.post('/auth/refresh')
    );

    if (res.success && res.data?.access_token) {
      applyToken(res.data);
    }

    return res;
  },

  // ===== Ensure JWT for AI calls =====
  async ensureAiAccessToken() {
    if (getMemoryAccessToken()) return { success: true };
    return this.refreshToken();
  },

  // Backward-compatible alias used by older callers.
  async ensureRagAccessToken() {
    return this.ensureAiAccessToken();
  },

  // ===== Forgot Password =====
  async forgotPassword(email) {
    return await handleResponse(
      userApi.post('/auth/forgot-password', { email })
    );
  },

  // ===== Verify OTP =====
  async verifyOtp(email, otp) {
    return await handleResponse(
      userApi.post('/auth/verify-otp', { email, otp })
    );
  },

  // ===== Reset Password =====
  async resetPassword(email, otp, newPassword) {
    return await handleResponse(
      userApi.post('/auth/reset-password', {
        email,
        otp,
        new_password: newPassword
      })
    );
  },

  // ===== Auth Check =====
  isAuthenticated,
};