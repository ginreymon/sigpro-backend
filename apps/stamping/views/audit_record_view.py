import django_filters as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from core.exceptions import error_response
from core.views.audit_model_view import AuditModelViewSet
from apps.stamping.models.audit_record_detail import AuditRecordDetail
from apps.stamping.repositories.audit_record_repository import AuditRecordRepository
from apps.stamping.serializers import (
    AuditRecordSerializer,
    AuditRecordBulkCreateSerializer,
    AuditedOpSummarySerializer,
)
from apps.stamping.serializers.audit_record_serializer import (
    OpBlockParamsSerializer,
    OpDocumentParamsSerializer,
    validate_query_params,
)
from apps.stamping.services.audit_record_service import AuditRecordService
from core import option_keys as opt


class AuditRecordDetailFilterSet(filters.FilterSet):
    """Expone los mismos nombres de parámetro que antes de normalizar la
    tabla (op_number, op_rowid, ...), aunque ahora viven en el AuditRecord
    padre en vez de en AuditRecordDetail."""

    op_number = filters.NumberFilter(field_name='audit_record__op_number')
    op_rowid = filters.NumberFilter(field_name='audit_record__op_rowid')
    op_type = filters.CharFilter(field_name='audit_record__op_type')
    total_ordered_quantity = filters.NumberFilter(field_name='audit_record__total_ordered_quantity')
    created_by = filters.NumberFilter(field_name='audit_record__created_by')
    updated_by = filters.NumberFilter(field_name='audit_record__updated_by')

    class Meta:
        model = AuditRecordDetail
        fields = [
            'op_number', 'op_rowid', 'op_type', 'total_ordered_quantity',
            'color', 'ordered_quantity', 'audited_quantity',
            'created_by', 'updated_by',
        ]


class AuditRecordViewSet(AuditModelViewSet):
    """
    Los registros de auditoría se manejan en bloque por OP (op_number/op_rowid/op_type),
    nunca fila por fila: por eso update/partial_update/destroy quedan deshabilitados y
    la edición/borrado real ocurre en la acción `bulk`.

    Almacenamiento normalizado: cada fila expuesta por la API es un
    AuditRecordDetail (un color), aplanado junto a los datos de su
    AuditRecord padre (op_number/op_rowid/op_type/total_ordered_quantity).

    La vista solo interpreta la petición y serializa la respuesta; las reglas
    viven en AuditRecordService y el acceso a datos en AuditRecordRepository.
    """

    write_options = (opt.AUDITORY,)

    queryset = AuditRecordRepository.details_queryset()
    serializer_class = AuditRecordSerializer
    filterset_class = AuditRecordDetailFilterSet
    ordering_fields = ['color', 'ordered_quantity', 'audited_quantity']
    ordering = ['-audit_record__created_at']

    def _serialize_details(self, details):
        return AuditRecordSerializer(details, many=True, context=self.get_serializer_context()).data

    def create(self, request, *args, **kwargs):
        input_serializer = AuditRecordBulkCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        instances = AuditRecordService.create_block(input_serializer.validated_data, request.user)
        return Response(self._serialize_details(instances), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @action(detail=False, methods=['put', 'delete'], url_path='bulk')
    def bulk(self, request):
        if request.method == 'PUT':
            return self._bulk_update(request)
        return self._bulk_delete(request)

    @action(detail=False, methods=['post'], url_path='bulk/confirm')
    def confirm(self, request):
        block = validate_query_params(OpBlockParamsSerializer, request.query_params)
        details = AuditRecordService.confirm_block(
            block['op_number'], block['op_rowid'], block['op_type'], request.user,
        )

        if details is None:
            return error_response(
                "No existe un bloque de auditoría para esta OP.",
                status_code=status.HTTP_404_NOT_FOUND, code="audit_block_not_found",
            )

        return Response(self._serialize_details(details))

    @action(detail=False, methods=['get'], url_path='status')
    def status_for_op(self, request):
        """Estado de auditoría de una OP por docType/docNumber (?docType=OP&docNumber=40346),
        sin traer el detalle por color — para saber al buscar una OP si ya
        fue auditada."""
        document = validate_query_params(OpDocumentParamsSerializer, request.query_params)
        return Response(
            AuditRecordService.status_for_document(document['docType'], document['docNumber'])
        )

    @action(detail=False, methods=['get'], url_path='audited-ops')
    def audited_ops(self, request):
        """Una fila por OP ya confirmada (is_audited=True), de la más
        reciente a la más antigua en ser auditada. Búsqueda por op_number
        (parcial, ej. "404" encuentra la OP 40436)."""
        queryset = AuditRecordService.audited_ops(request.query_params.get('search'))

        page = self.paginate_queryset(queryset)
        AuditRecordService.attach_cut_tracking(page)
        serializer = AuditedOpSummarySerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    def _bulk_update(self, request):
        input_serializer = AuditRecordBulkCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        instances = AuditRecordService.replace_block(input_serializer.validated_data, request.user)
        return Response(self._serialize_details(instances))

    def _bulk_delete(self, request):
        block = validate_query_params(OpBlockParamsSerializer, request.query_params)
        AuditRecordService.delete_block(block['op_number'], block['op_rowid'], block['op_type'])
        return Response(status=status.HTTP_204_NO_CONTENT)
