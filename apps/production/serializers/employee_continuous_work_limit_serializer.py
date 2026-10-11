from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from apps.production.models.employee_continuous_work_limit import EmployeeContinuousWorkLimit
from apps.people.models import EmployeeLocal
from core.serializers.audit_serializer import AuditSerializer
from apps.people.serializers import EmployeeLocalSerializer


class EmployeeContinuousWorkLimitSerializer(AuditSerializer):
    employee = EmployeeLocalSerializer(read_only=True)

    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeLocal.objects.filter(is_deleted=False),
        source="employee",
        write_only=True,
        validators=[UniqueValidator(
            queryset=EmployeeContinuousWorkLimit.objects.all(),
            message="Este empleado ya tiene un límite de trabajo continuo registrado.",
        )],
    )

    class Meta:
        model = EmployeeContinuousWorkLimit
        fields = "__all__"
