"""
Client for SIESA UNO EE's WSUNOEE webservice: sends documents (<Importar> XML)
through the ImportarXML SOAP method.

Pattern taken from a reference example (crear_tercero.py, a Python script that
creates a third party in SIESA through WSUNOEE) and its generic evolution
(planos/core.py from the same examples repo): configuration -> <Importar> XML
envelope -> SOAP call with zeep -> response interpretation (printTipoError).
That example mixes building the fixed-width line (specific to each SIESA table,
e.g. Terceros) with sending to the webservice (generic for any table). Only the
generic part lives here: build the <Importar> envelope from already-built lines
and send it. Each document type (Terceros, TEP, Requisiciones, ...) builds its
own fixed-width lines in its own builder and passes the result to
`send_flat_file_lines`.

WARNINGS (reviewed 2026-09-23, see the conversation/commit for details):

- **`send_xml`/`send_flat_file_lines` are a synchronous network call** (up to
  ~30s with the configured timeout): they block the Django worker while waiting
  for SIESA. Today only `tep/send/` calls them, on purpose, in the
  request/response cycle.
- **It does not validate the width/format of `flat_file_lines`.** On purpose:
  that validation is each document builder's responsibility (like
  `construir_linea` in the example repo), not this transport's. A builder that
  does not validate can send a malformed line to SIESA with no local safeguard
  here.
- **The WSDL may be served over plain HTTP** (that is how the reference example
  is configured: `http://10.0.0.4:8508/...`). If the real environment uses the
  same scheme, user/password travel unencrypted on the network. That is a
  limitation of the SIESA server/network where it lives, not of this client;
  mitigate with a VPN/internal network, not with changes here.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings

from apps.system_monitoring.metrics_store import record_siesa

logger = logging.getLogger("integration.siesa_webservice")

# SOAP client cache per wsdl_url: zeep.Client downloads and parses the whole
# WSDL on every instantiation (a real cost when called many times in a row,
# e.g. a batch of documents). The WSDL does not change at runtime during the
# process lifetime, so reusing the client is safe. Locked because Django may
# serve with several threads.
_client_cache: dict[str, Any] = {}
_client_cache_lock = threading.Lock()


class SiesaWebserviceConfigError(Exception):
    """Required configuration (SIESA_WSUNOEE_*) to talk to the webservice is missing."""


class SiesaWebserviceError(Exception):
    """The SOAP call failed (invalid WSDL, timeout, network) or the webservice reported an error."""


@dataclass(frozen=True)
class SiesaWebserviceConfig:
    wsdl_url: str
    connection_name: str
    company_id: str
    username: str
    password: str = field(repr=False)  # must never appear in logs/tracebacks/repr()

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
    """Builds the universal WSUNOEE <Importar> envelope: start line, the
    already-built data lines (fixed width, one per <Linea>) and closing line,
    wrapped with the connection credentials. Identical for every document type
    (Terceros, TEP, Requisiciones, ...); only the content of `flat_file_lines`
    changes per table, built beforehand by that document's builder."""
    start_line = "000000100000001001"
    total_lines = 1 + len(flat_file_lines) + 1  # start + data + closing
    closing_line = f"{total_lines:07d}99990001001"

    all_lines = [start_line, *flat_file_lines, closing_line]
    # Escaping is mandatory: a line with "&"/"<"/">" (common in free-text note
    # fields) breaks the XML or injects content into the envelope if it is not
    # escaped before interpolation.
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
            # On a business error (e.g. duplicate document), WSUNOEE returns a
            # typed dataset (e.g. "NewDataSet" with error rows) that zeep
            # deserializes into a Python object instead of leaving raw XML --
            # `tostring` is not possible on it, so it is serialized to JSON
            # as-is to keep the detail.
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
    """zeep client cached per wsdl_url (see the `_client_cache` comment above);
    avoids re-downloading/re-parsing the WSDL on every send."""
    from zeep import Client
    from zeep.transports import Transport

    with _client_cache_lock:
        client = _client_cache.get(wsdl_url)
        if client is None:
            # Without a timeout, a hung WSUNOEE would block this call forever
            # (dangerous if it is ever invoked from a request/view instead of a
            # background job). `timeout` = WSDL fetch, `operation_timeout` =
            # the SOAP call itself.
            transport = Transport(timeout=15, operation_timeout=30)
            logger.info("Connecting to WSUNOEE (first use, will cache): %s", wsdl_url)
            client = Client(wsdl_url, transport=transport)
            _client_cache[wsdl_url] = client
        return client


def send_xml(xml_data: str, cfg: SiesaWebserviceConfig | None = None) -> SiesaWebserviceResult:
    """Calls ImportarXML on the WSUNOEE webservice with an already-built
    <Importar> XML. Raises SiesaWebserviceError if the SOAP call fails (invalid
    WSDL, timeout, network). A printTipoError != 0 does NOT raise: it is
    reported in the result (`ok=False`) so the caller decides what to do
    (retry, mark as failed, etc.), like the rest of the SIESA integration in
    this project, which does not assume error semantics."""
    from requests.exceptions import RequestException
    from zeep.exceptions import Fault, TransportError

    cfg = cfg or SiesaWebserviceConfig.from_settings()

    try:
        client = _get_client(cfg.wsdl_url)
        logger.info("Invoking ImportarXML (%d XML characters)", len(xml_data))
        soap_response = client.service.ImportarXML(pvstrDatos=xml_data, printTipoError=0)
    except (Fault, TransportError, RequestException) as exc:
        logger.error("SOAP call to WSUNOEE failed: %s", exc)
        record_siesa(False, "send")
        raise SiesaWebserviceError(f"Fallo la llamada al webservice SIESA: {exc}") from exc

    result = _parse_result(soap_response)
    record_siesa(True, "send")  # reachability only: a business error (printTipoError) is not an outage
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
    """Shortcut: builds the <Importar> XML from the fixed-width flat-file lines
    already built by the matching document builder, and sends it. Typical use:

        from apps.integration.services.siesa_webservice_client import send_flat_file_lines
        result = send_flat_file_lines([header_line, detail_line_1, ...])
        if not result.ok:
            ...
    """
    cfg = cfg or SiesaWebserviceConfig.from_settings()
    xml_data = build_import_xml(cfg, flat_file_lines)
    return send_xml(xml_data, cfg=cfg)
