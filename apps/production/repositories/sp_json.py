import json
from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys


def exec_json_procedure(procedure: str, params: list):
    """Executes a stored procedure that returns a single JSON column and
    returns it parsed and passed through `translate_keys`, or None when the
    procedure returns no data.

    `procedure` must be a constant stored procedure name, never user input.
    """
    placeholders = ", ".join(["%s"] * len(params))
    with connection.cursor() as cursor:
        cursor.execute(f"EXEC {procedure} {placeholders}", params)
        row = cursor.fetchone()

    if not row or not row[0]:
        return None

    return translate_keys(json.loads(row[0]))
