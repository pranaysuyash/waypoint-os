"""
src/briefing/pdf_renderer.py — Pre-Departure Briefing PDF Renderer.

Converts a ``PreDepartureBriefingPacket`` (or a list of packets for all three
D-7/D-3/D-1 stages) into a professionally formatted PDF using reportlab.
No system binary dependencies — reportlab is pure Python.

Design principles:
- Every PDF is deterministically reproducible from the same input (content-
  addressed; timestamps are UTC and come from the caller, not from the system
  clock inside the renderer).
- The renderer is isolated from the cadence engine and HTTP layer so it can
  be tested independently.
"""

from __future__ import annotations

import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.briefing.pre_departure_cadence import PreDepartureBriefingPacket

# Brand palette
_BRAND_PRIMARY = colors.HexColor("#1B4F72")   # deep navy
_BRAND_ACCENT = colors.HexColor("#2ECC71")    # waypoint green
_BRAND_LIGHT = colors.HexColor("#EBF5FB")     # soft blue tint
_GREY = colors.HexColor("#7F8C8D")

STAGE_LABELS = {
    "D_MINUS_7": "7 Days Before Departure",
    "D_MINUS_3": "3 Days Before Departure",
    "D_MINUS_1": "Day Before Departure",
}


def _build_styles() -> dict:
    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontSize=22,
            fontName="Helvetica-Bold",
            textColor=_BRAND_PRIMARY,
            spaceAfter=6,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontSize=12,
            fontName="Helvetica",
            textColor=_GREY,
            spaceAfter=12,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontSize=14,
            fontName="Helvetica-Bold",
            textColor=colors.white,
            backColor=_BRAND_PRIMARY,
            borderPad=4,
            spaceAfter=6,
            leftIndent=4,
        ),
        "stage_label": ParagraphStyle(
            "stage_label",
            fontSize=10,
            fontName="Helvetica-BoldOblique",
            textColor=_BRAND_ACCENT,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10,
            fontName="Helvetica",
            textColor=colors.black,
            spaceAfter=4,
            leftIndent=8,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontSize=10,
            fontName="Helvetica",
            textColor=colors.black,
            bulletText="•",
            bulletIndent=8,
            leftIndent=20,
            spaceAfter=3,
        ),
        "action": ParagraphStyle(
            "action",
            fontSize=10,
            fontName="Helvetica",
            textColor=_BRAND_PRIMARY,
            bulletText="☐",
            bulletIndent=8,
            leftIndent=20,
            spaceAfter=3,
        ),
        "emergency_key": ParagraphStyle(
            "emergency_key",
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=colors.black,
        ),
        "emergency_val": ParagraphStyle(
            "emergency_val",
            fontSize=10,
            fontName="Helvetica",
            textColor=_GREY,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontSize=8,
            fontName="Helvetica-Oblique",
            textColor=_GREY,
            alignment=1,  # center
        ),
    }
    return styles


def _section(title: str, styles: dict) -> list:
    return [
        Spacer(1, 0.3 * cm),
        Paragraph(f"  {title}", styles["section_header"]),
        Spacer(1, 0.2 * cm),
    ]


def _packet_to_flowables(packet: PreDepartureBriefingPacket, styles: dict) -> list:
    """Convert one briefing packet into a list of reportlab Flowables."""
    els = []
    stage_label = STAGE_LABELS.get(packet.stage.value, packet.stage.value)

    els.append(Paragraph(stage_label, styles["stage_label"]))
    els.append(Paragraph(packet.headline, styles["cover_sub"]))
    els.append(HRFlowable(width="100%", thickness=1, color=_BRAND_ACCENT, spaceAfter=8))

    # Key Highlights
    els += _section("Key Highlights", styles)
    for h in packet.key_highlights:
        els.append(Paragraph(h, styles["bullet"]))

    # Action Checklist
    els += _section("Action Checklist", styles)
    for a in packet.action_items:
        els.append(Paragraph(a, styles["action"]))

    # Emergency Contacts
    if packet.emergency_contacts:
        els += _section("24/7 Emergency Contacts", styles)
        table_data = [
            [
                Paragraph(k, styles["emergency_key"]),
                Paragraph(v, styles["emergency_val"]),
            ]
            for k, v in packet.emergency_contacts.items()
        ]
        t = Table(table_data, colWidths=[8 * cm, 8 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), _BRAND_LIGHT),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, _BRAND_LIGHT]),
                    ("GRID", (0, 0), (-1, -1), 0.5, _GREY),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        els.append(t)

    els.append(Spacer(1, 0.5 * cm))
    return els


def render_briefing_pdf(packets: List[PreDepartureBriefingPacket]) -> bytes:
    """Render one or more ``PreDepartureBriefingPacket``s into a PDF byte string.

    Args:
        packets: Ordered list of packets (typically D-7, D-3, D-1 for a full bundle).

    Returns:
        Raw PDF bytes suitable for streaming as ``application/pdf``.
    """
    if not packets:
        raise ValueError("At least one PreDepartureBriefingPacket is required.")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Pre-Departure Briefing — {packets[0].destination}",
        author="Waypoint OS Concierge",
    )

    styles = _build_styles()
    story = []

    # Cover section
    first = packets[0]
    story.append(Paragraph("✈  Pre-Departure Travel Briefing", styles["cover_title"]))
    story.append(
        Paragraph(
            f"Trip: {first.trip_id} · Traveler: {first.traveler_name} · Destination: {first.destination}",
            styles["cover_sub"],
        )
    )
    story.append(Paragraph(f"Departure: {first.departure_date}", styles["cover_sub"]))
    story.append(HRFlowable(width="100%", thickness=2, color=_BRAND_PRIMARY, spaceAfter=12))

    for packet in packets:
        story.extend(_packet_to_flowables(packet, styles))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "Waypoint OS · Reality-tier: deterministic_preview · Not a live flight status document",
            styles["footer"],
        )
    )

    doc.build(story)
    return buf.getvalue()
