import datetime as dt

from django.test import SimpleTestCase, TestCase

from apps.integration.builders.flat_file import build_line
from apps.integration.builders.tep import (
    DETAIL_LAYOUT,
    HEADER_LAYOUT,
    build_tep_document,
    validate_header,
)
from apps.integration.services.siesa_outbox_service import enqueue_document

# Líneas reales tomadas de `assets/MovInv 3.TXT` (archivo generado por
# TP.xlsm, plano oficial de SIESA) — no son datos inventados. Se embeben
# como literal en vez de leer el archivo porque `assets/` no es parte del
# repo de backend (no está versionado), así que el test sigue siendo
# reproducible en cualquier clon/CI.
REAL_HEADER_LINE = '0000002045002010011001TPW000000022026092210                                                                                                                                                                                                                                                               731                              CF005          1'
REAL_DETAIL_LINE = '000000408800003001001TPW000000020000000001OP 000404780000000                                                                                                              0030CF005          0                              0000000000000000008800000000000000000000000000000000000000000  000000000000006.36                                                                                                                                                                                                                                                                 0001'


class TepBuilderByteAccuracyTests(SimpleTestCase):
    """Compara la salida del builder contra líneas reales generadas por
    TP.xlsm. Si esto falla, el plano que se envíe a SIESA no va a tener el
    formato exacto que espera SIESA — lo rechazará o leerá datos
    desplazados. Este test es la red de seguridad contra eso."""

    def setUp(self):
        self.header_values = dict(
            cia=1, consec_auto_reg=1, id_co="001", id_tipo_docto="TPW",
            consec_docto=2, fecha=dt.date(2026, 9, 22), ind_estado=1,
            ind_impresion=0, notas=None, id_clase_docto="731",
            docto_alterno=None, id_empleado=None, id_centro_trabajo="CF005",
            turno=1,
        )
        self.detail_values = dict(
            cia=1, id_co="001", id_tipo_docto_tep="TPW", consec_docto_tep=2,
            nro_registro=1, id_tipo_docto_op="OP", consec_docto_op=40478,
            numero_operacion=30, id_ctrabajo="CF005", ind_tipo_hora=0,
            ind_operacion_completa=0, cant_completa_base=0.088, horas=6.36,
        )

    def test_header_line_matches_real_file_byte_for_byte(self):
        line = build_line(HEADER_LAYOUT, 2, self.header_values)
        self.assertEqual(len(line), 347)
        self.assertEqual(line, REAL_HEADER_LINE)

    def test_detail_line_matches_real_file_byte_for_byte(self):
        line = build_line(DETAIL_LAYOUT, 4, self.detail_values)
        self.assertEqual(len(line), 562)
        self.assertEqual(line, REAL_DETAIL_LINE)

    def test_build_tep_document_produces_header_plus_detail(self):
        lines = build_tep_document(
            self.header_values,
            [dict(
                id_tipo_docto_op="OP", consec_docto_op=40478,
                numero_operacion=30, id_ctrabajo="CF005",
                cant_completa_base=0.088, horas=6.36,
            )],
        )
        self.assertEqual(len(lines), 2)
        self.assertEqual(len(lines[0]), 347)
        self.assertEqual(len(lines[1]), 562)

    def test_missing_work_center_for_class_731_is_rejected(self):
        errors = validate_header({"id_clase_docto": "731", "id_centro_trabajo": ""})
        self.assertTrue(errors)

    def test_missing_employee_for_class_730_is_rejected(self):
        errors = validate_header({"id_clase_docto": "730", "id_empleado": ""})
        self.assertTrue(errors)

    def test_valid_header_has_no_missing_fields(self):
        errors = validate_header(self.header_values)
        self.assertEqual(errors, [])


class SiesaOutboxServiceTests(TestCase):
    """`enqueue_document` toca base de datos (Django ORM) — TestCase envuelve
    cada test en una transacción y la revierte al final, sin dejar filas de
    prueba en la tabla real."""

    def test_enqueue_is_idempotent_by_idempotency_key(self):
        lines = ["x" * 347, "y" * 562]
        first = enqueue_document("TEP", "test-idempotency-key", lines)
        second = enqueue_document("TEP", "test-idempotency-key", lines)
        self.assertEqual(first.id, second.id)
