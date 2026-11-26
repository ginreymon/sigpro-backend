"""Aggregations and probes behind the monitoring endpoints. No probe here runs
SQL/network work per call without a TTL cache or an explicit request."""
import math
import socket
import threading
import time

import psutil
import requests
from django.conf import settings
from django.db import connection

from . import metrics_store as store

CLIENT_ERROR_WINDOW_SECONDS = 900
MIN_REQUESTS_FOR_API_STATUS = 10
DB_SLOW_MS = 500
API_P95_WARN_MS = 2000
API_P95_DOWN_MS = 5000

_cache = {}
_cache_locks = {}
_cache_locks_guard = threading.Lock()
psutil.cpu_percent(interval=None)  # prime: the first call always returns 0.0


def _cached(key, ttl, producer):
    # One probe at a time per key: during a DB outage concurrent polls wait for the
    # first probe's result instead of each blocking on its own connect timeout.
    with _cache_locks_guard:
        lock = _cache_locks.setdefault(key, threading.Lock())
    with lock:
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < ttl:
            return hit[1]
        value = producer()
        _cache[key] = (time.monotonic(), value)
        return value


def _percentile(sorted_values, pct):
    return sorted_values[min(len(sorted_values) - 1, math.ceil(pct / 100 * len(sorted_values)) - 1)]


def api_stats(requests_log):
    """Availability (share of non-5xx responses) and latency over the in-memory window."""
    total = len(requests_log)
    if not total:
        return {"total": 0, "availability": None, "p50_ms": None, "p95_ms": None, "since": None}
    durations = sorted(r[4] for r in requests_log)
    errors = sum(1 for r in requests_log if r[3] >= 500)
    return {
        "total": total,
        "availability": round(100 * (total - errors) / total, 2),
        "p50_ms": round(_percentile(durations, 50), 1),
        "p95_ms": round(_percentile(durations, 95), 1),
        "since": requests_log[0][0],
    }


def endpoint_stats(requests_log, limit=10):
    groups = {}
    for _, method, route, status, ms in requests_log:
        groups.setdefault((method, route), []).append((ms, status))
    rows = []
    for (method, route), items in groups.items():
        durations = sorted(ms for ms, _ in items)
        rows.append({
            "method": method,
            "route": route,
            "count": len(items),
            "avg_ms": round(sum(durations) / len(durations), 1),
            "p95_ms": round(_percentile(durations, 95), 1),
            "errors": sum(1 for _, s in items if s >= 500),
        })
    rows.sort(key=lambda r: r["p95_ms"], reverse=True)
    return rows[:limit]


def database_ping():
    def probe():
        started = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # any driver failure means the DB is unreachable
            return {"ok": False, "latency_ms": None}
        return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000, 1)}

    return _cached("db_ping", 15, probe)


def database_metrics():
    """Size and open sessions. Sessions need VIEW SERVER STATE; None when not granted."""
    def probe():
        out = {"size_mb": None, "user_sessions": None}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SUM(size) * 8 / 1024 FROM sys.database_files")
                row = cursor.fetchone()
                out["size_mb"] = int(row[0]) if row and row[0] is not None else None
        except Exception:
            pass
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE is_user_process = 1")
                out["user_sessions"] = cursor.fetchone()[0]
        except Exception:
            pass
        return out

    return _cached("db_metrics", 60, probe)


def host_metrics():
    def probe():
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(settings.BASE_DIR.anchor or str(settings.BASE_DIR))
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used // 1048576,
            "memory_total_mb": memory.total // 1048576,
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / 1073741824, 1),
        }

    return _cached("host", 30, probe)


def check_siesa():
    """Reachability of the WSDL endpoint (GET, no credentials, no document sent)."""
    url = getattr(settings, "SIESA_WSUNOEE_WSDL_URL", "")
    if not url:
        return {"status": "unknown", "detail": "SIESA no configurado"}

    def probe():
        started = time.perf_counter()
        try:
            ok = requests.get(url, timeout=5).status_code < 400
        except requests.RequestException:
            ok = False
        store.record_siesa(ok, "check")
        return {"status": "ok" if ok else "down", "latency_ms": round((time.perf_counter() - started) * 1000, 1)}

    return _cached("siesa_check", 10, probe)  # repeated clicks reuse the last probe


def _siesa_status(siesa):
    if not siesa:
        return {"status": "unknown"}
    return {"status": "ok" if siesa["ok"] else "down", "last_checked": siesa["ts"], "source": siesa["source"]}


def _api_status(stats):
    if stats["total"] < MIN_REQUESTS_FOR_API_STATUS:
        return "unknown"
    if stats["availability"] < 95 or stats["p95_ms"] > API_P95_DOWN_MS:
        return "down"
    if stats["availability"] < 99 or stats["p95_ms"] > API_P95_WARN_MS:
        return "warn"
    return "ok"


def _frontend_status(client_errors):
    now = time.time()
    recent = sum(1 for e in client_errors if now - e["ts"] <= CLIENT_ERROR_WINDOW_SECONDS)
    return {"status": "ok" if not recent else "warn" if recent < 5 else "down", "errors_last_15min": recent}


def build_summary():
    snap = store.snapshot()
    stats = api_stats(snap["requests"])
    db = database_ping()
    db_status = "down" if not db["ok"] else "warn" if db["latency_ms"] >= DB_SLOW_MS else "ok"
    services = {
        "backend": {"status": "ok", "uptime_seconds": int(time.time() - store.STARTED_AT)},
        "database": {"status": db_status, "latency_ms": db["latency_ms"]},
        "api": {"status": _api_status(stats), **stats},
        "frontend": _frontend_status(snap["client_errors"]),
        "siesa": _siesa_status(snap["siesa"]),
    }
    rank = {"ok": 0, "unknown": 0, "warn": 1, "down": 2}
    labels = {"backend": "Backend", "database": "Base de datos", "api": "API", "frontend": "Frontend", "siesa": "SIESA"}
    return {
        "overall": max((s["status"] for s in services.values()), key=rank.get),
        "environment": "development" if settings.DEBUG else "production",
        "server_time": time.time(),
        "services": services,
        "active_users": len(snap["active_users"]),
        "recent_errors": [
            {k: e[k] for k in ("ts", "method", "route", "status")} for e in reversed(snap["errors"][-5:])
        ],
        "alerts": [
            {"level": s["status"], "message": f"{labels[name]}: {'caído' if s['status'] == 'down' else 'degradado'}"}
            for name, s in services.items() if s["status"] in ("warn", "down")
        ],
    }


def build_diagnostics():
    snap = store.snapshot()
    return {
        "hostname": socket.gethostname(),
        "host": host_metrics(),
        "database": database_metrics(),
        "slow_endpoints": endpoint_stats(snap["requests"]),
        "server_errors": list(reversed(snap["errors"][-20:])),
        "client_errors": list(reversed(snap["client_errors"][-20:])),
        "active_users": sorted(snap["active_users"], key=lambda u: u["ts"], reverse=True),
    }
