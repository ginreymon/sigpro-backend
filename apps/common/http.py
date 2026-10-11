from rest_framework import status
from rest_framework.response import Response

from core.exceptions import error_response


def missing_params_response(params, *names, message=None):
    """Return a 400 response if any of the named params is missing or empty, else None."""
    if all(params.get(name) for name in names):
        return None
    return error_response(message, code="missing_params", legacy={"error": message})


def ok_or_404(data, message="No data found"):
    """Return a 200 response with the data, or a 404 response if the data is falsy."""
    if not data:
        return error_response(
            message, status_code=status.HTTP_404_NOT_FOUND, code="not_found", legacy={"error": message},
        )
    return Response(data, status=status.HTTP_200_OK)
