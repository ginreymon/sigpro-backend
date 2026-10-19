import logging

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from core.request_log import ApiRequestLogMiddleware


class FakeUser:
    pk = 7
    is_authenticated = True

    def get_username(self):
        return "operator"


class ApiRequestLogMiddlewareTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _call(self, path, status=200, user=None):
        request = self.factory.get(path, {"limit": "20"})
        request.user = user or AnonymousUser()
        middleware = ApiRequestLogMiddleware(lambda req: HttpResponse("ok", status=status))
        return middleware(request)

    def test_logs_info_with_user_and_query(self):
        with self.assertLogs("api.request", level="INFO") as logs:
            self._call("/api/v1/production/orders/", user=FakeUser())

        self.assertEqual(logs.records[0].levelno, logging.INFO)
        message = logs.records[0].getMessage()
        self.assertIn("GET /api/v1/production/orders/?limit=20", message)
        self.assertIn("status=200", message)
        self.assertIn("user=7:operator", message)

    def test_anonymous_user_label(self):
        with self.assertLogs("api.request", level="INFO") as logs:
            self._call("/api/v1/auth/token/")
        self.assertIn("user=anonymous", logs.records[0].getMessage())

    def test_level_follows_status(self):
        with self.assertLogs("api.request", level="INFO") as logs:
            self._call("/api/v1/x/", status=404)
            self._call("/api/v1/x/", status=500)
        self.assertEqual([r.levelno for r in logs.records], [logging.WARNING, logging.ERROR])

    def test_paths_outside_api_are_ignored(self):
        with self.assertNoLogs("api.request", level="INFO"):
            self._call("/admin/login/")

    @override_settings(API_REQUEST_LOG_EXCLUDED_PATHS=("/api/v1/auth/refresh/",))
    def test_excluded_paths_are_ignored(self):
        with self.assertNoLogs("api.request", level="INFO"):
            self._call("/api/v1/auth/refresh/")

    def test_unhandled_exception_is_logged(self):
        request = self.factory.get("/api/v1/x/")
        request.user = AnonymousUser()
        middleware = ApiRequestLogMiddleware(lambda req: HttpResponse())
        with self.assertLogs("api.request", level="ERROR") as logs:
            middleware.process_exception(request, ValueError("boom"))
        self.assertIn("unhandled exception", logs.records[0].getMessage())
