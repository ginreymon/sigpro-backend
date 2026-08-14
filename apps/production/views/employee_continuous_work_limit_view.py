from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import EmployeeContinuousWorkLimit
from apps.production.serializers import EmployeeContinuousWorkLimitSerializer


class EmployeeContinuousWorkLimitViewSet(AuditModelViewSet):
    queryset = EmployeeContinuousWorkLimit.objects.select_related("employee").all()
    serializer_class = EmployeeContinuousWorkLimitSerializer

    search_fields = [
        "employee__first_name",
        "employee__last_name1",
        "employee__last_name2",
        "employee__id_number",
    ]
