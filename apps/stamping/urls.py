from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.stamping.views import (
    StampingProcessViewSet,
    StampingMachineTypeViewSet,
    StampingMachineViewSet,
    StampingReferenceSamViewSet,
    AdditionalStampingTimeViewSet,
)

router = DefaultRouter()
router.register('processes', StampingProcessViewSet, basename='process')
router.register('machine-types', StampingMachineTypeViewSet, basename='machine-type')
router.register('machines', StampingMachineViewSet, basename='machine')
router.register('reference-sams', StampingReferenceSamViewSet, basename='reference-sam')
router.register('additional-times', AdditionalStampingTimeViewSet, basename='additional-time')

urlpatterns = [
    path('', include(router.urls)),
]
