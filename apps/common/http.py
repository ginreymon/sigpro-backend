from rest_framework import status
from rest_framework.response import Response


def missing_params_response(params, *names, message=None):
    """Return a 400 response if any of the named params is missing or empty, else None."""
    if all(params.get(name) for name in names):
        return None
    return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)


def ok_or_404(data, message="No data found"):
    """Return a 200 response with the data, or a 404 response if the data is falsy."""
    if not data:
        return Response({"error": message}, status=status.HTTP_404_NOT_FOUND)
    return Response(data, status=status.HTTP_200_OK)
