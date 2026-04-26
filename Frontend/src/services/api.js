import axios from 'axios';
import config from './config';

// ===== Token (in-memory) =====
let memoryAccessToken = null;

export const setMemoryAccessToken = (token) => {
  memoryAccessToken = token || null;
};

export const getMemoryAccessToken = () => memoryAccessToken;


// ===== Axios Factory =====
const createInstance = (baseURL, serviceName = '', { useBearer = false } = {}) => {
  const instance = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
  });

  // ===== Request Interceptor =====
  instance.interceptors.request.use(
    (req) => {
      if (useBearer && memoryAccessToken) {
        req.headers.Authorization = `Bearer ${memoryAccessToken}`;
      }

      if (import.meta.env.DEV) {
        console.log(`🚀 [${serviceName}] ${req.method?.toUpperCase()} ${req.url}`);
      }

      return req;
    },
    (error) => Promise.reject(error)
  );

  // ===== Response Interceptor =====
  instance.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config;

      const isAuthRoute = original.url?.includes('/auth/');

      // 🔄 Auto refresh token
      if (error.response?.status === 401 && !original._retry && !isAuthRoute) {
        original._retry = true;

        try {
          if (import.meta.env.DEV) {
            console.log(`🔄 [${serviceName}] Refreshing token...`);
          }

          const res = await axios.post(
            `${config.USER_API_URL}/auth/refresh`,
            {},
            { withCredentials: true }
          );

          const newToken = res.data?.access_token;

          if (newToken) {
            setMemoryAccessToken(newToken);

            if (useBearer) {
              original.headers.Authorization = `Bearer ${newToken}`;
            }

            return instance(original);
          }

        } catch (err) {
          console.error('❌ Token refresh failed:', err);
          setMemoryAccessToken(null);

          if (!['/'].includes(window.location.pathname)) {
            window.location.href = '/';
          }

          return Promise.reject(err);
        }
      }

      // ===== Error Formatting =====
      let message = 'Unknown Error';

      if (error.response) {
        switch (error.response.status) {
          case 400: message = error.response.data?.detail || 'Validation Error'; break;
          case 403: message = 'Access Denied'; break;
          case 404: message = 'Resource Not Found'; break;
          case 429: message = 'Rate limit exceeded'; break;
          case 500: message = 'Server error'; break;
          default: message = error.response.data?.detail || message;
        }
      } else {
        message = 'Network error (service down)';
      }

      return Promise.reject({
        success: false,
        status: error.response?.status,
        error: message
      });
    }
  );

  return instance;
};


// ===== Service Instances =====
export const userApi = createInstance(config.USER_API_URL, 'USER', { useBearer: false });

export const aiApi = createInstance(config.AI_API_URL, 'AI', { useBearer: true });


// ===== Helper =====
export const handleResponse = async (promise) => {
  try {
    const res = await promise;
    return { success: true, data: res.data };
  } catch (err) {
    return {
      success: false,
      error: err.error || 'Unexpected error'
    };
  }
};


export default userApi;