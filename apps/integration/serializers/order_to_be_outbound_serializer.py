from rest_framework import serializers


class OrderToBeOutboundDetailSerializer(serializers.Serializer):
    """Una entrada de `detail` de sp_totales_registrados_por_op_json: las
    columnas del SP que no son del grupo."""

    op_rowid = serializers.IntegerField()
    op_number = serializers.IntegerField()
    op_type = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    total_completed = serializers.FloatField()
    total_scrap = serializers.FloatField()
    total_rejected = serializers.FloatField()
    total_recorded = serializers.FloatField()
    total_records = serializers.IntegerField()
    pieces = serializers.FloatField(allow_null=True)
    times_on_route = serializers.IntegerField(allow_null=True)
    operation_number = serializers.IntegerField(allow_null=True)
    completed_operation = serializers.IntegerField(allow_null=True)
    erp_planned_quantity = serializers.FloatField(allow_null=True)
    erp_ordered_quantity = serializers.FloatField(allow_null=True)
    erp_completed_quantity = serializers.FloatField(allow_null=True)
    erp_rejected_quantity = serializers.FloatField(allow_null=True)
    erp_scrap_quantity = serializers.FloatField(allow_null=True)
    recorded_quantity_per_piece = serializers.FloatField(allow_null=True)
    erp_quantity_difference = serializers.FloatField(allow_null=True)
    # Ids de los registros agrupados (production/stamping record), arreglo JSON del SP.
    register_ids = serializers.ListField(child=serializers.IntegerField())


class OrderToBeOutboundSerializer(serializers.Serializer):
    """Fila de la tabla de aprobación: un item de `work_centers` de
    dbo.sp_totales_registrados_por_op_json (día + code/work_center_id), con el
    largo de su `detail` y el `detail` mismo (ver OPTotalsService). Las
    columnas deben coincidir con el JSON del SP."""

    # Secuencial dentro de la respuesta (lo asigna OPTotalsService): la fila
    # no tiene un id propio, solo encaja con el contrato BaseEntity de la tabla.
    id = serializers.IntegerField()
    # None cuando la consulta no trae rango de fechas.
    day_number = serializers.IntegerField(allow_null=True)
    record_date = serializers.CharField(allow_null=True)

    code = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    work_center_id = serializers.IntegerField()
    origin = serializers.CharField()
    origin_id = serializers.IntegerField()
    core_module_id = serializers.IntegerField(allow_null=True)
    first_start = serializers.DateTimeField(allow_null=True)
    last_end = serializers.DateTimeField(allow_null=True)

    detail_count = serializers.IntegerField()
    detail = OrderToBeOutboundDetailSerializer(many=True)
