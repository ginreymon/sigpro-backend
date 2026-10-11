from rest_framework.response import Response

from apps.production.services.exceptions import SessionRuleError
from core.exceptions import build_error_body


class SessionRuleErrorMixin:
    """Answers a SessionRuleError raised by a service with the standard error
    envelope (and the legacy keys while they are mirrored)."""

    def handle_exception(self, exc):
        if isinstance(exc, SessionRuleError):
            return Response(
                build_error_body(exc.payload, exc.status_code, code=exc.code),
                status=exc.status_code,
            )
        return super().handle_exception(exc)