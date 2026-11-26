"""In-memory, thread-safe store of runtime observations (requests, errors, activity).

shortcut: per-process memory. IIS may run several workers and a recycle resets it;
move to a DB table if history or cross-worker accuracy is needed.
"""
import threading
import time
from collections import deque
from urllib.parse import urlsplit

STARTED_AT = time.time()
ACTIVE_WINDOW_SECONDS = 300
MAX_REQUESTS = 2000
MAX_USERS = 500

_lock = threading.Lock()
_requests = deque(maxlen=MAX_REQUESTS)  # (ts, method, route, status, ms)
_errors = deque(maxlen=100)  # server errors: ts, method, route, status, exception
_client_errors = deque(maxlen=100)
_last_seen = {}  # user_id -> (ts, username)
_siesa = {}  # last known SIESA result: ok, ts, source


def record_request(method, route, status, duration_ms, user_id=None, username=None, exception=None):
    now = time.time()
    with _lock:
        _requests.append((now, method, route, status, duration_ms))
        if status >= 500:
            _errors.append({"ts": now, "method": method, "route": route, "status": status, "exception": exception})
        if user_id is not None:
            if user_id not in _last_seen and len(_last_seen) >= MAX_USERS:
                oldest = min(_last_seen, key=lambda k: _last_seen[k][0])
                del _last_seen[oldest]
            _last_seen[user_id] = (now, username)


def record_client_error(user_id, message, url, stack):
    with _lock:
        _client_errors.append({
            "ts": time.time(),
            "user_id": user_id,
            "message": message,
            "path": urlsplit(url or "").path,  # query strings may carry tokens/ids
            "stack": stack,
        })


def record_siesa(ok, source):
    with _lock:
        _siesa.update(ok=ok, ts=time.time(), source=source)


def snapshot():
    """Consistent copy of everything the services need to aggregate."""
    now = time.time()
    with _lock:
        return {
            "requests": list(_requests),
            "errors": list(_errors),
            "client_errors": list(_client_errors),
            "active_users": [
                {"user_id": uid, "username": name, "ts": ts}
                for uid, (ts, name) in _last_seen.items()
                if now - ts <= ACTIVE_WINDOW_SECONDS
            ],
            "siesa": dict(_siesa),
        }
