from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.integration.views import SiesaOutboundDocumentViewSet, SiesaTepViewSet

router = DefaultRouter()
router.register('siesa-outbound-documents', SiesaOutboundDocumentViewSet, basename='siesa-outbound-document')
router.register(r'', SiesaTepViewSet, basename='siesa-tep')

urlpatterns = [
    path('', include(router.urls)),
]
