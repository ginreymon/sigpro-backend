from rest_framework import serializers


class AuditSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by_username = serializers.CharField(
        source="updated_by.username", read_only=True
    )

    class Meta:
        abstract = True
