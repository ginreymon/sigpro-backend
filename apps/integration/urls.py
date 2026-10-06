from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.integration.views import SiesaTepViewSet, OrdersToBeOutboundViewSet, TepSubmissionViewSet

router = DefaultRouter()
router.register('orders-to-be-outbound', OrdersToBeOutboundViewSet, basename='orders-to-be-outbound')
router.register('tep-submissions', TepSubmissionViewSet, basename='tep-submission')
router.register(r'', SiesaTepViewSet, basename='siesa-tep')

urlpatterns = [
    path('', include(router.urls)),
]
