from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.integration.views import SiesaOutboundDocumentViewSet, SiesaTepViewSet, OrdersToBeOutboundViewSet

router = DefaultRouter()
router.register('siesa-outbound-documents', SiesaOutboundDocumentViewSet, basename='siesa-outbound-document')
router.register('orders-to-be-outbound', OrdersToBeOutboundViewSet, basename='orders-to-be-outbound')
router.register(r'', SiesaTepViewSet, basename='siesa-tep')

urlpatterns = [
    path('', include(router.urls)),
]
