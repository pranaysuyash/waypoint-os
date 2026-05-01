from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "pranay_family_singapore_may_dummy_itinerary.pdf"


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#d7dde5"))
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, height - 18 * mm, width - doc.rightMargin, height - 18 * mm)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor("#0f172a"))
    canvas.drawString(doc.leftMargin, height - 13 * mm, "Dummy itinerary for itinerary-checker testing")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawRightString(width - doc.rightMargin, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=18 * mm,
        title="Pranay Family Singapore Dummy Itinerary",
        author="Codex",
        subject="Dummy itinerary for travel checker testing",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="HeroTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HeroSub",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1f2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Badge",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.white,
        )
    )

    story = []

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Pranay Family Singapore Trip", styles["HeroTitle"]))
    story.append(Paragraph("Late May 2026 | Dummy itinerary for checker testing", styles["HeroSub"]))
    story.append(Spacer(1, 7 * mm))

    summary_data = [
        ["Origin city", "Mumbai, India"],
        ["Trip purpose", "Family holiday / school break"],
        ["Budget", "Mid-range family comfort with activity upgrades"],
        ["Travel party", "5 travelers: Pranay family, 2 adults, 2 elders, 1 child age 3"],
        ["Trip window", "Late May 2026, 6 days / 5 nights"],
        ["Primary focus", "Universal Studios, parks, Sentosa cable car, easy family pacing"],
        ["Style", "Low-stress, kid-friendly, wheelchair-aware, flexible afternoons"],
    ]
    summary_table = Table(summary_data, colWidths=[42 * mm, 120 * mm], hAlign="LEFT")
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.4),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Family Notes", styles["Section"]))
    family_notes = [
        "Plan assumes a straightforward arrival into Singapore with airport transfer to hotel on day 1.",
        "Two elders need shorter walking loops, more rest breaks, and shade wherever possible.",
        "The 3-year-old should have one major activity per day and an easy return-to-hotel plan.",
        "Afternoons are intentionally soft so the family can reset, swim, or skip activities if needed.",
    ]
    for note in family_notes:
        story.append(Paragraph(f"- {note}", styles["BodySmall"]))
        story.append(Spacer(1, 1.6 * mm))

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Daily Plan", styles["Section"]))

    daily_plan = [
        ("Day 1", "Arrival and check-in", "Land in Singapore, hotel transfer, light dinner near the hotel, early night."),
        ("Day 2", "Gardens and bayfront", "Visit Gardens by the Bay in the morning, Marina Bay area after lunch, sunset family photos."),
        ("Day 3", "Sentosa easy day", "Sentosa cable car ride, beach time, aquarium or relaxed island activities, return before sunset."),
        ("Day 4", "Universal Studios", "Full-day Universal Studios Singapore with a midday break and kid-friendly ride pacing."),
        ("Day 5", "Parks and nature", "Zoo or Bird Paradise in the morning, park time after lunch, optional shopping or cafe stop."),
        ("Day 6", "Departure buffer", "Slow breakfast, last-minute packing, airport transfer, no heavy activities."),
    ]
    for day, title, body in daily_plan:
        block = Table(
            [[
                Paragraph(f"<b>{day}</b>", styles["BodySmall"]),
                Paragraph(f"<b>{title}</b><br/>{body}", styles["BodySmall"]),
            ]],
            colWidths=[20 * mm, 142 * mm],
        )
        block.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#dbe4ee")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#eff6ff")),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#1d4ed8")),
                ]
            )
        )
        story.append(block)
        story.append(Spacer(1, 3 * mm))

    story.append(PageBreak())
    story.append(Paragraph("Suggested Checkpoints", styles["Section"]))
    checkpoints = [
        "Prebook stroller-friendly or accessible transfer options.",
        "Keep each day to one anchor activity and one optional add-on.",
        "Schedule an afternoon cooling or rest break every day.",
        "Use flexible dining so elders and the child can eat early if needed.",
        "Leave the last evening light to reduce airport-day stress.",
    ]
    for item in checkpoints:
        story.append(Paragraph(f"- {item}", styles["BodySmall"]))
        story.append(Spacer(1, 1.6 * mm))

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Testing Notes", styles["Section"]))
    story.append(
        Paragraph(
            "This PDF is intentionally formatted as a realistic family itinerary so the public checker can parse destination, timing, and activity cues during upload tests.",
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 4 * mm))

    badge = Table(
        [[Paragraph("Dummy sample - not a real booking", styles["Badge"])]],
        colWidths=[70 * mm],
        hAlign="LEFT",
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#0f172a")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(badge)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return OUTPUT


if __name__ == "__main__":
    path = build_pdf()
    print(path)
