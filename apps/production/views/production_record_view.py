from decimal import Decimal, InvalidOperation

from apps.production.models import ProductionRecord, ReferenceSam, SkuItemLocal
from apps.production.serializers import ProductionRecordSerializer
from apps.production.views.op_record_view import OpRecordViewSet


class ProductionRecordViewSet(OpRecordViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer
    module_type = 'production'

    def get_batch_efficiency_lines(self, records) -> list:
        """SAM per record: sku_rowid -> SkuItemLocal.rowid_item -> ReferenceSam."""
        def dec(value):
            try:
                return float(Decimal(str(value or 0)))
            except InvalidOperation:
                return 0.0

        sku_rowids = {r.get('sku_rowid') for r in records if isinstance(r, dict)}
        rowid_item_by_sku = dict(
            SkuItemLocal.objects.filter(rowid__in=[x for x in sku_rowids if x is not None])
            .values_list('rowid', 'rowid_item')
        )
        sam_by_item = dict(
            ReferenceSam.objects.filter(rowid_item__in=set(rowid_item_by_sku.values()))
            .values_list('rowid_item', 'sam')
        )
        lines = []
        for r in records:
            completed = dec(r.get('completed_quantity'))
            sam = sam_by_item.get(rowid_item_by_sku.get(r.get('sku_rowid')))
            lines.append({
                'sam': float(sam or 0),
                'completed': completed,
                'total': completed + dec(r.get('scrap_quantity')) + dec(r.get('rejected_quantity')),
            })
        return lines
