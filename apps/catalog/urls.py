from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.catalog.views import (
    TechnicalSheetViewSet,
    TechnicalSheetStatusViewSet,
    SheetMeasurementViewSet,
    SheetElasticCutViewSet,
    TechnicalSheetImageViewSet,
    TechnicalSheetPieceImageViewSet,
    TechnicalSheetDataViewSet,
    CollectionViewSet,
)

router = DefaultRouter()
router.register('technical-sheets', TechnicalSheetViewSet, basename='technical-sheet')
router.register('technical-sheet-statuses', TechnicalSheetStatusViewSet, basename='technical-sheet-status')
router.register('sheet-measurements', SheetMeasurementViewSet, basename='sheet-measurement')
router.register('sheet-elastic-cuts', SheetElasticCutViewSet, basename='sheet-elastic-cut')
router.register('technical-sheet-images', TechnicalSheetImageViewSet, basename='technical-sheet-image')
router.register('technical-sheet-piece-images', TechnicalSheetPieceImageViewSet, basename='technical-sheet-piece-image')
router.register('collections', CollectionViewSet, basename='collection')

urlpatterns = [
    path('', include(router.urls)),
    path('technical-sheets-json/', TechnicalSheetDataViewSet.as_view({'get': 'list'}), name='technical-sheet-json'),
    path('referencias/', TechnicalSheetDataViewSet.as_view({'get': 'referencias'}), name='referencias'),
    path('referencia-info/', TechnicalSheetDataViewSet.as_view({'get': 'referencia_info'}), name='referencia-info'),
]
