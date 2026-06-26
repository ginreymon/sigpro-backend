from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.catalog.views import (
    TechnicalSheetViewSet,
    SheetMeasurementViewSet,
    SheetElasticCutViewSet,
    TechnicalSheetImageViewSet,
)

router = DefaultRouter()
router.register('technical-sheets',       TechnicalSheetViewSet,      basename='technical-sheet')
router.register('sheet-measurements',     SheetMeasurementViewSet,    basename='sheet-measurement')
router.register('sheet-elastic-cuts',     SheetElasticCutViewSet,     basename='sheet-elastic-cut')
router.register('technical-sheet-images', TechnicalSheetImageViewSet, basename='technical-sheet-image')

urlpatterns = [
    path('', include(router.urls)),
]
