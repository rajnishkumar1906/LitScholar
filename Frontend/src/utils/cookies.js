// utils/cookies.js

const REFRESH_TOKEN_KEY = 'refresh_token';

const options = {
  path: '/',
  sameSite: 'Lax',
};

function setCookie(name, value, maxAge) {
  let cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;
  cookie += `; path=${options.path}`;
  cookie += `; max-age=${maxAge}`;
  cookie += `; SameSite=${options.sameSite}`;

  if (import.meta.env.PROD && window.location?.protocol === 'https:') {
    cookie += '; Secure';
  }

  document.cookie = cookie;
}

function getCookie(name) {
  return document.cookie
    .split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(`${name}=`))
    ?.split('=')[1] || null;
}

function deleteCookie(name) {
  document.cookie = `${name}=; path=${options.path}; max-age=0`;
}

// 7 days
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60;

export const tokenCookies = {
  getRefreshToken: () => getCookie(REFRESH_TOKEN_KEY),

  setRefreshToken: (token) =>
    setCookie(REFRESH_TOKEN_KEY, token, REFRESH_MAX_AGE),

  clear: () => deleteCookie(REFRESH_TOKEN_KEY),
};