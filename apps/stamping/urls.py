from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.stamping.views import (
    StampingProcessViewSet,
    StampingMachineTypeViewSet,
    StampingMachineViewSet,
    StampingPieceViewSet,
    StampingLocationViewSet,
    StampingStampTypeDescriptionViewSet,
    StampingFabricTypeViewSet,
    StampingTechniqueViewSet,
    StampingReferenceSamViewSet,
    AdditionalStampingTimeViewSet,
    OPStampingDetailViewSet,
    StampingRecordViewSet,
)

router = DefaultRouter()
router.register('processes', StampingProcessViewSet, basename='process')
router.register('machine-types', StampingMachineTypeViewSet, basename='machine-type')
router.register('machines', StampingMachineViewSet, basename='machine')
router.register('pieces', StampingPieceViewSet, basename='piece')
router.register('locations', StampingLocationViewSet, basename='location')
router.register('stamp-type-descriptions', StampingStampTypeDescriptionViewSet, basename='stamp-type-description')
router.register('fabric-types', StampingFabricTypeViewSet, basename='fabric-type')
router.register('techniques', StampingTechniqueViewSet, basename='technique')
router.register('reference-sams', StampingReferenceSamViewSet, basename='reference-sam')
router.register('additional-times', AdditionalStampingTimeViewSet, basename='additional-time')
router.register('stamping-orders', OPStampingDetailViewSet, basename='stamping-order')
router.register('stamping-records', StampingRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
