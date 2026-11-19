from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.base_model_view import BaseModelViewSet
from core.models.module import Module
from core.serializers.module_serializer import ModuleSerializer, ModuleWithOptionsSerializer
from core import option_keys as opt


class ModuleViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)

    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    @action(detail=False, methods=['get'], url_path='with-options', pagination_class=None)
    def with_options(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).prefetch_related('options')
        serializer = ModuleWithOptionsSerializer(queryset, many=True)
        return Response(serializer.data)
