from rest_framework import serializers


class OrderToBeOutboundSerializer(serializers.Serializer):
    """Fila de dbo.fn_totales_registrados_por_op (via sp_totales_registrados_por_op):
    una fila por combinacion op_rowid/op_number/op_type/origin_id. Contrato en
    evolucion (ver docstring de la funcion SQL) — se espera que crezca con mas
    columnas cuando se agregue el flujo de aprobacion/rechazo."""

    # Sintetico: no existe en el SP. La fila no tiene un id propio (la llave
    # natural es op_rowid + origin_id); se deriva solo para que la fila
    # encaje en el contrato BaseEntity que espera la tabla del frontend.
    # origin_id es 1 o 2 (ver fn_totales_registrados_por_op), por eso no
    # colisiona con op_rowid * 10.
    id = serializers.SerializerMethodField()
    op_rowid = serializers.IntegerField()
    op_number = serializers.IntegerField()
    op_type = serializers.CharField()
    origin = serializers.CharField()
    origin_id = serializers.IntegerField()
    ordered_quantity = serializers.IntegerField()
    planned_quantity = serializers.IntegerField()
    total_completed = serializers.IntegerField()
    total_scrap = serializers.IntegerField()
    total_rejected = serializers.IntegerField()
    total_recorded = serializers.IntegerField()
    pending_quantity = serializers.IntegerField()
    total_records = serializers.IntegerField()
    first_start = serializers.DateTimeField(allow_null=True)
    last_end = serializers.DateTimeField(allow_null=True)

    def get_id(self, obj):
        return obj["op_rowid"] * 10 + obj["origin_id"]
