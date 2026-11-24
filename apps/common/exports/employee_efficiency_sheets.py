"""
Per-employee efficiency sheets of the efficiency report Excel (Confección and Estampación).

Both sheets hold Excel dynamic-array formulas that depend only on the "Eficiencia"
sheet: no value is calculated in Python. openpyxl cannot flag a cell as a dynamic
array (spill), so the cells are written as array formulas and `inject_dynamic_array_metadata`
adds the metadata part Excel 365 needs to treat them as spilling formulas (no "@").
"""
import io
import re
import zipfile

from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

EFFICIENCY_SHEET = "Eficiencia"
LIST_SHEET = "Eficiencia por Empleado"
MATRIX_SHEET = "Eficiencia Empleado x Día"

HEADER_START, HEADER_MODULE, HEADER_EMPLOYEES, HEADER_EFFICIENCY = (
    "Inicio Jornada", "Módulo", "Operarios", "Eficiencia (%)",
)

EMPLOYEE_SHEET_DESCRIPTIONS = {
    "Fecha": "Día de Inicio Jornada, sin hora.",
    "Empleado": "Un operario de la columna Operarios (NOMBRE DOCUMENTO), una fila por módulo.",
    "Empleado \\ Fecha": (
        "Promedio de Eficiencia (%) del empleado en el día entre los módulos donde trabajó; vacío si no trabajó."
    ),
}

_FUTURE_FUNCTIONS = (
    "LET", "DROP", "REDUCE", "HSTACK", "VSTACK", "SEQUENCE", "LAMBDA", "TEXTSPLIT", "EXPAND",
    "UNIQUE", "SORT", "ANCHORARRAY",
)
_LET_NAMES = ("fech", "emps", "mods", "efs", "acc", "i", "ini", "lista", "dia", "nom", "cant")

_LIST_FORMULA = (
    '=IFERROR(DROP(LET(fech,{fech},emps,{emps},mods,{mods},efs,{efs},'
    'REDUCE(HSTACK("","","",""),SEQUENCE(ROWS(fech)),LAMBDA(acc,i,'
    'LET(ini,INDEX(fech,i),lista,INDEX(emps,i),'
    'IF(OR(ini="",lista=""),acc,'
    'LET(dia,IF(ISNUMBER(ini),INT(ini),DATE(LEFT(ini,4),MID(ini,6,2),MID(ini,9,2))),'
    'nom,UNIQUE(TRIM(TEXTSPLIT(lista,,";",TRUE))),cant,ROWS(nom),'
    'VSTACK(acc,HSTACK(EXPAND(dia,cant,,dia),nom,EXPAND(INDEX(mods,i),cant,,INDEX(mods,i)),'
    'EXPAND(INDEX(efs,i),cant,,INDEX(efs,i)))))))))),1),"")'
)

# X = spilled range of the list sheet; A4# / B3# = spilled ranges of the matrix sheet.
_MATRIX_DATES = '=IFERROR(TRANSPOSE(SORT(UNIQUE(INDEX(X,0,1)))),"")'
_MATRIX_NAMES = '=IFERROR(SORT(UNIQUE(INDEX(X,0,2))),"")'
_MATRIX_VALUES = '=IFERROR(AVERAGEIFS(INDEX(X,0,4),INDEX(X,0,2),A4#,INDEX(X,0,1),B3#),"")'

_MATRIX_MAX_COLUMNS = 400  # day columns formatted ahead of the spill (a period is at most about a year)


def _excel(formula: str) -> str:
    """Prefix the future functions (_xlfn.) and LET/LAMBDA names (_xlpm.) the file format requires."""
    for fn in _FUTURE_FUNCTIONS:
        formula = re.sub(rf"\b{fn}\(", f"_xlfn.{fn}(", formula)
    for name in _LET_NAMES:
        formula = re.sub(rf"(?<![\w.!'$]){name}(?![\w(])", f"_xlpm.{name}", formula)
    return formula


def _spill_ref(sheet: str, cell: str) -> str:
    return f"ANCHORARRAY('{sheet}'!{cell})"


def _header_columns(ws) -> dict[str, str]:
    return {c.value: c.column_letter for c in ws[1] if c.value}


def _put(ws, cell: str, formula: str, dynamic: list):
    ws[cell] = ArrayFormula(cell, _excel(formula))
    dynamic.append((ws.title, cell))


