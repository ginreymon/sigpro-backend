from rest_framework import status
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.stamping.models.audit_record import AuditRecord
from apps.stamping.serializers import AuditRecordSerializer, AuditRecordBulkCreateSerializer


class AuditRecordViewSet(AuditModelViewSet):
    queryset = AuditRecord.objects.all()
    serializer_class = AuditRecordSerializer

    def create(self, request, *args, **kwargs):
        input_serializer = AuditRecordBulkCreateSerializer(data=request.data, context={"request": request})
        input_serializer.is_valid(raise_exception=True)
        instances = input_serializer.save()

        output_serializer = AuditRecordSerializer(instances, many=True, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
