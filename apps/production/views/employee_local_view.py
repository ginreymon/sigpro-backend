from apps.production.models import EmployeeLocal
from apps.production.serializers import EmployeeLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet


class EmployeeLocalViewSet(LocalBaseModelViewSet):
    queryset = EmployeeLocal.objects.all()
    serializer_class = EmployeeLocalSerializer
