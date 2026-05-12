from rest_framework import serializers
from apps.production.models.sku_item_local import SkuItemLocal

_REFERENCE_STR_FIELDS = [
    "reference", "description", "inv_type", "inventory_unit", "order_unit",
    "packing_unit", "sku_status", "brand", "line", "group", "subgroup",
    "classification", "sewing", "print_design", "license", "collection",
    "world", "channel", "promotion", "priority", "pieces_per_set",
]


class SkuItemLocalSerializer(serializers.ModelSerializer):

    sam_value = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True, allow_null=True)

    class Meta:
        model = SkuItemLocal
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        str_fields = ["barcode", "size", "color", "size_key"] + _REFERENCE_STR_FIELDS
        for field in str_fields:
            if data.get(field):
                data[field] = data[field].strip()
        return data


class SkuItemReferenceSerializer(serializers.Serializer):
    rowid_item         = serializers.IntegerField()
    reference          = serializers.CharField()
    description        = serializers.CharField()
    inv_type           = serializers.CharField(allow_null=True)
    inventory_unit     = serializers.CharField(allow_null=True)
    order_unit         = serializers.CharField(allow_null=True)
    packing_unit       = serializers.CharField(allow_null=True)
    replenishment_time = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    lot_size           = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    safety_stock       = serializers.DecimalField(max_digits=14, decimal_places=4, allow_null=True)
    status             = serializers.IntegerField(allow_null=True)
    sku_status         = serializers.CharField(allow_null=True)
    cost               = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    suggested_price    = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    brand              = serializers.CharField(allow_null=True)
    line               = serializers.CharField(allow_null=True)
    group              = serializers.CharField(allow_null=True)
    subgroup           = serializers.CharField(allow_null=True)
    classification     = serializers.CharField(allow_null=True)
    sewing             = serializers.CharField(allow_null=True)
    print_design       = serializers.CharField(allow_null=True)
    license            = serializers.CharField(allow_null=True)
    collection         = serializers.CharField(allow_null=True)
    world              = serializers.CharField(allow_null=True)
    channel            = serializers.CharField(allow_null=True)
    promotion          = serializers.CharField(allow_null=True)
    priority           = serializers.CharField(allow_null=True)
    pieces_per_set     = serializers.CharField(allow_null=True)
    sam_value          = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in _REFERENCE_STR_FIELDS:
            if data.get(field):
                data[field] = data[field].strip()
        return data
