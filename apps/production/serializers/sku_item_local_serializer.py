from rest_framework import serializers
from apps.production.models.sku_item_local import SkuItemLocal


class SkuItemLocalSerializer(serializers.ModelSerializer):

    class Meta:
        model = SkuItemLocal
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        str_fields = [
            "barcode", "reference", "description", "size", "color",
            "inv_type", "size_key", "inventory_unit", "order_unit",
            "packing_unit", "sku_status", "brand", "line", "group",
            "subgroup", "classification", "sewing", "print_design",
            "license", "collection", "world", "channel", "promotion",
            "priority", "pieces_per_set",
        ]
        for field in str_fields:
            if data.get(field):
                data[field] = data[field].strip()
        return data
