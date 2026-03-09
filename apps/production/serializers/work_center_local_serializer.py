from rest_framework import serializers
from apps.production.models.work_center_local import WorkCenterLocal


class WorkCenterLocalSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()

    class Meta:
        model = WorkCenterLocal
        fields = "__all__"

    def get_code(self, obj):
        return obj.code.strip() if obj.code else obj.code

    def get_description(self, obj):
        return obj.description.strip() if obj.description else obj.description

    def get_short_description(self, obj):
        return obj.short_description.strip() if obj.short_description else obj.short_description