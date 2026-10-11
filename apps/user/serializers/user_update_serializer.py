from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from apps.user.employee import get_employee_serializer_class


class UserUpdateSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        required=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="El nombre de usuario ya existe"
            )
        ],
    )

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(required=False, write_only=True, min_length=8, allow_blank=True)
    group_id = serializers.IntegerField(required=False, write_only=True)
    employee = serializers.SerializerMethodField(read_only=True)
    groups = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "group_id", "is_active", "employee", "groups",]

    def validate(self, attrs):

        email = attrs.get("email")
        group_id = attrs.get("group_id")

        user = self.instance

        if email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                raise serializers.ValidationError({"email": "El correo ya existe"})

        if group_id:
            if not Group.objects.filter(id=group_id).exists():
                raise serializers.ValidationError({"group_id": "El rol no existe"})

        return attrs

    def update(self, instance, validated_data):

        password = validated_data.pop("password", None)
        group_id = validated_data.pop("group_id", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if group_id:
            group = Group.objects.get(id=group_id)
            instance.groups.set([group])

        return instance

    def get_employee(self, obj):

        if hasattr(obj, "employee_link"):
            employee = obj.employee_link.employee_local
            return get_employee_serializer_class()(employee).data

        return None

    def get_groups(self, obj):
        return list(obj.groups.values("id", "name"))
