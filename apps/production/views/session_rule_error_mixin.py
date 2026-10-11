from rest_framework.response import Response

from apps.production.services.exceptions import SessionRuleError


class SessionRuleErrorMixin:
    """Answers a SessionRuleError raised by a service with the payload and status
    it carries (the same responses the views used to build by hand)."""

    def handle_exception(self, exc):
        if isinstance(exc, SessionRuleError):
            return Response(exc.payload, status=exc.status_code)
        return super().handle_exception(exc)
