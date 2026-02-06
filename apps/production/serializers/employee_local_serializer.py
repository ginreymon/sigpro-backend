from rest_framework import serializers
from apps.production.models.employee_local import EmployeeLocal


class EmployeeLocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeLocal
        fields = "__all__"
