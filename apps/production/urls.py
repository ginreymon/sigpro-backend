from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.op_components_detail_view import OPComponentsDetailViewSet
from .views.op_production_detail_view import OPProductionDetailViewSet
from .views.op_type_documents_view import OPTypeDocumentsViewSet
from .views.module_assignee_view import ModuleAssigneeViewSet
from .views.module_view import ModuleViewSet
from .views.production_area_view import ProductionAreaViewSet
from .views.work_break_view import WorkBreakViewSet
from .views.work_shift_view import WorkShiftViewSet
from .views.work_session_view import WorkSessionViewSet
from .views.work_session_activity_view import WorkSessionActivityViewSet
from .views.employee_local_view import EmployeeLocalViewSet
from .views.work_center_local_view import WorkCenterLocalViewSet
from .views.sku_item_local_view import SkuItemLocalViewSet
from .views.reference_sam_view import ReferenceSamViewSet
from .views.production_record_view import ProductionRecordViewSet
from .views.work_break_record_view import WorkBreakRecordViewSet
from .views.module_work_break_record_view import ModuleWorkBreakRecordViewSet
from .views.productivity_view import ProductivityViewSet


router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'production-areas', ProductionAreaViewSet)
router.register(r'module-assignees', ModuleAssigneeViewSet)
router.register(r'work-breaks', WorkBreakViewSet)
router.register(r'work-shifts', WorkShiftViewSet)
router.register(r'work-sessions', WorkSessionViewSet)
router.register(r'work-session-activities', WorkSessionActivityViewSet)
router.register(r'employees', EmployeeLocalViewSet)
router.register(r'work-centers', WorkCenterLocalViewSet)
router.register(r'sku-items', SkuItemLocalViewSet)
router.register(r'reference-sam', ReferenceSamViewSet)
router.register(r'production-records', ProductionRecordViewSet)
router.register(r'work-break-records', WorkBreakRecordViewSet)
router.register(r'module-work-break-records', ModuleWorkBreakRecordViewSet)
router.register(r"production-orders", OPProductionDetailViewSet, basename="production-orders")
router.register(r"production-components", OPComponentsDetailViewSet, basename="production-components")
router.register(r"document-types", OPTypeDocumentsViewSet, basename="document-types")
router.register(r"productivity", ProductivityViewSet, basename="productivity")

urlpatterns = [    
    path("", include(router.urls)),
]
