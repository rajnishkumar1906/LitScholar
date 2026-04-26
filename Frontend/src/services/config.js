// src/services/config.js

const config = {
  // API URLs
  USER_API_URL: import.meta.env.VITE_USER_API_URL || 'http://localhost:8000',
  AI_API_URL: import.meta.env.VITE_AI_API_URL || 'http://localhost:8001',

  // Environment
  ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT || 'development',

  // Debug
  ENABLE_DEBUG_LOGS: import.meta.env.VITE_ENABLE_DEBUG_LOGS === 'true',

  // App
  APP_NAME: 'LitScholar',
  APP_VERSION: '1.0.0',

  // Pagination
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,

  // Cache (ms)
  CACHE_DURATION: 5 * 60 * 1000,

  // UI
  TOAST_DURATION: 2500,
};


// Validate required config
['USER_API_URL', 'AI_API_URL'].forEach(key => {
  if (!config[key]) {
    console.error(`❌ Missing config: ${key}`);
  }
});


// Debug log
if (config.ENABLE_DEBUG_LOGS) {
  console.log('📋 Config:', config);
}

export default config;