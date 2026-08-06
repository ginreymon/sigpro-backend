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
    "Estado_Nombre": "statusName",
    "Id_Doc": "documentId",
    "Id_Plan": "planId",
    # nested
    "Centro_Operaciones": "operationCenters",
    "Componentes": "components",
    "ColorRows": "colorRows",
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
    "SKUS": "skus",
    # tallas / totales
    "Talla": "size",
    "SKU_RowID": "skuRowId",
    "Cant_Ordenada": "orderedQty",
    "Cant_Planeada": "plannedQty",
    "Cant_Completada": "completedQty",
    "Cant_Desechos": "wasteQty",
    "Cant_Rechazos": "rejectedQty",
    "Tiene_Registros_Abiertos": "hasOpenRecords",
    "Cantidad_Base_Ruta": "baseRouteQuantity",
    "SAM": "sam",
    # clasificacion
    "Marca": "brand",
    "Linea": "line",
    "Clasificacion": "classification",
    "Confeccion": "manufacture",
    "Estampado": "print",
    "Comercial": "commercial",
    # productivity sp columns
    "total_ordenada":               "total_ordered",
    "total_planeada":               "total_planned",
    "total_completada":             "total_completed",
    "total_desechos":               "total_scrap",
    "total_rechazos":               "total_rejected",
    "total_sam_ganado":             "total_sam_earned",
    "total_segundos_productivos":   "total_productive_seconds",
    "total_segundos_pausa":         "total_break_seconds",
    "total_segundos_actividad":     "total_activity_seconds",
    "primer_record_inicio":         "first_record_start",
    "ultimo_record_fin":            "last_record_end",
    "segundos_transcurridos_turno": "elapsed_shift_seconds",
    "fecha_inicio":                 "period_start",
    "fecha_fin":                    "period_end",
    "total_segundos_disponibles":   "total_available_seconds",
    "meta_intervalo":               "interval_target",
    "meta_unidades":                "unit_target",
    "promedio_operadores":          "avg_employee_count",
    "tiempo_meta_segundos":         "total_meta_seconds",
    "promedio_sam_ponderado":       "weighted_avg_sam",
    "total_produccion":             "total_produced",
    "eficiencia":                   "efficiency",
    "modulo_id":                    "module_id",
    "turno_id":                     "shift_id",
    "ultima_fecha_trabajada":       "last_worked_date",
    "ultima_total_completada":      "last_worked_total_completed",
    "ultima_eficiencia":            "last_worked_efficiency",
    "ultima_productividad":         "last_worked_productivity",
    # fn_eficiencia_detallada / sp_reporte_eficiencia_detallada
    "cantidad_pausas":              "pause_count",
    "work_shift_start_utc":         "shift_start_utc",
    # materials sp columns
    "Referencias":                  "references",
    "Materiales":                   "materials",
    "Material":                     "materialNumber",
    "Codigo_Tela":                  "fabricCode",
    "Color_Tela":                   "fabricColor",
    "Consumo":                      "consumption",
    "Descripcion_Referencia":       "description",
    "Total":                        "total",
    "TipoDocto":                    "docType",
    "ConsecDocto":                  "docNumber",
    "OP":                           "op",
}


def translate_keys(data):
    from datetime import datetime, timezone

    if isinstance(data, list):
        return [translate_keys(item) for item in data]

    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = KEY_MAP.get(key, key)  # fallback if not mapped
            new_dict[new_key] = translate_keys(value)
        return new_dict

    if isinstance(data, datetime) and data.tzinfo is None:
        return data.replace(tzinfo=timezone.utc)

    return data

