import json
from rest_framework import serializers


class OPProductionDetailSerializer(serializers.Serializer):

    RowID = serializers.IntegerField()
    Color = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Id_Doc = serializers.CharField()
    Tipo_Doc = serializers.CharField()
    Numero_Doc = serializers.IntegerField()
    Referencia = serializers.CharField()
    Ref_RowID = serializers.IntegerField()
    Ref_Descripcion = serializers.CharField()
    Ref_Producto = serializers.CharField()
    Fecha_Creacion = serializers.DateTimeField()
    Talla = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Destino = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Estado = serializers.IntegerField()
    Cant_Ordenada = serializers.FloatField()
    Cant_Planeada = serializers.FloatField()
    Cant_Completada = serializers.FloatField()
    Cant_Desechos = serializers.FloatField()
    Cant_Rechazos = serializers.FloatField()
    SKU_RowID = serializers.IntegerField()
    Centro_Operaciones = serializers.SerializerMethodField()
    Totales = serializers.SerializerMethodField()

    def get_Centro_Operaciones(self, obj):
        value = obj.get("Centro_Operaciones")

        if not value:
            return []

        try:
            return json.loads(value)
        except Exception:
            return []

    def get_Totales(self, obj):
        value = obj.get("Totales")

        if not value:
            return {}

        try:
            data = json.loads(value)
            return data[0] if data else {}
        except Exception:
            return {}
