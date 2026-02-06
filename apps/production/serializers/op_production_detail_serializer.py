import json
from rest_framework import serializers


class OPProductionDetailSerializer(serializers.Serializer):

    RowID = serializers.IntegerField()
    Color = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Id_Doc = serializers.CharField()
    Tipo_Doc = serializers.CharField()
    Numero_Doc = serializers.IntegerField()
    Referencia = serializers.CharField()
    Fecha_Creacion = serializers.DateTimeField()
    Talla = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Destino = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Estado = serializers.IntegerField()
    Cantidad_Ordenada = serializers.FloatField()
    Cantidad_Planeada = serializers.FloatField()
    Cantidad_Completada = serializers.FloatField()
    Cantidad_Desechos = serializers.FloatField()
    Cantidad_Rechazos = serializers.FloatField()
    SKU_RowID = serializers.IntegerField()
    OperacionesCentrosJSON = serializers.SerializerMethodField()

    def get_OperacionesCentrosJSON(self, obj):
        value = obj.get("OperacionesCentrosJSON")

        if not value:
            return []

        try:
            return json.loads(value)
        except Exception:
            return []
