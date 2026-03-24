KEY_MAP = {
    # root
    "RowID": "rowId",
    "Tipo_Doc": "documentType",
    "Numero_Doc": "documentNumber",
    "Referencia": "reference",
    "Ref_RowID": "referenceRowId",
    "Ref_Descripcion": "description",
    "Ref_Producto": "product",
    "Fecha_Creacion": "createdAt",
    "Destino": "destination",
    "Estado": "status",
    "Id_Doc": "documentId",
    "Id_Plan": "planId",
    # nested
    "Centro_Operaciones": "operationCenters",
    "Componentes": "components",
    "Colores": "colors",
    # centro operaciones
    "operacion": "operation",
    "centro_id": "centerId",
    "centro_nombre": "centerName",
    # componentes
    "Grupo": "group",
    "Grupo_Id": "groupId",
    "Ref_Componente": "componentRef",
    "Descripcion": "description",
    "Ext1": "extra1",
    # colores
    "Color": "color",
    "Totales": "totals",
    "Tallas": "sizes",
    # tallas / totales
    "Talla": "size",
    "SKU_RowID": "skuRowId",
    "Cant_Ordenada": "orderedQty",
    "Cant_Planeada": "plannedQty",
    "Cant_Completada": "completedQty",
    "Cant_Desechos": "wasteQty",
    "Cant_Rechazos": "rejectedQty",
}


def translate_keys(data):
    if isinstance(data, list):
        return [translate_keys(item) for item in data]

    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = KEY_MAP.get(key, key)  # fallback if not mapped
            new_dict[new_key] = translate_keys(value)
        return new_dict

    return data
