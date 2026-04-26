// utils/trackRateLimit.js

const WINDOW_MS = 60_000;
const MAX_IN_WINDOW = 72;
const MIN_SAME_BOOK_MS = 1800;

const windowStarts = [];
const lastByBook = new Map();

export function allowClientTrack(bookId) {
  const now = Date.now();
  const id = String(bookId);

  // prevent spam on same book
  if (now - (lastByBook.get(id) || 0) < MIN_SAME_BOOK_MS) {
    return false;
  }

  // sliding window cleanup
  while (windowStarts.length && now - windowStarts[0] > WINDOW_MS) {
    windowStarts.shift();
  }

  if (windowStarts.length >= MAX_IN_WINDOW) {
    return false;
  }

  windowStarts.push(now);
  lastByBook.set(id, now);

  return true;
}