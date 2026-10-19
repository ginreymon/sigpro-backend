import logging
import time

from django.conf import settings

logger = logging.getLogger("api.request")


class ApiRequestLogMiddleware:
    """Logs one line per request under /api/v1/: method, path, query, status,
    duration, user, client IP and response size. Bodies are never logged
    (login/token endpoints carry credentials). Paths listed in
    API_REQUEST_LOG_EXCLUDED_PATHS are skipped."""

    API_PREFIX = "/api/v1/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_log(request.path):
            return self.get_response(request)

        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000

        logger.log(
            self._level_for(response.status_code),
            "%s %s%s status=%s duration_ms=%.1f user=%s ip=%s bytes=%s",
            request.method,
            request.path,
            f"?{request.META['QUERY_STRING']}" if request.META.get("QUERY_STRING") else "",
            response.status_code,
            duration_ms,
            self._user_label(request),
            self._client_ip(request),
            len(response.content) if not response.streaming else "-",
        )
        return response

    def process_exception(self, request, exception):
        if self._should_log(request.path):
            logger.error(
                "%s %s unhandled exception user=%s",
                request.method,
                request.path,
                self._user_label(request),
                exc_info=exception,
            )

    def _should_log(self, path):
        excluded = getattr(settings, "API_REQUEST_LOG_EXCLUDED_PATHS", ())
        return path.startswith(self.API_PREFIX) and path not in excluded

    @staticmethod
    def _level_for(status_code):
        if status_code >= 500:
            return logging.ERROR
        if status_code >= 400:
            return logging.WARNING
        return logging.INFO

    @staticmethod
    def _user_label(request):
        # DRF resolves the JWT inside the view and copies the user to the Django request.
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            return f"{user.pk}:{user.get_username()}"
        return "anonymous"

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "-")
