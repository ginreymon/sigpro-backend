import django_filters as filters
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.stamping.models.audit_record import AuditRecord
from apps.stamping.models.audit_record_detail import AuditRecordDetail
from apps.stamping.serializers import (
    AuditRecordSerializer,
    AuditRecordBulkCreateSerializer,
    AuditedOpSummarySerializer,
)


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
    """

    queryset = AuditRecordDetail.objects.select_related(
        'audit_record', 'audit_record__created_by', 'audit_record__updated_by',
    ).all()
    serializer_class = AuditRecordSerializer
    filterset_class = AuditRecordDetailFilterSet
    ordering_fields = ['color', 'ordered_quantity', 'audited_quantity']
    ordering = ['-audit_record__created_at']

    def create(self, request, *args, **kwargs):
        input_serializer = AuditRecordBulkCreateSerializer(data=request.data, context={"request": request})
        input_serializer.is_valid(raise_exception=True)
        instances = input_serializer.save()

        output_serializer = AuditRecordSerializer(instances, many=True, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

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
        op_number = request.query_params.get('op_number')
        op_rowid = request.query_params.get('op_rowid')
        op_type = request.query_params.get('op_type')

        missing = [f for f, v in (('op_number', op_number), ('op_rowid', op_rowid), ('op_type', op_type)) if not v]
        if missing:
            raise ValidationError({f: "Este parámetro es obligatorio." for f in missing})

        # QuerySet.update() bypasses save(), so auto_now on updated_at won't
        # fire on its own — stamp it explicitly, it's what "most recently
        # audited" ordering in the audited-ops list sorts by.
        updated = AuditRecord.objects.filter(
            op_number=op_number, op_rowid=op_rowid, op_type=op_type,
        ).update(is_audited=True, updated_at=timezone.now(), updated_by=request.user)

        if not updated:
            return Response(
                {"detail": "No existe un bloque de auditoría para esta OP."},
                status=status.HTTP_404_NOT_FOUND,
            )

        details = AuditRecordDetail.objects.filter(
            audit_record__op_number=op_number,
            audit_record__op_rowid=op_rowid,
            audit_record__op_type=op_type,
        ).select_related('audit_record', 'audit_record__created_by', 'audit_record__updated_by')

        output_serializer = AuditRecordSerializer(details, many=True, context=self.get_serializer_context())
        return Response(output_serializer.data)

    @action(detail=False, methods=['get'], url_path='audited-ops')
    def audited_ops(self, request):
        """Una fila por OP ya confirmada (is_audited=True), de la más
        reciente a la más antigua en ser auditada."""
        queryset = AuditRecord.objects.filter(is_audited=True).select_related(
            'created_by', 'updated_by',
        ).order_by('-updated_at')

        page = self.paginate_queryset(queryset)
        serializer = AuditedOpSummarySerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    def _bulk_update(self, request):
        input_serializer = AuditRecordBulkCreateSerializer(data=request.data, context={"request": request})
        input_serializer.is_valid(raise_exception=True)
        instances = input_serializer.replace(input_serializer.validated_data)

        output_serializer = AuditRecordSerializer(instances, many=True, context=self.get_serializer_context())
        return Response(output_serializer.data)

    def _bulk_delete(self, request):
        op_number = request.query_params.get('op_number')
        op_rowid = request.query_params.get('op_rowid')
        op_type = request.query_params.get('op_type')

        missing = [f for f, v in (('op_number', op_number), ('op_rowid', op_rowid), ('op_type', op_type)) if not v]
        if missing:
            raise ValidationError({f: "Este parámetro es obligatorio." for f in missing})

        # Cascade: borrar el AuditRecord padre elimina sus AuditRecordDetail hijos.
        AuditRecord.objects.filter(op_number=op_number, op_rowid=op_rowid, op_type=op_type).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
