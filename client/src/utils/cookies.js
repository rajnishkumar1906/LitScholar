// Cookie helpers for storing auth tokens (instead of localStorage)

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

const defaultOptions = {
  path: '/',
  sameSite: 'Lax',
};

function setCookie(name, value, maxAgeSeconds) {
  let cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;
  cookie += `; path=${defaultOptions.path}`;
  cookie += `; max-age=${maxAgeSeconds}`;
  cookie += `; SameSite=${defaultOptions.sameSite}`;
  if (import.meta.env.PROD && window.location?.protocol === 'https:') {
    cookie += '; Secure';
  }
  document.cookie = cookie;
}

function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (const c of cookies) {
    const eq = c.trim().indexOf('=');
    if (eq === -1) continue;
    const k = decodeURIComponent(c.trim().slice(0, eq).trim());
    const v = c.trim().slice(eq + 1).trim();
    if (k === name && v) {
      return decodeURIComponent(v);
    }
  }
  return null;
}

function deleteCookie(name) {
  document.cookie = `${encodeURIComponent(name)}=; path=${defaultOptions.path}; max-age=0`;
}

// Access token: ~1 hour (match backend ACCESS_TOKEN_EXPIRE_MINUTES)
const ACCESS_MAX_AGE = 60 * 60;
// Refresh token: 7 days
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60;

export const tokenCookies = {
  getAccessToken: () => getCookie(ACCESS_TOKEN_KEY),
  getRefreshToken: () => getCookie(REFRESH_TOKEN_KEY),
  setAccessToken: (token) => setCookie(ACCESS_TOKEN_KEY, token, ACCESS_MAX_AGE),
  setRefreshToken: (token) => setCookie(REFRESH_TOKEN_KEY, token, REFRESH_MAX_AGE),
  setTokens: (accessToken, refreshToken) => {
    setCookie(ACCESS_TOKEN_KEY, accessToken, ACCESS_MAX_AGE);
    setCookie(REFRESH_TOKEN_KEY, refreshToken, REFRESH_MAX_AGE);
  },
  clear: () => {
    deleteCookie(ACCESS_TOKEN_KEY);
    deleteCookie(REFRESH_TOKEN_KEY);
  },
  hasAccessToken: () => !!getCookie(ACCESS_TOKEN_KEY),
};