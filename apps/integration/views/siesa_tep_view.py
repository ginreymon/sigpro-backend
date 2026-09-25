import datetime as dt

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integration.builders.tep import build_tep_document
from apps.integration.services.siesa_webservice_client import (
    SiesaWebserviceConfig,
    SiesaWebserviceConfigError,
    SiesaWebserviceError,
    send_flat_file_lines,
)


class SiesaTepViewSet(viewsets.ViewSet):
    """Arma un documento TEP (Trabajo En Proceso) a partir de un JSON y lo
    envia a SIESA (WSUNOEE), devolviendo la respuesta real de SIESA en el
    mismo request.

    A proposito NO usa el outbox (`enqueue_document`/`dispatch_siesa_outbox`):
    es una llamada sincrona que bloquea hasta ~30s por request (ver
    advertencia en `siesa_webservice_client.py`). Sirve bien para envios
    puntuales/bajo demanda; si este endpoint pasa a recibir volumen real y
    sostenido de produccion, lo arquitectonicamente correcto es migrar ese
    flujo al outbox (asincrono, no bloquea el worker de Django).
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="tep/send")
    def send(self, request):
        header = request.data.get("header")
        details = request.data.get("details")

        if not isinstance(header, dict) or not header:
            return Response({"error": "'header' es requerido (objeto)"}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(details, list) or not details:
            return Response({"error": "'details' es requerido (lista no vacia)"}, status=status.HTTP_400_BAD_REQUEST)

        header = dict(header)
        fecha = header.get("fecha")
        if isinstance(fecha, str):
            try:
                header["fecha"] = dt.date.fromisoformat(fecha)
            except ValueError:
                return Response(
                    {"error": "'header.fecha' debe tener formato AAAA-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            lines = build_tep_document(header, details)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cfg = SiesaWebserviceConfig.from_settings()
        except SiesaWebserviceConfigError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            result = send_flat_file_lines(lines, cfg=cfg)
        except SiesaWebserviceError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                "ok": result.ok,
                "error_type": result.error_type,
                "error_detail_xml": result.error_detail_xml,
                "flat_file_lines": lines,
            },
            status=status.HTTP_200_OK if result.ok else status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
