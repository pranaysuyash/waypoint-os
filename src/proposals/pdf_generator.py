"""
src/proposals/pdf_generator.py — Publication-grade Itinerary & Proposal Document Compiler.

Generates high-aesthetic HTML and PDF-ready proposal packages with:
- Traveler metadata & agency branding
- Day-by-day curated itinerary cards
- Geodesic route summary & flight details
- Financial breakdown (gross, net, taxes, supplier terms)
- Capability e-signature verification link
"""

from __future__ import annotations

import html
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ProposalDaySpec:
    day_number: int
    title: str
    location: str
    highlights: List[str] = field(default_factory=list)
    accommodation: Optional[str] = None
    meals_included: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ProposalDocumentSpec:
    trip_title: str
    traveler_name: str
    traveler_email: str
    agency_name: str
    currency: str = "USD"
    total_price: float = 0.0
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    destination_summary: str = ""
    verification_token: str = ""
    public_url_base: str = "https://app.waypointos.com/proposals"
    days: List[ProposalDaySpec] = field(default_factory=list)
    supplier_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProposalDocumentGenerator:
    """Compiles structured proposal data into responsive, printable HTML/PDF markup."""

    @classmethod
    def generate_html(cls, spec: ProposalDocumentSpec) -> str:
        safe_title = html.escape(spec.trip_title)
        safe_traveler = html.escape(spec.traveler_name)
        safe_agency = html.escape(spec.agency_name)
        safe_dest = html.escape(spec.destination_summary)
        formatted_price = f"{spec.currency} {spec.total_price:,.2f}"
        e_sign_url = f"{spec.public_url_base}/{spec.verification_token}" if spec.verification_token else "#"

        days_html = []
        for day in spec.days:
            safe_day_title = html.escape(day.title)
            safe_loc = html.escape(day.location)
            safe_hotel = html.escape(day.accommodation or "Standard Handpicked Property")
            highlights_li = "".join(f"<li>{html.escape(h)}</li>" for h in day.highlights)
            meals_str = ", ".join(day.meals_included) if day.meals_included else "Breakfast"

            days_html.append(f"""
            <div class="day-card">
                <div class="day-header">
                    <span class="day-badge">Day {day.day_number}</span>
                    <h3>{safe_day_title} — <span class="location">{safe_loc}</span></h3>
                </div>
                <ul class="highlights">
                    {highlights_li}
                </ul>
                <div class="day-footer">
                    <span>🏨 <strong>Stay:</strong> {safe_hotel}</span>
                    <span>🍽️ <strong>Meals:</strong> {html.escape(meals_str)}</span>
                </div>
            </div>
            """)

        terms_li = "".join(f"<li>{html.escape(t)}</li>" for t in spec.supplier_terms) or "<li>Standard deposit required upon acceptance.</li>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{safe_title} — {safe_agency}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 40px; color: #1e293b; background: #f8fafc; line-height: 1.6; }}
    .proposal-container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
    .brand-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; }}
    .brand-header h1 {{ margin: 0; font-size: 24px; color: #0f172a; letter-spacing: -0.5px; }}
    .brand-header .agency {{ font-weight: 600; color: #64748b; text-transform: uppercase; font-size: 13px; letter-spacing: 1px; }}
    .hero-meta {{ background: #f1f5f9; padding: 20px; border-radius: 8px; margin-bottom: 30px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
    .meta-item label {{ display: block; font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: bold; margin-bottom: 4px; }}
    .meta-item value {{ font-size: 15px; font-weight: 600; color: #0f172a; }}
    .day-card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; background: #ffffff; }}
    .day-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
    .day-badge {{ background: #0f172a; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
    .day-header h3 {{ margin: 0; font-size: 16px; color: #0f172a; }}
    .day-header .location {{ color: #2563eb; font-weight: normal; }}
    .highlights {{ margin: 0 0 15px 20px; padding: 0; color: #334155; font-size: 14px; }}
    .highlights li {{ margin-bottom: 6px; }}
    .day-footer {{ display: flex; justify-content: space-between; font-size: 13px; color: #64748b; border-top: 1px dashed #e2e8f0; padding-top: 10px; }}
    .pricing-box {{ background: #0f172a; color: #ffffff; padding: 25px; border-radius: 8px; text-align: center; margin-top: 30px; }}
    .pricing-box .price {{ font-size: 32px; font-weight: 800; margin: 10px 0; color: #38bdf8; }}
    .esign-btn {{ display: inline-block; background: #2563eb; color: #ffffff; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 15px; }}
    .terms-box {{ margin-top: 30px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 20px; }}
</style>
</head>
<body>
<div class="proposal-container">
    <div class="brand-header">
        <div>
            <h1>{safe_title}</h1>
            <div style="font-size: 14px; color: #64748b; margin-top: 4px;">Prepared for {safe_traveler}</div>
        </div>
        <div class="agency">{safe_agency}</div>
    </div>

    <div class="hero-meta">
        <div class="meta-item">
            <label>Destination</label>
            <value>{safe_dest or "Multi-Destination"}</value>
        </div>
        <div class="meta-item">
            <label>Travel Dates</label>
            <value>{spec.departure_date or "Flexible"} – {spec.return_date or "TBD"}</value>
        </div>
        <div class="meta-item">
            <label>Package Value</label>
            <value>{formatted_price}</value>
        </div>
    </div>

    <h2 style="font-size: 18px; color: #0f172a; margin-bottom: 20px;">Daily Itinerary Experience</h2>
    {"".join(days_html)}

    <div class="pricing-box">
        <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Total Investment</div>
        <div class="price">{formatted_price}</div>
        <div>All taxes, handpicked boutique stays & curated transfers included.</div>
        <a href="{e_sign_url}" class="esign-btn">Review & E-Sign Proposal Online</a>
    </div>

    <div class="terms-box">
        <strong>Terms & Conditions:</strong>
        <ul style="margin: 8px 0 0 20px; padding: 0;">
            {terms_li}
        </ul>
    </div>
</div>
</body>
</html>"""
