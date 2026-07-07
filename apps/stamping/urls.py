from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.stamping.views import (
    StampingProcessViewSet,
    StampingReferenceSamViewSet,
    AdditionalStampingTimeViewSet,
)

router = DefaultRouter()
router.register('processes', StampingProcessViewSet, basename='process')
router.register('reference-sams', StampingReferenceSamViewSet, basename='reference-sam')
router.register('additional-times', AdditionalStampingTimeViewSet, basename='additional-time')

urlpatterns = [
    path('', include(router.urls)),
]
