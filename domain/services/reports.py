"""PDF reporting service for aggregated billing.

Generates simple PDF reports summarizing total billing over a period
using ReportLab. Periods supported: mensual (30d), trimestral (90d), anual (365d).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from sqlalchemy import select, func

from config.database import SessionLocal
from domain.models.venta import Venta


Periodo = Literal["mensual", "trimestral", "anual"]


def _period_to_delta(periodo: Periodo) -> timedelta:
    if periodo == "mensual":
        return timedelta(days=30)
    if periodo == "trimestral":
        return timedelta(days=90)
    if periodo == "anual":
        return timedelta(days=365)
    raise ValueError("Unsupported period. Use: mensual | trimestral | anual")


def generar_reporte(filename: str, periodo: Periodo = "mensual") -> None:
    """Generate a billing summary PDF for the given period.

    Parameters
    - filename: Output PDF file path.
    - periodo: One of "mensual", "trimestral", "anual".

    The report includes:
    - Title and date range
    - Total billed amount and count of sales
    - A simple table of (date, daily total) for the range, if data exists
    """
    now = datetime.utcnow()
    start = now - _period_to_delta(periodo)

    session = SessionLocal()
    try:
        # Aggregate totals for the range
        total_stmt = select(func.coalesce(func.sum(Venta.total_venta), 0.0), func.count(Venta.id)).where(
            Venta.fecha_venta >= start
        )
        total_amount, total_count = session.execute(total_stmt).one()

        # Daily totals
        daily_stmt = (
            select(func.date(Venta.fecha_venta), func.coalesce(func.sum(Venta.total_venta), 0.0))
            .where(Venta.fecha_venta >= start)
            .group_by(func.date(Venta.fecha_venta))
            .order_by(func.date(Venta.fecha_venta))
        )
        daily = session.execute(daily_stmt).all()
    finally:
        session.close()

    # Build PDF
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    title = f"Billing Report — {periodo.capitalize()}"
    date_range = f"Range: {start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')} (UTC)"
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(date_range, styles["Normal"]))
    story.append(Spacer(1, 0.6 * cm))

    summary_text = f"Total billed: <b>{total_amount:.2f}</b>  •  Sales count: <b>{total_count}</b>"
    story.append(Paragraph(summary_text, styles["Heading3"]))
    story.append(Spacer(1, 0.5 * cm))

    if daily:
        data = [["Date", "Total"]] + [[str(d), f"{amt:.2f}"] for d, amt in daily]
        table = Table(data, colWidths=[6 * cm, 6 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No sales in the selected period.", styles["Italic"]))

    doc.build(story)

