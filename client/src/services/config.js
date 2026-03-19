// src/services/config.js - Configuration service with all environment variables
const config = {
  // API URLs
  AUTH_API_URL: import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8000',
  RAG_API_URL: import.meta.env.VITE_RAG_API_URL || 'http://localhost:8001',
  EMAIL_API_URL: import.meta.env.VITE_EMAIL_API_URL || 'http://localhost:8002',
  PAYMENT_API_URL: import.meta.env.VITE_PAYMENT_API_URL || 'http://localhost:8003',
  
  // Environment
  ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT || 'development',
  
  // Feature flags
  ENABLE_MOCK_PAYMENTS: import.meta.env.VITE_ENABLE_MOCK_PAYMENTS === 'true' || false,
  ENABLE_DEBUG_LOGS: import.meta.env.VITE_ENABLE_DEBUG_LOGS === 'true' || false,
  
  // App settings
  APP_NAME: 'LitScholar',
  APP_VERSION: '1.0.0',
  
  // Pagination defaults
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // Cache durations (in milliseconds)
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
  
  // Toast durations
  TOAST_DURATION: 2500,
};

// Validate required config
const requiredVars = ['AUTH_API_URL', 'RAG_API_URL'];
requiredVars.forEach(varName => {
  if (!config[varName]) {
    console.error(`❌ Missing required config: ${varName}`);
  }
});

if (config.ENABLE_DEBUG_LOGS) {
  console.log('📋 Config loaded:', config);
}

export default config;