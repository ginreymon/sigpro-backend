from rest_framework import serializers


class OPComponentsDetailSerializer(serializers.Serializer):

    RowID = serializers.IntegerField()
    Id_Doc = serializers.CharField()
    Tipo_Doc = serializers.CharField()
    Numero_Doc = serializers.IntegerField()
    Grupo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Ref_Componente = serializers.CharField()
    Descripcion = serializers.CharField()
    Ref_Producto = serializers.CharField()
    Ext1_Detalle_Componente = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    Ext2_Detalle_Componente = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
