from core.views.base_model_view import BaseModelViewSet
from core.models import Option
from core.serializers.option_serializer import OptionSerializer
from core import option_keys as opt
from core.permissions import roles_option_ids
from rest_framework.exceptions import ValidationError


class OptionViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)

    queryset = Option.objects.all()
    serializer_class = OptionSerializer

    def perform_update(self, serializer):
        if serializer.instance.id in set(roles_option_ids()) and serializer.validated_data.get("state") is False:
            raise ValidationError("No se puede desactivar la opción de gestión de roles.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if instance.id in set(roles_option_ids()):
            raise ValidationError("No se puede eliminar la opción de gestión de roles.")
        super().perform_destroy(instance)