def add_employee_efficiency_sheets(wb, efficiency_ws, data_rows: int) -> list[tuple[str, str]]:
    """Insert the two sheets right after "Eficiencia". Returns the dynamic-array cells (sheet, ref) for
    `inject_dynamic_array_metadata`. Does nothing if "Eficiencia" lacks a required column."""
    columns = _header_columns(efficiency_ws)
    needed = (HEADER_START, HEADER_MODULE, HEADER_EMPLOYEES, HEADER_EFFICIENCY)
    if any(h not in columns for h in needed):
        return []

    n = max(1000, data_rows + 500)

    def rng(header):
        return f"{EFFICIENCY_SHEET}!{columns[header]}2:{columns[header]}{n}"

    dynamic: list[tuple[str, str]] = []
    bold = Font(bold=True)

    # List: one row per (day, employee, module)
    ls = wb.create_sheet(LIST_SHEET, index=wb.sheetnames.index(efficiency_ws.title) + 1)
    ls["A1"] = LIST_SHEET
    ls["A1"].font = Font(bold=True, size=14)
    for col, label in enumerate(("Fecha", "Empleado", "Módulo", "Eficiencia (%)"), start=1):
        ls.cell(row=3, column=col, value=label).font = bold
    _put(ls, "A4", _LIST_FORMULA.format(
        fech=rng(HEADER_START), emps=rng(HEADER_EMPLOYEES), mods=rng(HEADER_MODULE), efs=rng(HEADER_EFFICIENCY),
    ), dynamic)
    ls["A4"].number_format = "dd/mm/yyyy"  # the anchor cell has its own style; the rest of the spill takes the column's
    ls["D4"].number_format = "0.0"
    ls.column_dimensions["A"].number_format = "dd/mm/yyyy"
    ls.column_dimensions["D"].number_format = "0.0"
    for letter, width in (("A", 14), ("B", 44), ("C", 22), ("D", 16)):
        ls.column_dimensions[letter].width = width
    ls.freeze_panes = "A4"

    # Matrix: employee x day
    ms = wb.create_sheet(MATRIX_SHEET, index=wb.sheetnames.index(LIST_SHEET) + 1)
    ms["A1"] = MATRIX_SHEET
    ms["A1"].font = Font(bold=True, size=14)
    ms["A3"] = "Empleado \\ Fecha"
    ms["A3"].font = bold

    def sub(formula):
        return (formula.replace("INDEX(X,", f"INDEX({_spill_ref(LIST_SHEET, 'A4')},")
                       .replace("A4#", _spill_ref(MATRIX_SHEET, "A4"))
                       .replace("B3#", _spill_ref(MATRIX_SHEET, "B3")))

    _put(ms, "B3", sub(_MATRIX_DATES), dynamic)
    _put(ms, "A4", sub(_MATRIX_NAMES), dynamic)
    _put(ms, "B4", sub(_MATRIX_VALUES), dynamic)
    ms.column_dimensions["A"].width = 44
    for col in range(2, _MATRIX_MAX_COLUMNS + 2):
        letter = get_column_letter(col)
        ms.column_dimensions[letter].number_format = "0.0"
        ms[f"{letter}3"].number_format = "dd/mm"
        ms[f"{letter}3"].alignment = Alignment(horizontal="center")
    ms["A4"].number_format = "General"
    ms["B4"].number_format = "0.0"
    ms.freeze_panes = "B4"

    return dynamic


# Dynamic-array metadata: what XlsxWriter's write_dynamic_array_formula emits.
_METADATA_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<metadata xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:xda="http://schemas.microsoft.com/office/spreadsheetml/2017/dynamicarray">'
    '<metadataTypes count="1"><metadataType name="XLDAPR" minSupportedVersion="120000" copy="1" pasteAll="1" '
    'pasteValues="1" merge="1" splitFirst="1" rowColShift="1" clearFormats="1" clearComments="1" assign="1" '
    'coerce="1" cellMeta="1"/></metadataTypes>'
    '<futureMetadata name="XLDAPR" count="1"><bk><extLst><ext uri="{bdbb8cdc-fa1e-496e-a857-3c3f30c029c3}">'
    '<xda:dynamicArrayProperties fDynamic="1" fCollapsed="0"/></ext></extLst></bk></futureMetadata>'
    '<cellMetadata count="1"><bk><rc t="1" v="0"/></bk></cellMetadata></metadata>'
)
_METADATA_CONTENT_TYPE = (
    '<Override PartName="/xl/metadata.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml"/>'
)
_METADATA_REL = (
    '<Relationship Id="rIdSigproMeta" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata" Target="metadata.xml"/>'
)


def inject_dynamic_array_metadata(xlsx: bytes, sheet_names: list[str], cells: list[tuple[str, str]]) -> bytes:
    """Mark `cells` ((sheet title, ref) pairs) as dynamic-array formulas so Excel 365 spills them."""
    if not cells:
        return xlsx
    targets: dict[str, list[str]] = {}
    for title, ref in cells:
        targets.setdefault(f"xl/worksheets/sheet{sheet_names.index(title) + 1}.xml", []).append(ref)

    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(xlsx)) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename in targets:
                text = data.decode("utf-8")
                for ref in targets[item.filename]:
                    text = re.sub(rf'<c r="{ref}"', f'<c r="{ref}" cm="1"', text, count=1)
                data = text.encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                data = data.decode("utf-8").replace("</Types>", _METADATA_CONTENT_TYPE + "</Types>").encode("utf-8")
            elif item.filename == "xl/_rels/workbook.xml.rels":
                data = data.decode("utf-8").replace(
                    "</Relationships>", _METADATA_REL + "</Relationships>").encode("utf-8")
            dst.writestr(item, data)
        dst.writestr("xl/metadata.xml", _METADATA_XML)
    return out.getvalue()
