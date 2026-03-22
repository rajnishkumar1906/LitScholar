import axios from 'axios';
import config from './config';
import { tokenCookies } from '../utils/cookies';

// Standardized Instance Creator
const createInstance = (baseURL, serviceName = '') => {
  const instance = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
  });

  // 🛰️ REQUEST LOGGING
  instance.interceptors.request.use(
    (config) => {
      if (import.meta.env.DEV) {
        console.log(`🚀 [${serviceName}] ${config.method?.toUpperCase()} ${config.url}`);
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // 🔄 RESPONSE INTERCEPTOR (The Microservice Glue)
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      // Prevent infinite loops on auth endpoints
      const isAuthEndpoint = originalRequest.url?.includes('/auth/') || 
                             originalRequest.url?.includes('/users/me');

      // 1. Handle 401 Unauthorized (Token Expiry)
      if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
        originalRequest._retry = true;
        
        try {
          if (import.meta.env.DEV) console.log(`🔄 [${serviceName}] Refreshing tokens via AUTH service...`);
          
          // Always hit the AUTH service regardless of which service triggered the 401
          await axios.post(`${config.AUTH_API_URL}/auth/refresh`, {}, {
            withCredentials: true,
            timeout: 10000
          });

          // Retry the original request with the new cookie
          return instance(originalRequest);
        } catch (refreshError) {
          tokenCookies.clear();
          // Force a clean state on failure
          if (!['/', '/pricing'].includes(window.location.pathname)) {
            window.location.href = '/';
          }
          return Promise.reject(refreshError);
        }
      }

      // 2. Standardized Error Mapping
      const errorPayload = {
        success: false,
        status: error.response?.status,
        error: error.response?.data?.detail || error.message || 'Unknown Error'
      };

      // Handle specific status codes
      if (error.response) {
        switch (error.response.status) {
          case 400: errorPayload.error = error.response.data?.detail || 'Validation Error'; break;
          case 403: errorPayload.error = 'Access Denied'; break;
          case 404: errorPayload.error = 'Resource Not Found'; break;
          case 429: errorPayload.error = 'Rate limit exceeded. Slow down!'; break;
          case 500: errorPayload.error = 'Internal Server Error (Microservice failure)'; break;
        }
      } else {
        errorPayload.error = 'Network error. Service might be down.';
      }

      return Promise.reject(errorPayload);
    }
  );

  return instance;
};

// --- Service Instances ---
export const authApi = createInstance(config.AUTH_API_URL, 'AUTH');
export const ragApi = createInstance(config.RAG_API_URL, 'RAG');
export const emailApi = createInstance(config.EMAIL_API_URL, 'EMAIL');
export const paymentApi = createInstance(config.PAYMENT_API_URL, 'PAYMENT');

// --- Response Helper ---
export const handleResponse = async (promise) => {
  try {
    const response = await promise;
    return { success: true, data: response.data };
  } catch (error) {
    // Note: error here is now our formatted errorPayload from the interceptor
    return { 
      success: false, 
      error: error.error || 'An unexpected error occurred'
    };
  }
};

export default authApi;