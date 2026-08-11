from rest_framework import serializers
from core.models.role_home_view import RoleHomeView
from core.serializers.audit_serializer import AuditSerializer


class RoleHomeViewSerializer(AuditSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    home_view_key = serializers.CharField(source='home_view.key', read_only=True)

    class Meta:
        model = RoleHomeView
        fields = "__all__"
