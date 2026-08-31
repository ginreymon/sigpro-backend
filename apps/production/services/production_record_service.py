from django.utils import timezone
from rest_framework.exceptions import ValidationError


def validate_manual_duration_budget(indicators: dict, duration_seconds: float) -> None:
    """
    Rejects a manual-duration entry that claims more time than has actually
    elapsed in the shift, net of breaks/downtime (and, once there are prior
    records, net of the elapsed time those records already cover).

    has_no_records:  (now - period_start) - work_break_seconds - module_downtime_seconds - duration_seconds >= 0
    otherwise:       (now - elapsed_time_max_seconds) - duration_seconds > 0

    Raises ValidationError when the budget is exceeded.
    """
    elapsed_real_seconds = (timezone.now() - indicators['period_start']).total_seconds()

    if indicators['has_no_records']:
        available_seconds = (
            elapsed_real_seconds
            - indicators['work_break_seconds']
            - indicators['module_downtime_seconds']
            - duration_seconds
        )
        is_valid = available_seconds >= 0
    else:
        remaining_seconds = elapsed_real_seconds - indicators['elapsed_time_max_seconds']
        available_seconds = remaining_seconds - duration_seconds
        is_valid = available_seconds > 0

    if not is_valid:
        raise ValidationError({
            'duration_seconds': 'La duración excede el tiempo disponible del turno.'
        })
