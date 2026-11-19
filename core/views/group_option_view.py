from core.views.base_model_view import BaseModelViewSet
from core.models.group_option import GroupOption
from core.serializers.group_option_serializer import GroupOptionSerializer
from core import option_keys as opt
from core.permissions import other_role_managers, roles_option_ids
from rest_framework.exceptions import ValidationError


class GroupOptionViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)
    read_options = (opt.ROLES,)

    queryset = GroupOption.objects.all()
    serializer_class = GroupOptionSerializer

    def _guard_last_roles_grant(self, instance):
        if instance.option_id in set(roles_option_ids()) and not other_role_managers(instance.group).exists():
            raise ValidationError("Debe existir al menos otro rol activo con acceso a Roles.")

    def perform_destroy(self, instance):
        self._guard_last_roles_grant(instance)
        super().perform_destroy(instance)

    def perform_update(self, serializer):
        self._guard_last_roles_grant(serializer.instance)
        super().perform_update(serializer)
