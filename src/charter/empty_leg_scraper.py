"""
src/charter/empty_leg_scraper.py — AI-Native Autonomous Empty-Leg Scraper & Runway Ingestion Engine.

Processes scraped public empty-leg charter feeds (e.g. from Crawl4AI / Stagehand),
coerces unstructured markdown/DOM tables into typed EmptyLegOffer models, and
automatically validates aircraft runway feasibility against AIRPORT_PERFORMANCE_DATABASE.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.charter.aviation_engine import (
    AIRPORT_PERFORMANCE_DATABASE,
    FLEET_CATALOG,
    PrivateAviationEngine,
)
from src.charter.models import EmptyLegOffer, JetCategory


@dataclass(slots=True)
class ScrapedEmptyLegResult:
    offer: EmptyLegOffer
    is_runway_feasible: bool
    origin_effective_runway_ft: int
    dest_effective_runway_ft: int
    runway_warnings: List[str] = field(default_factory=list)


class EmptyLegScraperEngine:
    """
    Parses and verifies raw empty-leg charter feeds from browser scrapers.
    """

    @classmethod
    def parse_and_validate_feed(
        cls,
        raw_items: List[Dict[str, Any]],
    ) -> List[ScrapedEmptyLegResult]:
        """
        Coerces a list of scraped raw dictionaries into verified ScrapedEmptyLegResult objects.
        """
        results: List[ScrapedEmptyLegResult] = []

        for item in raw_items:
            origin_icao = str(item.get("origin_icao") or item.get("origin") or "").strip().upper()
            dest_icao = str(item.get("destination_icao") or item.get("destination") or "").strip().upper()
            aircraft_model = str(item.get("aircraft_model") or item.get("aircraft") or "Phenom 300E").strip()

            # Map jet category
            cat_str = str(item.get("category") or "").upper()
            category = JetCategory.LIGHT_JET
            for cat in JetCategory:
                if cat.value.upper() == cat_str or cat.name == cat_str:
                    category = cat
                    break

            std_price = float(item.get("standard_charter_price_usd") or item.get("standard_price") or 15000.0)
            disc_price = float(item.get("empty_leg_discounted_price_usd") or item.get("discounted_price") or 6000.0)
            discount_pct = round(((std_price - disc_price) / std_price * 100.0), 1) if std_price > disc_price else 0.0

            offer = EmptyLegOffer(
                offer_id=str(item.get("offer_id") or f"EL-SCRAPED-{uuid.uuid4().hex[:6].upper()}"),
                aircraft_model=aircraft_model,
                category=category,
                origin_icao=origin_icao,
                destination_icao=dest_icao,
                departure_window_start=str(item.get("departure_window_start") or "2026-10-15T10:00:00Z"),
                departure_window_end=str(item.get("departure_window_end") or "2026-10-15T18:00:00Z"),
                standard_charter_price_usd=std_price,
                empty_leg_discounted_price_usd=disc_price,
                discount_percent=discount_pct,
                operator_name=str(item.get("operator_name") or "Verified Charter Broker"),
                fbo_origin=str(item.get("fbo_origin") or f"FBO {origin_icao}"),
                fbo_destination=str(item.get("fbo_destination") or f"FBO {dest_icao}"),
            )

            # Runway feasibility audit
            spec = FLEET_CATALOG.get(aircraft_model, FLEET_CATALOG["Phenom 300E"])
            base_runway_req = spec.min_runway_length_ft

            orig_perf = AIRPORT_PERFORMANCE_DATABASE.get(origin_icao)
            dest_perf = AIRPORT_PERFORMANCE_DATABASE.get(dest_icao)

            orig_req = PrivateAviationEngine.calculate_effective_runway_required(spec, orig_perf) if orig_perf else base_runway_req
            dest_req = PrivateAviationEngine.calculate_effective_runway_required(spec, dest_perf) if dest_perf else base_runway_req

            orig_avail = orig_perf.runway_length_ft if orig_perf else 7000
            dest_avail = dest_perf.runway_length_ft if dest_perf else 7000

            runway_warnings: List[str] = []
            is_feasible = True

            if orig_req > orig_avail:
                is_feasible = False
                runway_warnings.append(
                    f"Origin runway {origin_icao} too short: {orig_avail}ft available vs {orig_req}ft required (hot/high penalty)."
                )

            if dest_req > dest_avail:
                is_feasible = False
                runway_warnings.append(
                    f"Destination runway {dest_icao} too short: {dest_avail}ft available vs {dest_req}ft required (hot/high penalty)."
                )

            if orig_perf and orig_perf.max_payload_reduction_percent > 0:
                runway_warnings.append(
                    f"Origin {origin_icao} density altitude imposes -{orig_perf.max_payload_reduction_percent}% payload reduction."
                )

            results.append(
                ScrapedEmptyLegResult(
                    offer=offer,
                    is_runway_feasible=is_feasible,
                    origin_effective_runway_ft=orig_req,
                    dest_effective_runway_ft=dest_req,
                    runway_warnings=runway_warnings,
                )
            )

        return results

    @classmethod
    def parse_markdown_table_feed(cls, markdown_text: str) -> List[ScrapedEmptyLegResult]:
        """
        Parses Markdown tables produced by Crawl4AI or Stagehand scraping runs.
        """
        raw_items: List[Dict[str, Any]] = []
        lines = [line.strip() for line in markdown_text.strip().split("\n") if line.strip()]

        for line in lines:
            if not line.startswith("|") or "---" in line or "Origin" in line:
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 4:
                # Format: | Origin | Destination | Aircraft | Price |
                orig = cells[0]
                dest = cells[1]
                aircraft = cells[2]
                price_match = re.search(r"[\d,]+", cells[3])
                price = float(price_match.group(0).replace(",", "")) if price_match else 7500.0

                raw_items.append({
                    "origin_icao": orig,
                    "destination_icao": dest,
                    "aircraft_model": aircraft,
                    "standard_charter_price_usd": price * 2.5,
                    "empty_leg_discounted_price_usd": price,
                })

        return cls.parse_and_validate_feed(raw_items)
