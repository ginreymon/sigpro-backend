from rest_framework import serializers


class OrderToBeOutboundDetailSerializer(serializers.Serializer):
    """One `detail` entry of sp_totales_registrados_por_op_json: the SP columns
    that do not belong to the group."""

    op_rowid = serializers.IntegerField()
    op_number = serializers.IntegerField()
    op_type = serializers.CharField()
    reference = serializers.CharField(allow_null=True)
    reference_rowid = serializers.IntegerField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    total_completed = serializers.FloatField()
    total_scrap = serializers.FloatField()
    total_rejected = serializers.FloatField()
    total_recorded = serializers.FloatField()
    total_records = serializers.IntegerField()
    pieces = serializers.FloatField(allow_null=True)
    times_on_route = serializers.IntegerField(allow_null=True)
    operation_number = serializers.IntegerField(allow_null=True)
    erp_completed_operation = serializers.IntegerField(allow_null=True)
    erp_execution_quantity = serializers.FloatField(allow_null=True)
    erp_completed_quantity = serializers.FloatField(allow_null=True)
    recorded_quantity_per_piece = serializers.FloatField(allow_null=True)
    erp_quantity_discrepancy =serializers.FloatField(allow_null=True)
    # Net time of the OP (excluding breaks and module stoppages) and per recorded
    # unit. Production with a date range only; None for stamping or without a range.
    total_seconds = serializers.FloatField(allow_null=True)
    seconds_by_unit = serializers.FloatField(allow_null=True)
    # Ids of the grouped records (production/stamping record), JSON array from the SP.
    register_ids = serializers.ListField(child=serializers.IntegerField())


class OrderToBeOutboundSerializer(serializers.Serializer):
    """Approval table row: one array item of
    dbo.sp_totales_registrados_por_op_json (day + code/work_center_id), with the
    length of its `detail` and the `detail` itself (see OPTotalsService). The
    columns must match the SP JSON."""

    # Sequential within the response (assigned by OPTotalsService): the row has
    # no id of its own, it only fits the table's BaseEntity contract.
    id = serializers.IntegerField()
    # None when the query has no date range.
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


class WorkCenterDocumentSerializer(OrderToBeOutboundDetailSerializer):
    """One `documents` entry of sp_totales_registrados_por_op_work_center_json: the
    detail columns, with `additional_seconds_by_unit` (not calculated) instead of
    `total_seconds` and with the per-document `detail` ({"colorRows": [...]},
    only for origin_id = 1)."""

    total_seconds = None  # drops the field inherited from the detail serializer
    additional_seconds_by_unit = serializers.FloatField(allow_null=True)
    # MAX(Cantidad_Base_Ruta) of the OP; only Confección (origin_id = 1), None in the rest.
    base_route_quantity = serializers.FloatField(allow_null=True)
    detail = serializers.DictField(allow_null=True)


class OrderIntegrationStatusSerializer(serializers.Serializer):
    """Row of dbo.fn_estado_integracion_op: integrated / pending / missing
    quantities of an OP in a work center (see OPTotalsService). The columns must
    match the SQL function."""

    # Sequential within the response (assigned by OPTotalsService).
    id = serializers.IntegerField()
    op_rowid = serializers.IntegerField()
    op_number = serializers.IntegerField()
    op_type = serializers.CharField()
    origin = serializers.CharField()
    origin_id = serializers.IntegerField()
    code = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    work_center_rowid = serializers.IntegerField()
    core_module_id = serializers.IntegerField(allow_null=True)
    reference = serializers.CharField(allow_null=True)
    reference_rowid = serializers.IntegerField(allow_null=True)

    total_records = serializers.IntegerField()
    integrated_records = serializers.IntegerField()
    pending_records = serializers.IntegerField()
    integrated_quantity = serializers.FloatField(allow_null=True)
    pending_quantity = serializers.FloatField(allow_null=True)
    erp_execution_quantity = serializers.FloatField(allow_null=True)
    erp_completed_quantity = serializers.FloatField(allow_null=True)
    erp_completed_operation = serializers.IntegerField(allow_null=True)
    missing_quantity = serializers.FloatField()

    first_start = serializers.DateTimeField(allow_null=True)
    last_end = serializers.DateTimeField(allow_null=True)
    integration_status = serializers.ChoiceField(choices=("PENDING", "MISSING", "INTEGRATED"))


class OrderIntegrationSummarySerializer(serializers.Serializer):
    """Counters of the integration dashboard (OPTotalsService.get_resumen_integracion):
    rows (OP / work center) and quantities per status."""

    total = serializers.IntegerField()
    integrated = serializers.IntegerField()
    pending = serializers.IntegerField()
    missing = serializers.IntegerField()
    integrated_quantity = serializers.FloatField()
    pending_quantity = serializers.FloatField()
    missing_quantity = serializers.FloatField()


class OrderByWorkCenterSerializer(serializers.Serializer):
    """Row of sp_totales_registrados_por_op_work_center_json: one work center with
    its `documents` and their count (see OPTotalsService). The columns must match
    the SP JSON."""

    # Sequential within the response (assigned by OPTotalsService).
    id = serializers.IntegerField()
    code = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    work_center_id = serializers.IntegerField()
    origin = serializers.CharField()
    origin_id = serializers.IntegerField()
    core_module_id = serializers.IntegerField(allow_null=True)
    first_start = serializers.DateTimeField(allow_null=True)
    last_end = serializers.DateTimeField(allow_null=True)

    documents_count = serializers.IntegerField()
    documents = WorkCenterDocumentSerializer(many=True)
