from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ModuleWorkBreakRecord
from apps.production.serializers import ModuleWorkBreakRecordSerializer


class ModuleWorkBreakRecordViewSet(AuditModelViewSet):
    queryset = ModuleWorkBreakRecord.objects.all()
    serializer_class = ModuleWorkBreakRecordSerializer
