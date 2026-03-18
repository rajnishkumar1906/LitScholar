// src/services/config.js - Configuration service
const config = {
  AUTH_API_URL: import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8000',
  RAG_API_URL: import.meta.env.VITE_RAG_API_URL || 'http://localhost:8001',
  EMAIL_API_URL: import.meta.env.VITE_EMAIL_API_URL || 'http://localhost:8002',
  PAYMENT_API_URL: import.meta.env.VITE_PAYMENT_API_URL || 'http://localhost:8003',
};

export default config;
