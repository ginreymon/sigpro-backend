"""
Standard error envelope of the API.

Every 4xx/5xx JSON response under /api/v1/ has this shape:

    {
      "detail": "Human readable message (first error when there are several).",
      "code":   "machine_readable_code",       # e.g. validation_error, not_found
      "errors": {"<field>": ["message", ...]}   # {} when there are no field errors;
                                                # non-field messages go in "non_field_errors"
    }

Roll-back switch: with API_ERRORS_LEGACY_MIRROR=True (default False) the keys of
the previous shapes ("error", "message", form field names, "details", ...) are also
copied next to the envelope, for clients that were not migrated yet.

Two places produce the envelope: `api_exception_handler` (every exception DRF
handles) and `ApiErrorEnvelopeMiddleware` (manual `Response(..., status=4xx)`
that were written before the standard existed).
"""
import json

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler

ENVELOPE_KEYS = ("detail", "code", "errors")
NON_FIELD_ERRORS = "non_field_errors"

# Keys of legacy bodies that carry the message rather than a field error.
_MESSAGE_KEYS = ("detail", "error", "message")

_STATUS_CODES = {
    400: "bad_request",
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    415: "unsupported_media_type",
    429: "throttled",
    500: "server_error",
    502: "bad_gateway",
    503: "service_unavailable",
}

_DEFAULT_DETAIL = {
    400: "Solicitud inválida.",
    401: "No autenticado.",
    403: "No tiene permiso para realizar esta acción.",
    404: "No encontrado.",
    405: "Método no permitido.",
}


def _clean(value):
    """ErrorDetail/lazy strings -> str, keeping lists and dicts as they are."""
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _as_field_errors(value):
    """A message or a list/dict of messages -> list/dict (never a bare string)."""
    cleaned = _clean(value)
    return cleaned if isinstance(cleaned, (list, dict)) else [cleaned]


def _first_message(errors):
    """First message found in an errors structure, or None."""
    if isinstance(errors, str):
        return errors
    if isinstance(errors, dict):
        errors = list(errors.values())
    if isinstance(errors, (list, tuple)):
        for item in errors:
            message = _first_message(item)
            if message:
                return message
    return None


def _legacy_mirror_enabled() -> bool:
    return getattr(settings, "API_ERRORS_LEGACY_MIRROR", False)


def is_standard_error_body(data) -> bool:
    return isinstance(data, dict) and all(key in data for key in ENVELOPE_KEYS)


def build_error_body(data, status_code: int, code: str | None = None):
    """
    Turns any error payload (DRF validation dict/list, {"error": ...}, {"detail": ...},
    a bare string, ...) into the standard envelope. Idempotent: a payload that is
    already standard is returned untouched (same object).
    """
    if is_standard_error_body(data):
        return data

    legacy = {}

    if isinstance(data, dict):
        detail = next((str(data[key]) for key in _MESSAGE_KEYS if isinstance(data.get(key), str)), None)

        # DRF/SimpleJWT style {"detail": ..., "code": "token_not_valid", "messages": [...]}:
        # keeps its own code and has no field errors.
        own_code = isinstance(data.get("code"), str) and detail is not None

        if isinstance(data.get("errors"), dict):
            errors = _clean(data["errors"])
        elif own_code:
            errors = {}
        else:
            errors = {
                key: _as_field_errors(value)
                for key, value in data.items()
                if key not in _MESSAGE_KEYS and key != "errors"
                and isinstance(value, (str, list, tuple, dict))
            }

        if code is None and own_code:
            code = data["code"]

        if _legacy_mirror_enabled():
            legacy = {
                key: _clean(value) for key, value in data.items()
                if key not in ENVELOPE_KEYS
            }
    elif isinstance(data, (list, tuple)):
        messages = _clean(data)
        errors = {NON_FIELD_ERRORS: messages}
        detail = _first_message(messages)
    else:
        detail = str(data) if data not in (None, "") else None
        errors = {}

    if detail is None:
        detail = _first_message(errors) or _DEFAULT_DETAIL.get(status_code, "Ocurrió un error.")

    if code is None:
        code = "validation_error" if (status_code == 400 and errors) else _STATUS_CODES.get(status_code, "error")

    return {"detail": detail, "code": code, "errors": errors, **legacy}


def error_response(detail, *, status_code: int = 400, code: str | None = None, errors=None, legacy=None, extra=None):
    """
    Builds a standard error Response for a manual error (instead of Response({"error": ...})).

    `legacy`: keys of the previous body (e.g. {"error": detail}) that are mirrored
    next to the envelope while API_ERRORS_LEGACY_MIRROR is on. Nothing new should
    depend on them.

    `extra`: domain data that always travels with the error (e.g. the SIESA result
    of a rejected TEP), next to the envelope.
    """
    from rest_framework.response import Response

    body = build_error_body(
        {"detail": detail, "errors": errors or {}}, status_code, code=code,
    )
    if legacy and _legacy_mirror_enabled():
        body = {**{key: _clean(value) for key, value in legacy.items() if key not in ENVELOPE_KEYS}, **body}
    if extra:
        body = {**body, **{key: _clean(value) for key, value in extra.items() if key not in ENVELOPE_KEYS}}
    return Response(body, status=status_code)


def api_exception_handler(exc, context):
    """DRF EXCEPTION_HANDLER: DRF's own handling, with the body in the standard envelope.
    Unhandled exceptions (server errors) are left to Django (returns None)."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        code = "validation_error"
    else:
        codes = exc.get_codes() if hasattr(exc, "get_codes") else None
        code = codes if isinstance(codes, str) else None

    response.data = build_error_body(response.data, response.status_code, code=code)
    return response


class ApiErrorEnvelopeMiddleware:
    """Puts the envelope on error responses that did not come from the exception
    handler (manual Response(..., status=4xx/5xx)). Only touches JSON error
    responses under /api/v1/."""

    API_PREFIX = "/api/v1/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            response.status_code >= 400
            and request.path.startswith(self.API_PREFIX)
            and "application/json" in response.get("Content-Type", "")
        ):
            try:
                data = json.loads(response.content)
            except ValueError:
                return response

            body = build_error_body(data, response.status_code)
            if body is not data:
                response.content = json.dumps(body, ensure_ascii=False).encode("utf-8")
                if response.has_header("Content-Length"):
                    response["Content-Length"] = str(len(response.content))

        return response


def _is_api_request(request) -> bool:
    return request.path.startswith("/api/")


def api_not_found(request, exception=None):
    """handler404: JSON envelope for unknown /api/ URLs, Django's page otherwise."""
    if _is_api_request(request):
        return JsonResponse(build_error_body({}, 404), status=404)

    from django.views.defaults import page_not_found
    return page_not_found(request, exception)


def api_server_error(request):
    """handler500: JSON envelope for /api/ URLs (no internals leaked), Django's page otherwise."""
    if _is_api_request(request):
        return JsonResponse(
            build_error_body({"detail": "Error interno del servidor."}, 500), status=500
        )

    from django.views.defaults import server_error
    return server_error(request)