// src/config/index.js
const config = {
  AUTH_API_URL: import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8000',
  RAG_API_URL: import.meta.env.VITE_RAG_API_URL || 'http://localhost:8001',
  // Keep API_URL for backward compatibility if needed, but we should move away from it
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
};

export default config;

