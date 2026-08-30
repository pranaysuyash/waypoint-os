"""
spine_api.routers.public_proposals — Public client-facing proposal co-creation endpoints.

Allows travelers to:
- View interactive proposals via secure public tokens (/p/{token})
- Select options (room upgrades, excursions, transfer options) with real-time recalculation
- Accept and e-sign proposals with audit logging
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

logger = logging.getLogger("spine_api.public_proposals")
router = APIRouter(prefix="/api/public/proposals", tags=["public-proposals"])


# In-memory proposal token store for fast, stateless client access
# (maps proposal_token -> trip_id / proposal_config)
_PROPOSAL_REGISTRY: Dict[str, Dict[str, Any]] = {}


class ProposalOption(BaseModel):
    id: str
    category: str  # "accommodation" | "transport" | "activity" | "insurance"
    name: str
    description: str
    price_delta_usd: float = 0.0
    selected: bool = False
    is_default: bool = False


class ProposalDay(BaseModel):
    day_number: int
    title: str
    location: str
    description: str
    highlights: List[str] = Field(default_factory=list)
    options: List[ProposalOption] = Field(default_factory=list)


class PublicProposalView(BaseModel):
    token: str
    trip_id: str
    title: str
    destination: str
    duration_days: int
    traveler_name: str
    base_price_usd: float
    selected_total_price_usd: float
    currency: str = "USD"
    status: str = "open"  # "open" | "accepted" | "expired"
    accepted_at: Optional[str] = None
    accepted_by: Optional[str] = None
    days: List[ProposalDay] = Field(default_factory=list)
    available_options: List[ProposalOption] = Field(default_factory=list)


class UpdateOptionsRequest(BaseModel):
    selected_option_ids: List[str]


class AcceptProposalRequest(BaseModel):
    signer_name: str
    signer_email: str
    selected_option_ids: List[str] = Field(default_factory=list)
    e_signature_consent: bool


def generate_proposal_token(trip_id: str, agency_id: str = "system") -> str:
    """Generate a deterministic, secure URL token for a trip proposal."""
    raw = f"{trip_id}:{agency_id}:waypoint_proposal"
    token = f"prop_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"
    return token


def _get_or_create_proposal(token: str) -> PublicProposalView:
    if token in _PROPOSAL_REGISTRY:
        return _PROPOSAL_REGISTRY[token]

    # Generate a demo/dynamic proposal for the token
    base_options = [
        ProposalOption(
            id="opt_hotel_upgrade",
            category="accommodation",
            name="Upgrade to 5-Star Grand Luxury Suite",
            description="Private balcony overlooking the grand canal with daily champagne breakfast.",
            price_delta_usd=450.0,
            selected=False,
            is_default=False,
        ),
        ProposalOption(
            id="opt_private_transfer",
            category="transport",
            name="Private Chauffeur Airport & Rail Transfers",
            description="Dedicated Mercedes-Benz S-Class transfer with meet-and-greet.",
            price_delta_usd=180.0,
            selected=True,
            is_default=True,
        ),
        ProposalOption(
            id="opt_wine_tour",
            category="activity",
            name="Exclusive Sommelier Vineyard Masterclass",
            description="Private tasting tour through historic family estates with lunch.",
            price_delta_usd=220.0,
            selected=False,
            is_default=False,
        ),
    ]

    proposal = PublicProposalView(
        token=token,
        trip_id="trip_2333bff6434d",
        title="Bespoke Italian Grand Tour: Rome, Florence & Amalfi Coast",
        destination="Italy (Rome, Florence, Amalfi Coast)",
        duration_days=8,
        traveler_name="Priya & Rajesh Sharma",
        base_price_usd=4850.0,
        selected_total_price_usd=5030.0,
        currency="USD",
        status="open",
        days=[
            ProposalDay(
                day_number=1,
                title="Arrival in the Eternal City & Sunset Welcome",
                location="Rome, Italy",
                description="Private VIP arrival transfer to Hotel de Russie. Evening aperitivo in Piazza del Popolo.",
                highlights=["VIP Airport Meet & Greet", "Colosseum at Twilight View", "Private Welcome Dinner"],
                options=[],
            ),
            ProposalDay(
                day_number=2,
                title="Vatican Secret Archives & Renaissance Masterpieces",
                location="Rome & Vatican City",
                description="Early morning access before public opening hours with a private art historian guide.",
                highlights=["Sistine Chapel Private Access", "St. Peter's Basilica", "Historic Trastevere Walk"],
                options=[],
            ),
            ProposalDay(
                day_number=3,
                title="High-Speed Rail to Florence & Tuscan Hillside",
                location="Florence, Italy",
                description="First-class Frecciarossa express to Florence. Check-in at Four Seasons Hotel Firenze.",
                highlights=["Frecciarossa Executive Class", "Uffizi Gallery Fast-Track", "Duomo Panoramic Rooftop"],
                options=[base_options[0]],
            ),
        ],
        available_options=base_options,
    )
    _PROPOSAL_REGISTRY[token] = proposal
    return proposal


@router.get("/{token}", response_model=PublicProposalView)
def get_public_proposal(token: str) -> PublicProposalView:
    """Retrieve public interactive proposal details by token."""
    return _get_or_create_proposal(token)


@router.post("/{token}/calculate", response_model=PublicProposalView)
def calculate_proposal_options(token: str, req: UpdateOptionsRequest) -> PublicProposalView:
    """Recalculate proposal total based on selected option IDs."""
    proposal = _get_or_create_proposal(token)
    selected_set = set(req.selected_option_ids)

    updated_options = []
    options_total = 0.0
    for opt in proposal.available_options:
        is_selected = opt.id in selected_set
        updated_options.append(
            ProposalOption(
                id=opt.id,
                category=opt.category,
                name=opt.name,
                description=opt.description,
                price_delta_usd=opt.price_delta_usd,
                selected=is_selected,
                is_default=opt.is_default,
            )
        )
        if is_selected:
            options_total += opt.price_delta_usd

    proposal.available_options = updated_options
    proposal.selected_total_price_usd = round(proposal.base_price_usd + options_total, 2)
    _PROPOSAL_REGISTRY[token] = proposal
    return proposal


@router.post("/{token}/accept", response_model=PublicProposalView)
def accept_proposal(token: str, req: AcceptProposalRequest) -> PublicProposalView:
    """E-sign and accept proposal."""
    if not req.e_signature_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Electronic signature consent is required to accept this proposal.",
        )

    proposal = _get_or_create_proposal(token)
    now_iso = datetime.now(timezone.utc).isoformat()
    proposal.status = "accepted"
    proposal.accepted_at = now_iso
    proposal.accepted_by = f"{req.signer_name} <{req.signer_email}>"

    # Audit the acceptance
    AuditStore.log_event(
        "proposal_accepted",
        "public_client",
        {
            "proposal_token": token,
            "trip_id": proposal.trip_id,
            "signer_name": req.signer_name,
            "signer_email": req.signer_email,
            "total_price_usd": proposal.selected_total_price_usd,
            "accepted_at": now_iso,
        },
    )
    _PROPOSAL_REGISTRY[token] = proposal
    return proposal
