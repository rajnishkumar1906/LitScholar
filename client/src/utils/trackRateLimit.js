const WINDOW_MS = 60_000;
const MAX_IN_WINDOW = 72;
const MIN_SAME_BOOK_MS = 1800;

const windowStarts = [];
const lastByBook = new Map();

export function allowClientTrack(bookId) {
  const now = Date.now();
  const bid = String(bookId);

  const lastSame = lastByBook.get(bid) || 0;
  if (now - lastSame < MIN_SAME_BOOK_MS) {
    return false;
  }

  while (windowStarts.length && now - windowStarts[0] > WINDOW_MS) {
    windowStarts.shift();
  }
  if (windowStarts.length >= MAX_IN_WINDOW) {
    return false;
  }

  windowStarts.push(now);
  lastByBook.set(bid, now);
  return true;
}
