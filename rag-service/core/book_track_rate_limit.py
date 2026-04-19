"""In-memory rate limiting for POST /books/track (per user + per book debounce)."""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException

_lock = Lock()
_timeline: dict[int, deque] = defaultdict(deque)
_last_pair: dict[tuple[int, str], float] = {}

WINDOW_SEC = 60
MAX_TRACKS_PER_WINDOW = 72
MIN_SAME_BOOK_SEC = 1.8
_PAIR_PRUNE_INTERVAL = 5000


def check_book_track_rate_limit(user_id: int, book_id: str) -> None:
    now = time.time()
    uid = int(user_id)
    bid = str(book_id)

    with _lock:
        pair_key = (uid, bid)
        last_same = _last_pair.get(pair_key, 0.0)
        if now - last_same < MIN_SAME_BOOK_SEC:
            raise HTTPException(
                status_code=429,
                detail="Too many requests for this book. Please wait a moment.",
            )

        q = _timeline[uid]
        while q and now - q[0] > WINDOW_SEC:
            q.popleft()
        if len(q) >= MAX_TRACKS_PER_WINDOW:
            raise HTTPException(
                status_code=429,
                detail="Too many book views. Please slow down and try again in a minute.",
            )

        q.append(now)
        _last_pair[pair_key] = now

        if len(_last_pair) > _PAIR_PRUNE_INTERVAL:
            cutoff = now - WINDOW_SEC * 2
            dead = [k for k, t in _last_pair.items() if t < cutoff]
            for k in dead[: _PAIR_PRUNE_INTERVAL // 2]:
                del _last_pair[k]
