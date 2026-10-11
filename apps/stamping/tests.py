from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from apps.stamping.serializers.audit_record_serializer import (
    OpBlockParamsSerializer,
    OpDocumentParamsSerializer,
    validate_query_params,
)
from apps.stamping.services.audit_record_service import AuditRecordService

REPOSITORY = "apps.stamping.services.audit_record_service.AuditRecordRepository"


class AuditQueryParamsTests(SimpleTestCase):

    def test_block_params_missing_are_reported_per_field(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_query_params(OpBlockParamsSerializer, {})
        self.assertEqual(
            {field: str(message) for field, message in ctx.exception.detail.items()},
            {
                "op_number": "Este parámetro es obligatorio.",
                "op_rowid": "Este parámetro es obligatorio.",
                "op_type": "Este parámetro es obligatorio.",
            },
        )

    def test_block_params_are_converted_to_int(self):
        params = validate_query_params(
            OpBlockParamsSerializer, {"op_number": "40497", "op_rowid": "12", "op_type": "OP"}
        )
        self.assertEqual(params, {"op_number": 40497, "op_rowid": 12, "op_type": "OP"})

    def test_document_number_must_be_an_integer(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_query_params(OpDocumentParamsSerializer, {"docType": "OP", "docNumber": "abc"})
        self.assertEqual(str(ctx.exception.detail["docNumber"]), "Debe ser un número entero.")


class AuditRecordServiceTests(SimpleTestCase):

    @patch(REPOSITORY)
    def test_confirm_block_returns_none_when_op_has_no_block(self, repository):
        repository.mark_audited.return_value = 0
        self.assertIsNone(AuditRecordService.confirm_block(1, 2, "OP", user="u"))
        repository.block_details.assert_not_called()

    @patch(REPOSITORY)
    def test_confirm_block_returns_details_when_marked(self, repository):
        repository.mark_audited.return_value = 1
        result = AuditRecordService.confirm_block(1, 2, "OP", user="u")
        repository.mark_audited.assert_called_once_with(1, 2, "OP", "u")
        self.assertIs(result, repository.block_details.return_value)

    @patch(REPOSITORY)
    def test_status_for_unknown_document(self, repository):
        repository.find_by_document.return_value = None
        status = AuditRecordService.status_for_document("OP", 40346)
        self.assertEqual(status["exists"], False)
        self.assertEqual(status["is_audited"], False)
        self.assertIsNone(status["matches_total"])

    @patch(REPOSITORY)
    def test_replace_block_deletes_then_creates(self, repository):
        data = {"op_number": 1, "op_rowid": 2, "op_type": "OP", "total_ordered_quantity": 10, "colors": []}
        calls = []
        repository.delete_block.side_effect = lambda *a: calls.append("delete")
        repository.create_block.side_effect = lambda **kw: calls.append("create") or []

        with patch("apps.stamping.services.audit_record_service.transaction"):
            AuditRecordService.replace_block(data, user="u")

        self.assertEqual(calls, ["delete", "create"])
