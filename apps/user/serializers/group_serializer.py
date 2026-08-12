from rest_framework import serializers
from apps.user.serializers.permission_serializer import PermissionSerializer
from core.serializers.option_serializer import OptionSerializer
from core.models.group_option import GroupOption
from core.models.role_home_view import RoleHomeView
from django.contrib.auth.models import Group
from django.db import transaction


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    options = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    option_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    home_view = serializers.SerializerMethodField()
    home_view_label = serializers.SerializerMethodField()
    home_view_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Group
        fields = "__all__"

    def get_options(self, obj):
        options = [go.option for go in obj.group_options.all()]
        return OptionSerializer(options, many=True).data

    def get_user_count(self, obj):
        annotated = getattr(obj, "user_count", None)
        if annotated is not None:
            return annotated
        return obj.user_set.count()

    def get_home_view(self, obj):
        link = getattr(obj, "home_view_link", None)
        return link.home_view_id if link else None

    def get_home_view_label(self, obj):
        link = getattr(obj, "home_view_link", None)
        return link.home_view.label if link else None

    @transaction.atomic
    def create(self, validated_data):
        option_ids = validated_data.pop("option_ids", [])
        home_view_id = validated_data.pop("home_view_id", None)

        group = Group.objects.create(**validated_data)

        if option_ids:
            group_options = [
                GroupOption(group=group, option_id=option_id)
                for option_id in option_ids
            ]
            GroupOption.objects.bulk_create(group_options)

        if home_view_id:
            RoleHomeView.objects.create(group=group, home_view_id=home_view_id)

        return group

    @transaction.atomic
    def update(self, instance, validated_data):
        option_ids = validated_data.pop("option_ids", None)
        home_view_id = validated_data.pop("home_view_id", serializers.empty)

        instance.name = validated_data.get("name", instance.name)
        instance.save()

        if option_ids is not None:
            GroupOption.objects.filter(group=instance).delete()

            group_options = [
                GroupOption(group=instance, option_id=option_id)
                for option_id in option_ids
            ]
            GroupOption.objects.bulk_create(group_options)

        if home_view_id is not serializers.empty:
            RoleHomeView.objects.filter(group=instance).delete()
            if home_view_id:
                RoleHomeView.objects.create(group=instance, home_view_id=home_view_id)

        return instance
