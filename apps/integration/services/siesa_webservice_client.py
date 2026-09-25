"""
Cliente del webservice WSUNOEE de SIESA UNO EE: envía documentos (XML
<Importar>) al método SOAP ImportarXML.

Patrón tomado de un ejemplo de referencia (crear_tercero.py — script Python
que crea un tercero en SIESA vía WSUNOEE) y su evolución genérica
(planos/core.py del mismo repo de ejemplos): configuración -> sobre XML
<Importar> -> invocación SOAP con zeep -> interpretación de la respuesta
(printTipoError). Ese ejemplo mezcla el armado de la línea de ancho fijo
(específico de cada tabla SIESA, ej. Terceros) con el envío al webservice
(genérico para cualquier tabla). Aquí solo vive lo genérico: construir el
sobre <Importar> a partir de líneas ya armadas y enviarlo. Cada tipo de
documento (Terceros, TEP, Requisiciones, ...) arma sus propias líneas de
ancho fijo en su propio builder y le pasa el resultado a `send_flat_file_lines`.

ADVERTENCIAS (revisión 2026-09-23, ver conversación/commit para el detalle):

- **Nunca invocar `send_xml`/`send_flat_file_lines` desde una vista/request de
  usuario.** Es una llamada de red síncrona (hasta ~30s con el timeout
  configurado) — bloquea el worker de Django mientras espera a SIESA. Debe
  invocarse solo desde un comando de management/job en background (mismo
  patrón de outbox/Windows Task Scheduler ya usado en el proyecto para otras
  tareas SIESA), nunca en el ciclo request/response.
- **No valida el ancho/formato de `flat_file_lines`.** A propósito: esa
  validación es responsabilidad del builder de cada documento (igual que
  `construir_linea` en el repo de ejemplo), no de este transporte. Un builder
  que no valide puede mandar una línea mal armada a SIESA sin ningún freno
  local aquí.
- **El WSDL puede estar servido por HTTP plano** (así viene configurado en el
  ejemplo de referencia: `http://10.0.0.4:8508/...`). Si el ambiente real usa
  ese mismo esquema, usuario/clave viajan sin cifrar en la red — es una
  limitación del servidor SIESA/la red donde vive, no de este cliente; mitigar
  con VPN/red interna, no con cambios aquí.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings

logger = logging.getLogger("integration.siesa_webservice")

# Cache del cliente SOAP por wsdl_url: zeep.Client descarga y parsea el WSDL
# completo en cada instanciación (costo real si esto se llama muchas veces
# seguidas, ej. un lote de documentos). El WSDL no cambia en caliente durante
# la vida del proceso, así que reusar el cliente es seguro. Con lock porque
# Django puede servir con varios threads.
_client_cache: dict[str, Any] = {}
_client_cache_lock = threading.Lock()


class SiesaWebserviceConfigError(Exception):
    """Falta configuración obligatoria (SIESA_WSUNOEE_*) para hablar con el webservice."""


class SiesaWebserviceError(Exception):
    """La llamada SOAP falló (WSDL inválido, timeout, red) o el webservice reportó error."""


@dataclass(frozen=True)
class SiesaWebserviceConfig:
    wsdl_url: str
    connection_name: str
    company_id: str
    username: str
    password: str = field(repr=False)  # nunca debe salir en logs/tracebacks/repr()

    @classmethod
    def from_settings(cls) -> "SiesaWebserviceConfig":
        fields = {
            "wsdl_url": getattr(settings, "SIESA_WSUNOEE_WSDL_URL", ""),
            "connection_name": getattr(settings, "SIESA_WSUNOEE_CONNECTION_NAME", ""),
            "company_id": getattr(settings, "SIESA_WSUNOEE_COMPANY_ID", ""),
            "username": getattr(settings, "SIESA_WSUNOEE_USERNAME", ""),
            "password": getattr(settings, "SIESA_WSUNOEE_PASSWORD", ""),
        }
        missing = [name for name, value in fields.items() if not value]
        if missing:
            raise SiesaWebserviceConfigError(
                "Faltan variables de configuración para SIESA WSUNOEE (agregar a backend/.env): "
                + ", ".join(f"SIESA_WSUNOEE_{name.upper()}" for name in missing)
            )
        return cls(**fields)


@dataclass(frozen=True)
class SiesaWebserviceResult:
    ok: bool
    error_type: int | None
    error_detail_xml: str | None
    raw_response: Any


def build_import_xml(cfg: SiesaWebserviceConfig, flat_file_lines: list[str]) -> str:
    """Arma el sobre <Importar> universal de WSUNOEE: línea de inicio, las
    líneas de datos ya construidas (ancho fijo, una por <Linea>) y línea de
    cierre, envueltas con las credenciales de conexión. Igual para cualquier
    tipo de documento (Terceros, TEP, Requisiciones, ...) — lo único que
    cambia por tabla es el contenido de `flat_file_lines`, armado antes por el
    builder de ese documento."""
    start_line = "000000100000001001"
    total_lines = 1 + len(flat_file_lines) + 1  # inicio + datos + cierre
    closing_line = f"{total_lines:07d}99990001001"

    all_lines = [start_line, *flat_file_lines, closing_line]
    # Escapar es obligatorio: una línea con "&"/"<"/">" (frecuente en campos de
    # notas de texto libre) rompe el XML o inyecta contenido en el sobre si no
    # se escapa antes de interpolarla.
    data_xml = "\n".join(f"    <Linea>{xml_escape(line)}</Linea>" for line in all_lines)

    return (
        "<Importar>\n"
        f"  <NombreConexion>{xml_escape(cfg.connection_name)}</NombreConexion>\n"
        f"  <IdCia>{xml_escape(cfg.company_id)}</IdCia>\n"
        f"  <Usuario>{xml_escape(cfg.username)}</Usuario>\n"
        f"  <Clave>{xml_escape(cfg.password)}</Clave>\n"
        "  <Datos>\n"
        f"{data_xml}\n"
        "  </Datos>\n"
        "</Importar>"
    )


def _parse_result(soap_response: Any) -> SiesaWebserviceResult:
    import_result = getattr(soap_response, "ImportarXMLResult", None)
    value = getattr(import_result, "_value_1", None) if import_result is not None else None

    error_detail_xml = None
    if value is not None:
        from lxml.etree import _Element

        if isinstance(value, _Element):
            from lxml import etree
            error_detail_xml = etree.tostring(value, pretty_print=True).decode("utf-8")
        else:
            # Cuando hay error de negocio (ej. documento duplicado), WSUNOEE
            # devuelve un dataset tipado (ej. "NewDataSet" con filas de error)
            # que zeep deserializa a un objeto Python en vez de dejarlo como
            # XML crudo -- no hay `tostring` posible sobre eso, así que se
            # serializa a JSON con los datos tal cual para no perder el detalle.
            import json
            from zeep.helpers import serialize_object
            error_detail_xml = json.dumps(serialize_object(value), default=str, ensure_ascii=False)

    error_type = getattr(soap_response, "printTipoError", None)
    return SiesaWebserviceResult(
        ok=error_type in (0, None),
        error_type=error_type,
        error_detail_xml=error_detail_xml,
        raw_response=soap_response,
    )


def _get_client(wsdl_url: str):
    """Cliente zeep cacheado por wsdl_url (ver comentario de `_client_cache`
    arriba) — evita re-descargar/re-parsear el WSDL en cada envío."""
    from zeep import Client
    from zeep.transports import Transport

    with _client_cache_lock:
        client = _client_cache.get(wsdl_url)
        if client is None:
            # Sin timeout, un WSUNOEE colgado bloquearía esta llamada
            # indefinidamente (peligroso si algún día se invoca desde un
            # request/vista en vez de un job en background). `timeout` =
            # fetch del WSDL, `operation_timeout` = la llamada SOAP en sí.
            transport = Transport(timeout=15, operation_timeout=30)
            logger.info("Connecting to WSUNOEE (first use, will cache): %s", wsdl_url)
            client = Client(wsdl_url, transport=transport)
            _client_cache[wsdl_url] = client
        return client


def send_xml(xml_data: str, cfg: SiesaWebserviceConfig | None = None) -> SiesaWebserviceResult:
    """Invoca ImportarXML contra el webservice WSUNOEE con un XML <Importar>
    ya armado. Lanza SiesaWebserviceError si la llamada SOAP falla (WSDL
    inválido, timeout, red) — un printTipoError != 0 NO lanza excepción, se
    reporta en el resultado (`ok=False`) para que quien llame decida qué
    hacer (reintentar, marcar como fallido, etc.), igual que el resto de la
    integración con SIESA en este proyecto no asume la semántica de error."""
    from requests.exceptions import RequestException
    from zeep.exceptions import Fault, TransportError

    cfg = cfg or SiesaWebserviceConfig.from_settings()

    try:
        client = _get_client(cfg.wsdl_url)
        logger.info("Invoking ImportarXML (%d XML characters)", len(xml_data))
        soap_response = client.service.ImportarXML(pvstrDatos=xml_data, printTipoError=0)
    except (Fault, TransportError, RequestException) as exc:
        logger.error("SOAP call to WSUNOEE failed: %s", exc)
        raise SiesaWebserviceError(f"Fallo la llamada al webservice SIESA: {exc}") from exc

    result = _parse_result(soap_response)
    if result.ok:
        logger.info("WSUNOEE responded with no error (printTipoError=0)")
    else:
        logger.error(
            "WSUNOEE reported an error (printTipoError=%s): %s",
            result.error_type, result.error_detail_xml,
        )
    return result


def send_flat_file_lines(
    flat_file_lines: list[str], cfg: SiesaWebserviceConfig | None = None
) -> SiesaWebserviceResult:
    """Atajo: arma el XML <Importar> a partir de las líneas de plano de ancho
    fijo ya construidas por el builder del documento correspondiente, y lo
    envía. Uso típico:

        from apps.integration.services.siesa_webservice_client import send_flat_file_lines
        result = send_flat_file_lines([header_line, detail_line_1, ...])
        if not result.ok:
            ...
    """
    cfg = cfg or SiesaWebserviceConfig.from_settings()
    xml_data = build_import_xml(cfg, flat_file_lines)
    return send_xml(xml_data, cfg=cfg)
