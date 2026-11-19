from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.base_model_view import BaseModelViewSet
from core.models.module import Module
from core.serializers.module_serializer import ModuleSerializer, ModuleWithOptionsSerializer
from core import option_keys as opt
from core.permissions import roles_option_ids
from rest_framework.exceptions import ValidationError


class ModuleViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)
    # The full module/option tree is only needed by the roles screen.
    read_options_by_action = {"with_options": (opt.ROLES,)}

    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def _holds_roles_option(self, module):
        return module.options.filter(id__in=list(roles_option_ids())).exists()

    def perform_update(self, serializer):
        if serializer.validated_data.get("state") is False and self._holds_roles_option(serializer.instance):
            raise ValidationError("No se puede desactivar el módulo de gestión de roles.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if self._holds_roles_option(instance):
            raise ValidationError("No se puede eliminar el módulo de gestión de roles.")
        super().perform_destroy(instance)

    @action(detail=False, methods=['get'], url_path='with-options', pagination_class=None)
    def with_options(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).prefetch_related('options')
        serializer = ModuleWithOptionsSerializer(queryset, many=True)
        return Response(serializer.data)
