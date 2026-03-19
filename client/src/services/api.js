// src/services/api.js - API clients for microservices
import axios from 'axios';
import config from './config';
import { tokenCookies } from '../utils/cookies';

// Create axios instance with common configuration
const createInstance = (baseURL, serviceName = '') => {
  const instance = axios.create({
    baseURL,
    withCredentials: true, // Important! This sends cookies
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 seconds timeout
  });

  // Request interceptor for logging
  instance.interceptors.request.use(
    (config) => {
      if (import.meta.env.DEV) {
        console.log(`🚀 [${serviceName}] ${config.method?.toUpperCase()} ${config.url}`);
      }
      
      // Don't modify GET requests with timestamp - let browser cache work
      return config;
    },
    (error) => {
      console.error(`❌ [${serviceName}] Request error:`, error);
      return Promise.reject(error);
    }
  );

  // Response interceptor for token refresh and error handling
  instance.interceptors.response.use(
    (response) => {
      if (import.meta.env.DEV) {
        console.log(`✅ [${serviceName}] Response:`, response.status);
      }
      return response;
    },
    async (error) => {
      const originalRequest = error.config;
      
      // Don't log 401 errors for auth endpoints (they're expected)
      const isAuthEndpoint = originalRequest.url?.includes('/auth/') || 
                             originalRequest.url?.includes('/users/me');
      
      if (!isAuthEndpoint && import.meta.env.DEV) {
        console.error(`❌ [${serviceName}] Response error:`, {
          status: error.response?.status,
          url: originalRequest.url,
          message: error.response?.data?.detail || error.message
        });
      }
      
      // Handle 401 Unauthorized - token refresh
      if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
        originalRequest._retry = true;
        
        try {
          console.log(`🔄 [${serviceName}] Attempting token refresh...`);
          
          // Call refresh token endpoint - cookies are sent automatically with withCredentials
          await axios.post(`${config.AUTH_API_URL}/auth/refresh`, {}, {
            withCredentials: true,
            timeout: 10000
          });
          
          console.log(`✅ [${serviceName}] Token refreshed, retrying request`);
          
          // Retry the original request
          return instance(originalRequest);
        } catch (refreshError) {
          console.error(`❌ [${serviceName}] Token refresh failed:`, refreshError);
          
          // Clear cookies
          tokenCookies.clear();
          
          // Only redirect to login if not already there
          if (!window.location.pathname.includes('/') && 
              !window.location.pathname.includes('/pricing')) {
            window.location.href = '/';
          }
          
          return Promise.reject(refreshError);
        }
      }
      
      // Handle network errors
      if (!error.response) {
        console.error(`❌ [${serviceName}] Network error:`, error.message);
        return Promise.reject({
          success: false,
          error: 'Network error. Please check your connection.'
        });
      }
      
      // Handle specific HTTP status codes
      switch (error.response.status) {
        case 400:
          return Promise.reject({
            success: false,
            error: error.response.data?.detail || 'Bad request'
          });
        case 403:
          return Promise.reject({
            success: false,
            error: 'You don\'t have permission to perform this action'
          });
        case 404:
          return Promise.reject({
            success: false,
            error: 'Resource not found'
          });
        case 429:
          return Promise.reject({
            success: false,
            error: 'Too many requests. Please try again later.'
          });
        case 500:
          return Promise.reject({
            success: false,
            error: 'Server error. Please try again later.'
          });
        default:
          return Promise.reject(error);
      }
    }
  );

  return instance;
};

// Create instances for each microservice
export const authApi = createInstance(config.AUTH_API_URL, 'AUTH');
export const ragApi = createInstance(config.RAG_API_URL, 'RAG');
export const emailApi = createInstance(config.EMAIL_API_URL, 'EMAIL');
export const paymentApi = createInstance(config.PAYMENT_API_URL, 'PAYMENT');

// Helper function to handle API responses
export const handleResponse = async (promise) => {
  try {
    const response = await promise;
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.error || error.response?.data?.detail || error.message || 'An error occurred'
    };
  }
};

// For backward compatibility
export default authApi;