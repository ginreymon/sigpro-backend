from django.contrib import admin

# Register your models here.
from apps.catalog.models import (
    Collection,
    TechnicalSheetStatus,
    TechnicalSheet,
    SheetMeasurement,
    SheetMeasurementDetail,
    SheetElasticCut,
    SheetElasticCutDetail,
    TechnicalSheetImage,
)

admin.site.register([
    Collection,
    TechnicalSheetStatus,
    TechnicalSheet,
    SheetMeasurement,
    SheetMeasurementDetail,
    SheetElasticCut,
    SheetElasticCutDetail,
    TechnicalSheetImage,
])