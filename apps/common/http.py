from datetime import datetime

from django.utils.text import slugify
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


def build_export_filename(area_name, start_date, end_date, extension="xlsx", fallback="exportacion"):
    """
    Export file name `<area>_<DDMMYYYY>_<DDMMYYYY>.<ext>`: the area is lowercased,
    stripped of accents/special characters and joined with underscores; dates
    arrive as YYYY-MM-DD.
    """
    area = slugify(area_name or "").replace("-", "_") or fallback
    start = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d%m%Y")
    end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d%m%Y")
    return f"{area}_{start}_{end}.{extension}"
