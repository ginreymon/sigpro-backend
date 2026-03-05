from rest_framework import serializers
from apps.production.models.employee_local import EmployeeLocal


class EmployeeLocalSerializer(serializers.ModelSerializer):

    has_account = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    groups = serializers.ReadOnlyField()
    is_account_active = serializers.ReadOnlyField()
    user_id  = serializers.ReadOnlyField()

    class Meta:
        model = EmployeeLocal
        fields = "__all__"
