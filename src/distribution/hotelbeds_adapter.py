"""
src/distribution/hotelbeds_adapter.py — Hotelbeds / Bedsonline Wholesale Bed-Bank Adapter.

Provides live hotel rate shopping and booking creation via the Hotelbeds API
(https://developer.hotelbeds.com/documentation/hotels/).

Authentication:
- API Key + Shared Secret → SHA-256 signature header per the Hotelbeds spec:
  ``Api-signature: SHA256(apiKey + sharedSecret + unixTimestampSeconds)``

Reality boundary: when ``HOTELBEDS_API_KEY`` / ``HOTELBEDS_SHARED_SECRET`` are
absent, the adapter returns synthetic preview inventory labeled with
``reality_tier="deterministic_preview"`` and ``provider_connected=False``.
When credentials ARE present, live API calls are made against
``https://api.test.hotelbeds.com`` (test) or ``https://api.hotelbeds.com``
(production), selected by ``HOTELBEDS_ENV=test|production``.

Missing-for-upgrade (production):
- Deposit policy handling and cancellation penalty calculation
- Static hotel content cache (hotel portfolio pre-load)
- Currency conversion via Hotelbeds /types/currencies endpoint
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from spine_api.core.reality_tier import RealityTier

logger = logging.getLogger("src.distribution.hotelbeds_adapter")

_TEST_BASE = "https://api.test.hotelbeds.com"
_PROD_BASE = "https://api.hotelbeds.com"

_MISSING_FOR_UPGRADE = [
    "Production Hotelbeds API credentials (HOTELBEDS_API_KEY + HOTELBEDS_SHARED_SECRET)",
    "Static hotel content portfolio pre-load (Hotelbeds Hotel Content API)",
    "Deposit policy and cancellation penalty calculation per rate plan",
    "Currency conversion via Hotelbeds /types/currencies endpoint",
]


@dataclass(slots=True)
class HotelRateOffer:
    """A single hotel rate option returned from Hotelbeds."""

    hotel_code: str
    hotel_name: str
    room_type: str
    board_code: str          # BB=Bed & Breakfast, AI=All-Inclusive, RO=Room Only, etc.
    rate_key: str            # Opaque key for booking creation
    net_rate_usd: float      # Net wholesale rate (what the agency pays)
    retail_rate_usd: float   # Retail price recommended to client
    agency_margin_usd: float
    currency: str
    check_in: str            # ISO 8601 date
    check_out: str
    nights: int
    available: bool
    cancellation_deadline: Optional[str]  # ISO 8601 or None for non-refundable
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hotel_code": self.hotel_code,
            "hotel_name": self.hotel_name,
            "room_type": self.room_type,
            "board_code": self.board_code,
            "rate_key": self.rate_key,
            "net_rate_usd": self.net_rate_usd,
            "retail_rate_usd": self.retail_rate_usd,
            "agency_margin_usd": self.agency_margin_usd,
            "currency": self.currency,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "nights": self.nights,
            "available": self.available,
            "cancellation_deadline": self.cancellation_deadline,
            "reality_tier": self.reality_tier,
            "provider_connected": self.provider_connected,
        }


@dataclass(slots=True)
class HotelBookingResult:
    """Result of a Hotelbeds hotel booking creation request."""

    booking_reference: str   # Hotelbeds booking reference (e.g. "HTB-2026-000123")
    hotel_code: str
    hotel_name: str
    check_in: str
    check_out: str
    total_net_usd: float
    total_retail_usd: float
    status: str              # "CONFIRMED" | "ON_REQUEST" | "PREVIEW_ONLY"
    voucher_url: Optional[str]
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False
    missing_for_upgrade: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "booking_reference": self.booking_reference,
            "hotel_code": self.hotel_code,
            "hotel_name": self.hotel_name,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "total_net_usd": self.total_net_usd,
            "total_retail_usd": self.total_retail_usd,
            "status": self.status,
            "voucher_url": self.voucher_url,
            "reality_tier": self.reality_tier,
            "provider_connected": self.provider_connected,
            "missing_for_upgrade": self.missing_for_upgrade,
        }


class HotelbedsAdapter:
    """Wholesale hotel rate shopping and booking via Hotelbeds / Bedsonline.

    Usage:
        adapter = HotelbedsAdapter()
        offers = adapter.search_hotel_rates(
            destination_code="LON",
            check_in="2026-11-01",
            check_out="2026-11-05",
            adults=2,
        )
        booking = adapter.create_hotel_booking(
            rate_key=offers[0].rate_key,
            lead_traveler_name="Jane Smith",
        )
    """

    def __init__(self) -> None:
        self._api_key = os.environ.get("HOTELBEDS_API_KEY", "").strip()
        self._shared_secret = os.environ.get("HOTELBEDS_SHARED_SECRET", "").strip()
        env = os.environ.get("HOTELBEDS_ENV", "test").strip().lower()
        self._base_url = _PROD_BASE if env == "production" else _TEST_BASE
        self._live = bool(self._api_key and self._shared_secret)
        if self._live:
            logger.info(
                "HotelbedsAdapter: live mode (base=%s)", self._base_url
            )
        else:
            logger.info(
                "HotelbedsAdapter: sandbox/preview mode (no credentials)"
            )

    def _signature(self) -> str:
        """Compute the Hotelbeds API signature per spec:
        SHA256(apiKey + sharedSecret + UTCTimestampSeconds)
        """
        ts = str(int(time.time()))
        raw = self._api_key + self._shared_secret + ts
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _headers(self) -> Dict[str, str]:
        return {
            "Api-key": self._api_key,
            "X-Signature": self._signature(),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _live_search(
        self,
        destination_code: str,
        check_in: str,
        check_out: str,
        adults: int,
        rooms: int,
    ) -> List[HotelRateOffer]:
        """Execute a live Hotelbeds /hotel-api/1.0/hotels availability request."""
        import urllib.request
        import json

        nights = self._nights(check_in, check_out)
        payload = {
            "stay": {"checkIn": check_in, "checkOut": check_out},
            "occupancies": [{"rooms": rooms, "adults": adults, "children": 0}],
            "destination": {"code": destination_code},
        }
        req = urllib.request.Request(
            f"{self._base_url}/hotel-api/1.0/hotels",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            logger.error("Hotelbeds live search failed: %s", exc)
            return []

        offers = []
        for hotel in (data.get("hotels") or {}).get("hotels") or []:
            for rate in (hotel.get("rooms") or [{}])[0].get("rates") or []:
                net = float(rate.get("net") or 0)
                retail = round(net * 1.15, 2)  # 15% markup
                offers.append(
                    HotelRateOffer(
                        hotel_code=str(hotel.get("code")),
                        hotel_name=str(hotel.get("name")),
                        room_type=str(
                            (hotel.get("rooms") or [{}])[0].get("name", "Standard Room")
                        ),
                        board_code=str(rate.get("boardCode", "BB")),
                        rate_key=str(rate.get("rateKey", "")),
                        net_rate_usd=net,
                        retail_rate_usd=retail,
                        agency_margin_usd=round(retail - net, 2),
                        currency="USD",
                        check_in=check_in,
                        check_out=check_out,
                        nights=nights,
                        available=True,
                        cancellation_deadline=None,
                        reality_tier=RealityTier.LIVE_PROVIDER.value
                        if hasattr(RealityTier, "LIVE_PROVIDER")
                        else "live_provider",
                        provider_connected=True,
                    )
                )
        return offers

    @staticmethod
    def _nights(check_in: str, check_out: str) -> int:
        from datetime import date
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
            return max(1, (co - ci).days)
        except Exception:
            return 1

    def _sandbox_offers(
        self,
        destination_code: str,
        check_in: str,
        check_out: str,
        adults: int,
    ) -> List[HotelRateOffer]:
        """Return deterministic preview hotel offers when no credentials are set."""
        nights = self._nights(check_in, check_out)
        base = 120.0 * nights  # $120/night baseline net rate
        return [
            HotelRateOffer(
                hotel_code=f"HTB-{destination_code.upper()}-001",
                hotel_name=f"Grand Central Hotel {destination_code.upper()}",
                room_type="Superior King Room",
                board_code="BB",
                rate_key=f"PREVIEW-RATEKEY-{destination_code.upper()}-BB-{check_in}",
                net_rate_usd=base,
                retail_rate_usd=round(base * 1.15, 2),
                agency_margin_usd=round(base * 0.15, 2),
                currency="USD",
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                available=True,
                cancellation_deadline=check_in,
                reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
                provider_connected=False,
            ),
            HotelRateOffer(
                hotel_code=f"HTB-{destination_code.upper()}-002",
                hotel_name=f"Boutique Collection {destination_code.upper()}",
                room_type="Deluxe Twin Room",
                board_code="RO",
                rate_key=f"PREVIEW-RATEKEY-{destination_code.upper()}-RO-{check_in}",
                net_rate_usd=round(base * 0.85, 2),
                retail_rate_usd=round(base * 0.85 * 1.15, 2),
                agency_margin_usd=round(base * 0.85 * 0.15, 2),
                currency="USD",
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                available=True,
                cancellation_deadline=None,  # Non-refundable
                reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
                provider_connected=False,
            ),
        ]

    def search_hotel_rates(
        self,
        destination_code: str,
        check_in: str,
        check_out: str,
        adults: int = 2,
        rooms: int = 1,
    ) -> List[HotelRateOffer]:
        """Search available hotel rates for a destination and stay window.

        Args:
            destination_code: Hotelbeds destination code (e.g. "LON", "NYC", "DXB").
            check_in: ISO 8601 date (YYYY-MM-DD).
            check_out: ISO 8601 date (YYYY-MM-DD).
            adults: Number of adult occupants.
            rooms: Number of rooms.

        Returns:
            List of HotelRateOffer sorted by net_rate_usd ascending.
        """
        if self._live:
            offers = self._live_search(destination_code, check_in, check_out, adults, rooms)
            if offers:
                return sorted(offers, key=lambda o: o.net_rate_usd)
            # Fall through to sandbox on empty live response
            logger.warning("Live Hotelbeds search returned no offers; using preview fallback.")
        return sorted(
            self._sandbox_offers(destination_code, check_in, check_out, adults),
            key=lambda o: o.net_rate_usd,
        )

    def create_hotel_booking(
        self,
        rate_key: str,
        lead_traveler_name: str,
        idempotency_key: str = "",
    ) -> HotelBookingResult:
        """Create a hotel booking for the selected rate key.

        In live mode, calls POST /hotel-api/1.0/bookings.
        In preview mode, returns a deterministic synthetic confirmation.
        """
        if self._live and not rate_key.startswith("PREVIEW-"):
            import urllib.request
            import json

            payload = {
                "holder": {
                    "name": lead_traveler_name.split()[-1] if lead_traveler_name else "Traveler",
                    "surname": lead_traveler_name.split()[0] if lead_traveler_name else "Lead",
                },
                "rooms": [{"rateKey": rate_key, "paxes": [{"roomId": 1, "type": "AD"}]}],
                "clientReference": idempotency_key or f"WP-{rate_key[:12]}",
            }
            req = urllib.request.Request(
                f"{self._base_url}/hotel-api/1.0/bookings",
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers(),
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                bk = data.get("booking") or {}
                hotel = (bk.get("hotel") or {})
                return HotelBookingResult(
                    booking_reference=str(bk.get("reference") or "HTB-LIVE-REF"),
                    hotel_code=str(hotel.get("code", "")),
                    hotel_name=str(hotel.get("name", "")),
                    check_in=str(hotel.get("checkIn", "")),
                    check_out=str(hotel.get("checkOut", "")),
                    total_net_usd=float((bk.get("totalNet") or {}).get("amount") or 0),
                    total_retail_usd=float((bk.get("pendingAmount") or {}).get("amount") or 0),
                    status="CONFIRMED",
                    voucher_url=None,
                    reality_tier="live_provider",
                    provider_connected=True,
                    missing_for_upgrade=[],
                )
            except Exception as exc:
                logger.error("Hotelbeds live booking failed: %s", exc)
                # Fall through to preview

        # Preview/sandbox booking
        ref = f"HTB-PREVIEW-{(idempotency_key or rate_key)[:12].upper()}"
        return HotelBookingResult(
            booking_reference=ref,
            hotel_code=rate_key.split("-")[2] if "-" in rate_key else "HTB000",
            hotel_name="Preview Hotel (not booked)",
            check_in="",
            check_out="",
            total_net_usd=0.0,
            total_retail_usd=0.0,
            status="PREVIEW_ONLY",
            voucher_url=None,
            reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
            provider_connected=False,
            missing_for_upgrade=_MISSING_FOR_UPGRADE,
        )
