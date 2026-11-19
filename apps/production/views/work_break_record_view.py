from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkBreakRecord
from apps.production.serializers import WorkBreakRecordSerializer
from core import option_keys as opt


class WorkBreakRecordViewSet(AuditModelViewSet):
    write_options = (opt.PROD_DAY_OPERATION, opt.PROD_SHIFT_CYCLES, opt.STAMP_DAY_OPERATION, opt.STAMP_SHIFT_CYCLES, *opt.SESSION_EDITORS_ADMIN)

    queryset = WorkBreakRecord.objects.all()
    serializer_class = WorkBreakRecordSerializer
