from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core import option_keys as opt

from . import metrics_store as store
from . import services
from .serializers import ClientErrorSerializer


class SummaryView(APIView):
    """Health summary for the admin Home. Cheap: in-memory aggregates + TTL-cached DB ping."""

    read_options = (opt.SYSTEM_MONITORING, opt.SYSTEM_DIAGNOSTICS)

    def get(self, request):
        return Response(services.build_summary())


class DiagnosticsView(APIView):
    """Technical detail (host, DB, slow endpoints, error details). Developers only."""

    read_options = (opt.SYSTEM_DIAGNOSTICS,)

    def get(self, request):
        return Response(services.build_diagnostics())


class SiesaCheckView(APIView):
    """On-demand SIESA reachability probe (a network call, so never part of the summary)."""

    write_options = (opt.SYSTEM_DIAGNOSTICS,)

    def post(self, request):
        return Response(services.check_siesa())


class ClientErrorThrottle(UserRateThrottle):
    rate = "30/min"  # shortcut: counted per worker process (LocMemCache); use a shared cache to cap globally


class ClientErrorView(APIView):
    """Receives frontend errors from any authenticated user (throttled, size-capped)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientErrorThrottle]

    def post(self, request):
        serializer = ClientErrorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        store.record_client_error(request.user.pk, data["message"], data["url"], data["stack"])
        return Response(status=204)
