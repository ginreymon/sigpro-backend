from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.technical_sheet import TechnicalSheet
from apps.production.models.sku_item_local import SkuItemLocal


class TechnicalSheetSerializer(AuditSerializer):

    sku_info              = serializers.SerializerMethodField()
    sizes                 = serializers.SerializerMethodField()
    status_name           = serializers.CharField(source='status.name', read_only=True, allow_null=True)
    collection_local_name = serializers.SerializerMethodField()

    class Meta:
        model = TechnicalSheet
        fields = '__all__'

    def _get_sku(self, obj):
        sku_map = self.context.get('sku_map')
        if sku_map is not None:
            return sku_map.get(obj.rowid_item)
        return (
            SkuItemLocal.objects
            .filter(rowid_item=obj.rowid_item, is_deleted=False, is_active=True)
            .first()
        )

    def get_sku_info(self, obj):
        sku = self._get_sku(obj)
        if not sku:
            return None
        return {
            'id':             sku.id,
            'rowid':          sku.rowid,
            'reference':      sku.reference.strip() if sku.reference else None,
            'description':    sku.description.strip() if sku.description else None,
            'inv_type':       sku.inv_type.strip() if sku.inv_type else None,
            'brand':          sku.brand.strip() if sku.brand else None,
            'line':           sku.line.strip() if sku.line else None,
            'classification': sku.classification.strip() if sku.classification else None,
            'sewing':         sku.sewing.strip() if sku.sewing else None,
            'collection':     sku.collection.strip() if sku.collection else None,
            'group':          sku.group.strip() if sku.group else None,
            'subgroup':       sku.subgroup.strip() if sku.subgroup else None,
            'print_design':   sku.print_design.strip() if sku.print_design else None,
            'world':          sku.world.strip() if sku.world else None,
        }

    def get_sizes(self, obj):
        sizes_map = self.context.get('sizes_map')
        if sizes_map is not None:
            return sorted(sizes_map.get(obj.rowid_item, []))
        return list(
            SkuItemLocal.objects
            .filter(rowid_item=obj.rowid_item, is_deleted=False, is_active=True)
            .exclude(size__isnull=True)
            .exclude(size='')
            .values_list('size', flat=True)
            .distinct()
            .order_by('size')
        )

    def get_collection_local_name(self, obj):
        if not obj.collection_rowid:
            return None
        collection_map = self.context.get('collection_map')
        if collection_map is not None:
            c = collection_map.get(obj.collection_rowid)
            return c.name if c else None
        from apps.catalog.models.collection import Collection
        c = Collection.objects.filter(rowid=obj.collection_rowid, is_deleted=False).first()
        return c.name if c else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        sku = data.get('sku_info') or {}
        data['reference']   = sku.get('reference')
        data['description'] = sku.get('description')
        data['brand']       = sku.get('brand')
        data['collection']  = sku.get('collection')
        return data
