from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.integration.views import SiesaOutboundDocumentViewSet

router = DefaultRouter()
router.register('siesa-outbound-documents', SiesaOutboundDocumentViewSet, basename='siesa-outbound-document')

urlpatterns = [
    path('', include(router.urls)),
]
