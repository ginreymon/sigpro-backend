"""
Motor genérico para construir líneas de ancho fijo ("plano") de SIESA a
partir de una definición declarativa de campos — igual a como SIESA publica
sus propios `.xlsm` de referencia (columnas NOMBRE/TIPO/OBSERVACIONES/OBL/
INICIO/TAMAÑO/TOTAL, ya verificado byte a byte contra `TP.xlsm` para TEP).

Separado a propósito de `apps.integration.services.siesa_webservice_client`:
este módulo no sabe nada de XML ni de red, solo arma el string de ancho fijo.
Cada tipo de documento (TEP, y a futuro Terceros/Requisiciones si se migran
del Excel al backend) declara su propio `RecordLayout` en su propio archivo
(ver `apps/integration/builders/tep.py`) y usa `build_line` para armar cada
`<Linea>`, que luego se le pasa a `send_flat_file_lines`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

FieldType = Literal["alpha", "numeric", "quantity", "time", "date", "const"]


@dataclass(frozen=True)
class FieldSpec:
    """Un campo dentro de un registro de ancho fijo, tal como aparece en el
    plano de SIESA (columnas NOMBRE / TIPO / OBSERVACIONES / OBL / TAMAÑO)."""

    name: str
    width: int
    type: FieldType = "alpha"
    required: bool | Literal["dep"] = False
    description: str = ""
    const_value: str | None = None  # solo para type="const" (bloques de control, reservados)
    decimals: int = 4               # solo para type="quantity" / "time"
    default: object = None


@dataclass(frozen=True)
class RecordLayout:
    """Un tipo de registro completo (una `<Linea>`), ej. Encabezado TEP (450)
    o Detalle TEP (880)."""

    name: str
    fields: tuple[FieldSpec, ...]

    @property
    def total_width(self) -> int:
        return sum(f.width for f in self.fields)


def _format_alpha(value, width: int) -> str:
    return str(value if value is not None else "")[:width].ljust(width)


def _format_numeric(value, width: int) -> str:
    return str(int(value or 0)).zfill(width)[-width:]


def _format_quantity(value, width: int, decimals: int) -> str:
    """Punto decimal literal (igual que `_format_time`): 15 enteros + '.' +
    4 decimales = 20 caracteres. SIESA NO aplica decimales implicitos a este
    campo: enviar `1143` como digitos escalados (11430000) lo cargaba como
    11.430.000,0000."""
    return f"{float(value or 0):0{width}.{decimals}f}"[-width:]


def _format_time(value, width: int, decimals: int) -> str:
    """Formato HH.MM (con punto literal) si hay valor; puros ceros sin punto
    si `value` es None (no aplica)."""
    if value is None:
        return "0" * width
    return f"{float(value):0{width}.{decimals}f}"[-width:]


def _format_date(value: dt.date | None, width: int) -> str:
    return (value or dt.date.today()).strftime("%Y%m%d")[:width].ljust(width)


_FORMATTERS = {
    "alpha": lambda field, value: _format_alpha(value, field.width),
    "numeric": lambda field, value: _format_numeric(value, field.width),
    "quantity": lambda field, value: _format_quantity(value, field.width, field.decimals),
    "time": lambda field, value: _format_time(value, field.width, field.decimals),
    "date": lambda field, value: _format_date(value, field.width),
}


def build_line(layout: RecordLayout, sequence: int, values: dict) -> str:
    """Construye una `<Linea>` de ancho fijo a partir de un layout y un dict
    de valores por nombre de campo. Campos `type="const"` (bloques de
    control, secciones reservadas/en blanco) se toman de `const_value` y no
    necesitan valor. El primer campo del layout se trata como la secuencia
    de línea dentro de `<Datos>` (consecutivo global, lo recalcula quien
    arma el documento completo — ver `apps/integration/builders/tep.py`)."""
    parts = []
    for i, field in enumerate(layout.fields):
        if i == 0:
            parts.append(_format_numeric(sequence, field.width))
            continue
        if field.type == "const":
            parts.append(_format_alpha(field.const_value, field.width))
            continue
        value = values.get(field.name, field.default)
        parts.append(_FORMATTERS[field.type](field, value))

    line = "".join(parts)
    assert len(line) == layout.total_width, (
        f"layout '{layout.name}': línea de {len(line)} caracteres, "
        f"se esperaban {layout.total_width}"
    )
    return line
