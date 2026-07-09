from rest_framework import serializers
from django.contrib.auth.models import User, Group
from apps.user.models import UserEmployeeLink
from apps.production.models import EmployeeLocal
from django.db import transaction
from rest_framework.validators import UniqueValidator


class RegisterSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="El nombre de usuario ya existe")
        ]
    )

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    employee_local_id = serializers.IntegerField(write_only=True, required=True)
    group_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "employee_local_id","group_id"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):

        employee_id = attrs.get("employee_local_id")
        group_id = attrs.get("group_id")
        email = attrs.get("email")

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "El correo ya existe"})

        try:
            employee = EmployeeLocal.objects.get(id=employee_id)
        except EmployeeLocal.DoesNotExist:
            raise serializers.ValidationError(
                {"employee_local_id": "El empleado no existe"}
            )

        if UserEmployeeLink.objects.filter(employee_local=employee).exists():
            raise serializers.ValidationError(
                {"employee_local_id": "El empleado ya tiene un usuario"}
            )

        try:
            Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise serializers.ValidationError({"group_id": "El rol no existe"})

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        employee_id = validated_data.pop("employee_local_id")
        group_id = validated_data.pop("group_id")

        employee = EmployeeLocal.objects.get(id=employee_id)

        group = Group.objects.get(id=group_id)

        user = User.objects.create_user(**validated_data)

        user.groups.add(group)

        UserEmployeeLink.objects.create(django_user=user, employee_local=employee)

        return user
