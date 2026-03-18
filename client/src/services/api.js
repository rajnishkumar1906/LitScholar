// src/services/api.js - API clients for microservices
import axios from 'axios';
import config from './config';

const createInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Response interceptor for token refresh
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          // Always refresh using the Auth service
          // withCredentials: true ensures the refresh_token cookie is sent
          await axios.post(`${config.AUTH_API_URL}/auth/refresh`, {}, {
            withCredentials: true
          });
          
          return instance(originalRequest);
        } catch (refreshError) {
          // If refresh fails, we can't do much here. 
          // AppContext usually handles redirecting to login.
        }
      }
      
      return Promise.reject(error);
    }
  );

  return instance;
};

export const authApi = createInstance(config.AUTH_API_URL);
export const ragApi = createInstance(config.RAG_API_URL);
export const emailApi = createInstance(config.EMAIL_API_URL);
export const paymentApi = createInstance(config.PAYMENT_API_URL);

// For backward compatibility, default export authApi
export default authApi;
