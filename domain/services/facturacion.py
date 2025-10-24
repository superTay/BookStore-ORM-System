"""Invoice generation service.

Provides a function to render a human-readable invoice for a given order
(Venta) including header, line items, and totals. Designed as a domain
service that operates on loaded ORM entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from domain.models.venta import Venta, DetalleVenta


def _fmt_currency(value: Optional[float], symbol: str = "€") -> str:
    v = float(value or 0.0)
    return f"{symbol}{v:,.2f}"


def generar_factura(pedido: Venta, currency_symbol: str = "€") -> str:
    """Generate an invoice text for a given Venta (pedido).

    Parameters
    - pedido: A Venta instance with its `detalles` collection available. Each
      `DetalleVenta` should reference a `Libro` with a `titulo` and `precio`.
    - currency_symbol: Currency symbol to use when formatting amounts (default "€").

    Returns
    - A multiline string representing the invoice.

    Notes
    - This function reads attributes only; it does not access the database.
      Ensure relationships needed (detalles -> libro) are available on `pedido`.
    """
    lines: list[str] = []

    # Header
    fecha = pedido.fecha_venta if isinstance(pedido.fecha_venta, datetime) else None
    fecha_txt = fecha.strftime("%Y-%m-%d %H:%M") if fecha else str(pedido.fecha_venta)
    cliente = pedido.cliente_nombre or "Unknown Customer"
    usuario_txt = ""
    try:
        if getattr(pedido, "usuario", None):
            usuario = pedido.usuario
            usuario_txt = f" | User: {getattr(usuario, 'nombre', '')} <{getattr(usuario, 'email', '')}>"
    except Exception:
        pass

    lines.append(f"Invoice #{pedido.id} — {fecha_txt}")
    lines.append(f"Customer: {cliente}{usuario_txt}")
    lines.append("".ljust(60, "-"))
    lines.append(f"{'Title':40} {'Qty':>5} {'Unit':>10} {'Total':>12}")
    lines.append("".ljust(60, "-"))

    # Items
    total_calc = 0.0
    for d in getattr(pedido, "detalles", []) or []:
        titulo = getattr(getattr(d, "libro", None), "titulo", "<unknown>")
        qty = int(getattr(d, "cantidad", 0) or 0)
        unit = float(getattr(getattr(d, "libro", None), "precio", 0.0) or 0.0)
        line_total = unit * qty
        total_calc += line_total
        lines.append(
            f"{titulo[:40]:40} {qty:>5} {_fmt_currency(unit, currency_symbol):>10} {_fmt_currency(line_total, currency_symbol):>12}"
        )

    lines.append("".ljust(60, "-"))
    lines.append(f"{'TOTAL:':>58} {_fmt_currency(total_calc, currency_symbol):>12}")

    # If the stored total_venta differs (rounding/manual changes), show it
    try:
        stored = float(pedido.total_venta or 0.0)
        if abs(stored - total_calc) > 1e-6:
            lines.append(f"{'Stored Total:':>58} {_fmt_currency(stored, currency_symbol):>12}")
    except Exception:
        pass

    return "\n".join(lines)

