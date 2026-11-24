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

from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

# Same header look as the other sheets of the report (see efficiency_report_export.py).
_HEADER_FILL = PatternFill("solid", fgColor="1F3864")
_HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
_HEADER_BORDER_SIDE = Side(style="thin", color="D9D9D9")
_HEADER_BORDER = Border(left=_HEADER_BORDER_SIDE, right=_HEADER_BORDER_SIDE,
                        top=_HEADER_BORDER_SIDE, bottom=_HEADER_BORDER_SIDE)


# Body cells look like the "Eficiencia" / "Detalle registros" ones: size 10, thin grey border,
# numbers centred and text left. Spilled cells cannot be styled one by one, so the font and
# alignment go on the columns and the border on a conditional format that only marks filled cells.
_CELL_FONT = Font(size=10)
_CENTER = Alignment(horizontal="center", vertical="center")
_LEFT = Alignment(horizontal="left", vertical="center")
_HEADER_ROW_HEIGHT = 22


def _style_column(ws, letter: str, alignment, number_format: str = "General"):
    dim = ws.column_dimensions[letter]
    dim.font, dim.alignment, dim.number_format = _CELL_FONT, alignment, number_format


def _style_anchor(cell, alignment, number_format: str = "General"):
    cell.font, cell.alignment, cell.number_format = _CELL_FONT, alignment, number_format


def _border_filled_cells(ws, area: str):
    top_left = area.split(":")[0]
    ws.conditional_formatting.add(area, FormulaRule(formula=[f'LEN({top_left})>0'], border=_HEADER_BORDER))


def _style_header_cell(cell):
    cell.font, cell.fill, cell.border = _HEADER_FONT, _HEADER_FILL, _HEADER_BORDER
    cell.alignment = Alignment(horizontal="center", vertical="center")


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

# X = spilled range of the list sheet; A2# / B1# = spilled ranges of the matrix sheet.
_MATRIX_DATES = '=IFERROR(TRANSPOSE(SORT(UNIQUE(INDEX(X,0,1)))),"")'
_MATRIX_NAMES = '=IFERROR(SORT(UNIQUE(INDEX(X,0,2))),"")'
_MATRIX_VALUES = '=IFERROR(AVERAGEIFS(INDEX(X,0,4),INDEX(X,0,2),A2#,INDEX(X,0,1),B1#),"")'

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

    # List: one row per (day, employee, module)
    ls = wb.create_sheet(LIST_SHEET, index=wb.sheetnames.index(efficiency_ws.title) + 1)
    for col, label in enumerate(("Fecha", "Empleado", "Módulo", "Eficiencia (%)"), start=1):
        _style_header_cell(ls.cell(row=1, column=col, value=label))
    _put(ls, "A2", _LIST_FORMULA.format(
        fech=rng(HEADER_START), emps=rng(HEADER_EMPLOYEES), mods=rng(HEADER_MODULE), efs=rng(HEADER_EFFICIENCY),
    ), dynamic)
    ls.row_dimensions[1].height = _HEADER_ROW_HEIGHT
    for letter, alignment, number_format in (
        ("A", _CENTER, "dd/mm/yyyy"), ("B", _LEFT, "General"), ("C", _LEFT, "General"), ("D", _CENTER, "0.0"),
    ):
        _style_column(ls, letter, alignment, number_format)
        _style_anchor(ls[f"{letter}2"], alignment, number_format)  # a cell's own style overrides its column's
    for letter, width in (("A", 14), ("B", 44), ("C", 22), ("D", 16)):
        ls.column_dimensions[letter].width = width
    _border_filled_cells(ls, f"A2:D{n}")
    ls.freeze_panes = "A2"

    # Matrix: employee x day
    ms = wb.create_sheet(MATRIX_SHEET, index=wb.sheetnames.index(LIST_SHEET) + 1)
    ms["A1"] = "Empleado \\ Fecha"
    _style_header_cell(ms["A1"])

    def sub(formula):
        return (formula.replace("INDEX(X,", f"INDEX({_spill_ref(LIST_SHEET, 'A2')},")
                       .replace("A2#", _spill_ref(MATRIX_SHEET, "A2"))
                       .replace("B1#", _spill_ref(MATRIX_SHEET, "B1")))

    _put(ms, "B1", sub(_MATRIX_DATES), dynamic)
    _put(ms, "A2", sub(_MATRIX_NAMES), dynamic)
    _put(ms, "B2", sub(_MATRIX_VALUES), dynamic)
    ms.column_dimensions["A"].width = 44
    ms.row_dimensions[1].height = _HEADER_ROW_HEIGHT
    _style_column(ms, "A", _LEFT)
    _style_anchor(ms["A2"], _LEFT)
    for col in range(2, _MATRIX_MAX_COLUMNS + 2):
        letter = get_column_letter(col)
        _style_column(ms, letter, _CENTER, "0.0")
        ms[f"{letter}1"].number_format = "yyyy-mm-dd"
        _style_header_cell(ms[f"{letter}1"])  # spilled day headers keep the header look
    _style_anchor(ms["B2"], _CENTER, "0.0")
    _border_filled_cells(ms, f"A2:{get_column_letter(_MATRIX_MAX_COLUMNS + 1)}{n}")
    ms.freeze_panes = "B2"

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
