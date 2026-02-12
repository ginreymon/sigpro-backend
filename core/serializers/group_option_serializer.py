from rest_framework import serializers
from core.models.group_option import GroupOption


class GroupOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupOption
        fields = "__all__"
