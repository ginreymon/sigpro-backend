from django.contrib.auth.models import User, Group
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from apps.people.models import AuthUserEmployee, EmployeeLocal
from apps.people.serializers import EmployeeLocalSerializer


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
    # Omitted = keep the link, null = remove it, id = (re)link to that employee.
    employee_local_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    employee = serializers.SerializerMethodField(read_only=True)
    groups = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "group_id", "employee_local_id", "is_active", "employee", "groups",]

    def validate(self, attrs):

        # auth_user.email is NOT NULL: store "no email" as an empty string.
        if "email" in attrs and attrs["email"] is None:
            attrs["email"] = ""
        email = attrs.get("email")
        group_id = attrs.get("group_id")

        user = self.instance
        employee_id = attrs.get("employee_local_id")

        if employee_id is not None:
            if not EmployeeLocal.objects.filter(id=employee_id).exists():
                raise serializers.ValidationError({"employee_local_id": "El empleado no existe"})
            if AuthUserEmployee.objects.filter(employee_local_id=employee_id).exclude(auth_user=user).exists():
                raise serializers.ValidationError({"employee_local_id": "El empleado ya tiene un usuario"})

        if email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                raise serializers.ValidationError({"email": "El correo ya existe"})

        if group_id:
            if not Group.objects.filter(id=group_id).exists():
                raise serializers.ValidationError({"group_id": "El rol no existe"})

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):

        has_employee = "employee_local_id" in validated_data
        employee_id = validated_data.pop("employee_local_id", None)
        password = validated_data.pop("password", None)
        group_id = validated_data.pop("group_id", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if has_employee:
            AuthUserEmployee.objects.filter(auth_user=instance).delete()
            if employee_id is not None:
                AuthUserEmployee.objects.create(auth_user=instance, employee_local_id=employee_id)
            instance = User.objects.get(pk=instance.pk)

        if group_id:
            group = Group.objects.get(id=group_id)
            instance.groups.set([group])

        return instance

    def get_employee(self, obj):

        if hasattr(obj, "employee_link"):
            employee = obj.employee_link.employee_local
            return EmployeeLocalSerializer(employee).data

        return None

    def get_groups(self, obj):
        return list(obj.groups.values("id", "name"))
