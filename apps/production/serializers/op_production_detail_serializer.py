import json
from rest_framework import serializers


class OPProductionDetailSerializer(serializers.Serializer):

    rowId = serializers.IntegerField(source="RowID")
    color = serializers.CharField(source="Color", required=False, allow_null=True, allow_blank=True)

    documentId = serializers.CharField(source="Id_Doc")
    documentType = serializers.CharField(source="Tipo_Doc")
    documentNumber = serializers.IntegerField(source="Numero_Doc")

    reference = serializers.CharField(source="Referencia")
    referenceRowId = serializers.IntegerField(source="Ref_RowID")
    description = serializers.CharField(source="Ref_Descripcion")
    product = serializers.CharField(source="Ref_Producto")

    createdAt = serializers.DateTimeField(source="Fecha_Creacion")
    size = serializers.CharField(source="Talla", required=False, allow_null=True, allow_blank=True)

    destination = serializers.CharField(source="Destino", required=False, allow_null=True, allow_blank=True)
    status = serializers.IntegerField(source="Estado")
    sam = serializers.FloatField(source="SAM", required=False, allow_null=True, default=None)

    orderedQty = serializers.FloatField(source="Cant_Ordenada")
    plannedQty = serializers.FloatField(source="Cant_Planeada")
    completedQty = serializers.FloatField(source="Cant_Completada")
    wasteQty = serializers.FloatField(source="Cant_Desechos")
    rejectedQty = serializers.FloatField(source="Cant_Rechazos")

    skuRowId = serializers.IntegerField(source="SKU_RowID")

    operationCenters = serializers.SerializerMethodField()
    totals = serializers.SerializerMethodField()

    def get_operationCenters(self, obj):
        value = obj.get("Centro_Operaciones")

        if not value:
            return []

        try:
            data = json.loads(value)
            return [
                {
                    "operation": item.get("operacion"),
                    "centerId": item.get("centro_id"),
                    "centerName": item.get("centro_nombre"),
                }
                for item in data
            ]
        except Exception:
            return []

    def get_totals(self, obj):
        value = obj.get("Totales")

        if not value:
            return {}

        try:
            data = json.loads(value)
            if not data:
                return {}

            t = data[0]
            return {
                "orderedQty": t.get("Cant_Ordenada"),
                "plannedQty": t.get("Cant_Planeada"),
                "completedQty": t.get("Cant_Completada"),
                "wasteQty": t.get("Cant_Desechos"),
                "rejectedQty": t.get("Cant_Rechazos"),
            }
        except Exception:
            return {}
