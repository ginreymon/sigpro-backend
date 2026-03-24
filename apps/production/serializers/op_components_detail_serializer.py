from rest_framework import serializers


class OPComponentsDetailSerializer(serializers.Serializer):

    rowId = serializers.IntegerField(source="RowID")
    documentId = serializers.CharField(source="Id_Doc")
    documentType = serializers.CharField(source="Tipo_Doc")
    documentNumber = serializers.IntegerField(source="Numero_Doc")

    group = serializers.CharField(source="Grupo", required=False, allow_null=True, allow_blank=True)
    groupId = serializers.IntegerField(source="Grupo_Id", required=False)

    componentRef = serializers.CharField(source="Ref_Componente")
    description = serializers.CharField(source="Descripcion")
    productRef = serializers.CharField(source="Ref_Producto")
    planId = serializers.CharField(source="Id_Plan")

    extra1 = serializers.CharField(
        source="Ext1_Detalle_Componente",
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    extra2 = serializers.CharField(
        source="Ext2_Detalle_Componente",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
