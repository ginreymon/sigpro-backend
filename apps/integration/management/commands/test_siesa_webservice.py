"""
Comando de humo manual para probar la integración SIESA de punta a punta,
SIN pasar por el outbox (llama al webservice directo, a propósito, para
poder ver el resultado al instante en vez de esperar al dispatcher).

Uso:
    # Solo arma el XML con datos de prueba y lo muestra — no llama a nadie.
    python manage.py test_siesa_webservice --dry-run

    # Llama de verdad al webservice configurado en SIESA_WSUNOEE_* (.env).
    # USAR SOLO CONTRA UN AMBIENTE DE PRUEBAS/UAT, nunca contra producción
    # sin que el negocio lo apruebe explícitamente.
    python manage.py test_siesa_webservice

Los datos de prueba usan notas="PRUEBA CLAUDE CODE - TEP" y un consec_docto
alto (999999) para poder ubicarlos e ignorarlos fácil en SIESA.
"""

import datetime as dt

from django.core.management.base import BaseCommand

from apps.integration.builders.tep import build_tep_document
from apps.integration.services.siesa_webservice_client import (
    SiesaWebserviceConfig,
    SiesaWebserviceConfigError,
    SiesaWebserviceError,
    build_import_xml,
    send_flat_file_lines,
)

_DEMO_HEADER = dict(
    cia=1, id_co="001", id_tipo_docto="TPW", consec_docto=999999,
    fecha=dt.date.today(), id_clase_docto="731", id_centro_trabajo="CF005",
    turno=1, notas="PRUEBA CLAUDE CODE - TEP",
)
_DEMO_DETAIL = dict(
    id_tipo_docto_op="OP", consec_docto_op=40478, numero_operacion=30,
    id_ctrabajo="CF005", cant_completa_base=0.088, horas=6.36,
)


class Command(BaseCommand):
    help = (
        "Prueba manual de humo contra WSUNOEE con un documento TEP de prueba "
        "claramente marcado. No usa el outbox — llama al webservice directo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo arma y muestra el XML <Importar>, no llama al webservice.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        self.stdout.write("Armando documento TEP de prueba...")
        lines = build_tep_document(_DEMO_HEADER, [_DEMO_DETAIL])
        self.stdout.write(self.style.SUCCESS(
            f"OK: {len(lines)} líneas armadas (anchos: {[len(l) for l in lines]})"
        ))

        try:
            cfg = SiesaWebserviceConfig.from_settings()
        except SiesaWebserviceConfigError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            self.stdout.write(
                "No se puede armar el XML completo sin configuración — "
                "mostrando solo las líneas de datos:"
            )
            for line in lines:
                self.stdout.write(f"  {line!r}")
            return

        xml_data = build_import_xml(cfg, lines)
        self.stdout.write("\n--- XML a enviar ---")
        self.stdout.write(xml_data.replace(cfg.password, "***"))

        if dry_run:
            self.stdout.write(self.style.WARNING("\n--dry-run: no se llamó al webservice."))
            return

        self.stdout.write(self.style.WARNING(
            f"\nInvocando el webservice real en {cfg.wsdl_url} ..."
        ))
        try:
            result = send_flat_file_lines(lines, cfg=cfg)
        except SiesaWebserviceError as exc:
            self.stderr.write(self.style.ERROR(f"Fallo la llamada: {exc}"))
            return

        if result.ok:
            self.stdout.write(self.style.SUCCESS(
                "OK: WSUNOEE respondió sin error (printTipoError=0). "
                "Verifica en SIESA UNO EE (documento TEP, consec_docto=999999) "
                "que el registro haya quedado creado — ImportarXML no lo confirma."
            ))
        else:
            self.stderr.write(self.style.ERROR(
                f"WSUNOEE reportó error (printTipoError={result.error_type}):"
            ))
            self.stderr.write(str(result.error_detail_xml))
