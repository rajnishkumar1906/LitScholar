import axios from 'axios';
import config from './config';

let memoryAccessToken = null;
export const setMemoryAccessToken = (token) => {
  memoryAccessToken = token || null;
};
export const getMemoryAccessToken = () => memoryAccessToken;

const createInstance = (baseURL, serviceName = '', options = {}) => {
  const { useMemoryBearer = false } = options;
  const instance = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
  });

  instance.interceptors.request.use(
    (reqConfig) => {
      if (useMemoryBearer && memoryAccessToken) {
        reqConfig.headers.Authorization = `Bearer ${memoryAccessToken}`;
      }

      if (import.meta.env.DEV) {
        console.log(`🚀 [${serviceName}] ${reqConfig.method?.toUpperCase()} ${reqConfig.url}`);
      }
      return reqConfig;
    },
    (error) => Promise.reject(error)
  );

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      const isAuthEndpoint = originalRequest.url?.includes('/auth/');

      if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
        originalRequest._retry = true;
        
        try {
          if (import.meta.env.DEV) console.log(`🔄 [${serviceName}] Refreshing token...`);
          
          const response = await axios.post(`${config.AUTH_API_URL}/auth/refresh`, {}, {
            withCredentials: true
          });
          
          if (response.data.access_token) {
            setMemoryAccessToken(response.data.access_token);
            if (useMemoryBearer) {
              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
            }
            return instance(originalRequest);
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          setMemoryAccessToken(null);

          if (!['/'].includes(window.location.pathname)) {
            window.location.href = '/';
          }
          return Promise.reject(refreshError);
        }
      }

      const errorPayload = {
        success: false,
        status: error.response?.status,
        error: error.response?.data?.detail || error.message || 'Unknown Error'
      };

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
export const authApi = createInstance(config.AUTH_API_URL, 'AUTH', { useMemoryBearer: false });
export const ragApi = createInstance(config.RAG_API_URL, 'RAG', { useMemoryBearer: true });

// --- Response Helper ---
export const handleResponse = async (promise) => {
  try {
    const response = await promise;
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.error || 'An unexpected error occurred'
    };
  }
};

export default authApi;
