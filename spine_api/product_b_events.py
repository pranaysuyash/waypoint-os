from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from spine_api.persistence import file_lock


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("occurred_at must be a non-empty ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _percentile(values: List[int], q: float) -> Optional[int]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    idx = (len(ordered) - 1) * q
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return ordered[lower]
    weight = idx - lower
    return int(round(ordered[lower] * (1.0 - weight) + ordered[upper] * weight))


class ProductBEventStore:
    """Append-only event store for Product B wedge instrumentation."""

    DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "product_b_events"
    RAW_FILE = DATA_DIR / "events_raw.jsonl"
    NORMALIZED_FILE = DATA_DIR / "events_normalized.jsonl"
    NORMALIZED_DATA_SOURCE_LABEL = "data/product_b_events/events_normalized.jsonl"

    ALLOWED_EVENT_NAMES = {
        "intake_started",
        "first_credible_finding_shown",
        "finding_evidence_opened",
        "action_packet_copied",
        "action_packet_shared",
        "agency_revision_reported",
        "re_audit_started",
        "product_a_interest_signal",
    }

    REQUIRED_ENVELOPE_FIELDS = {
        "event_name",
        "event_version",
        "event_id",
        "occurred_at",
        "session_id",
        "inquiry_id",
        "trip_id",
        "actor_type",
        "actor_id",
        "workspace_id",
        "channel",
        "locale",
        "currency",
    }

    ALLOWED_ACTOR_TYPES = {"traveler", "system", "operator"}
    ALLOWED_CHANNELS = {"web", "mobile_web", "api"}

    MAX_EVENT_BYTES = 16 * 1024
    MAX_PROPERTIES = 64
    MAX_ID_LENGTH = 128

    EVENT_REQUIRED_PROPERTIES: Dict[str, set[str]] = {
        "intake_started": {
            "input_mode",
            "has_destination",
            "has_dates",
            "has_budget_band",
            "has_traveler_profile",
        },
        "first_credible_finding_shown": {
            "time_from_intake_start_ms",
            "finding_id",
            "finding_category",
            "severity",
            "confidence_score",
            "evidence_present",
        },
        "finding_evidence_opened": {
            "finding_id",
            "evidence_type",
            "open_index",
        },
        "action_packet_copied": {
            "packet_id",
            "packet_type",
            "finding_count",
            "had_manual_edits",
        },
        "action_packet_shared": {
            "packet_id",
            "share_channel",
            "had_manual_edits",
        },
        "agency_revision_reported": {
            "revision_report_mode",
            "revision_outcome",
            "time_from_share_ms",
        },
        "re_audit_started": {
            "prior_packet_id",
            "revision_input_mode",
        },
        "product_a_interest_signal": {
            "signal_type",
            "attribution_mode",
            "source_inquiry_id",
        },
    }

    @classmethod
    def _ensure_dirs(cls) -> None:
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _append_jsonl(cls, path: Path, payload: Dict[str, Any]) -> None:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")

    @classmethod
    def _read_jsonl(cls, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    rows.append(parsed)
        return rows

    @classmethod
    def _event_id_exists(cls, event_id: str) -> bool:
        if not cls.NORMALIZED_FILE.exists():
            return False
        with open(cls.NORMALIZED_FILE, "r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict) and parsed.get("event_id") == event_id:
                    return True
        return False

    @classmethod
    def build_event(
        cls,
        *,
        event_name: str,
        session_id: str,
        inquiry_id: str,
        actor_type: str,
        channel: str,
        properties: Dict[str, Any],
        trip_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        locale: Optional[str] = None,
        currency: Optional[str] = None,
        event_id: Optional[str] = None,
        occurred_at: Optional[str] = None,
        event_version: int = 1,
    ) -> Dict[str, Any]:
        return {
            "event_name": event_name,
            "event_version": event_version,
            "event_id": event_id or str(uuid4()),
            "occurred_at": occurred_at or _utc_now_iso(),
            "session_id": session_id,
            "inquiry_id": inquiry_id,
            "trip_id": trip_id,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "channel": channel,
            "locale": locale,
            "currency": currency,
            "properties": properties,
        }

    @classmethod
    def normalize_event(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("event payload must be an object")

        payload_size = len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
        if payload_size > cls.MAX_EVENT_BYTES:
            raise ValueError("event payload exceeds maximum size")

        missing = [field for field in cls.REQUIRED_ENVELOPE_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"missing required envelope fields: {', '.join(sorted(missing))}")

        event_name = str(payload.get("event_name") or "").strip()
        if event_name not in cls.ALLOWED_EVENT_NAMES:
            raise ValueError(f"unsupported event_name: {event_name}")

        event_version = payload.get("event_version")
        if not isinstance(event_version, int) or event_version < 1:
            raise ValueError("event_version must be an integer >= 1")

        event_id = str(payload.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("event_id must be non-empty")
        if len(event_id) > cls.MAX_ID_LENGTH:
            raise ValueError("event_id is too long")

        occurred_at = _parse_iso_utc(str(payload.get("occurred_at")))

        session_id = str(payload.get("session_id") or "").strip()
        inquiry_id = str(payload.get("inquiry_id") or "").strip()
        if not session_id:
            raise ValueError("session_id must be non-empty")
        if not inquiry_id:
            raise ValueError("inquiry_id must be non-empty")
        if len(session_id) > cls.MAX_ID_LENGTH:
            raise ValueError("session_id is too long")
        if len(inquiry_id) > cls.MAX_ID_LENGTH:
            raise ValueError("inquiry_id is too long")

        actor_type = str(payload.get("actor_type") or "").strip()
        if actor_type not in cls.ALLOWED_ACTOR_TYPES:
            raise ValueError(f"actor_type must be one of: {sorted(cls.ALLOWED_ACTOR_TYPES)}")

        channel = str(payload.get("channel") or "").strip()
        if channel not in cls.ALLOWED_CHANNELS:
            raise ValueError(f"channel must be one of: {sorted(cls.ALLOWED_CHANNELS)}")

        properties = payload.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("properties must be an object")
        if len(properties) > cls.MAX_PROPERTIES:
            raise ValueError("properties has too many keys")

        required_properties = cls.EVENT_REQUIRED_PROPERTIES.get(event_name, set())
        missing_properties = [key for key in required_properties if key not in properties]
        if missing_properties:
            raise ValueError(
                f"missing required properties for {event_name}: {', '.join(sorted(missing_properties))}"
            )

        if event_name == "first_credible_finding_shown" and not bool(properties.get("evidence_present")):
            raise ValueError("first_credible_finding_shown requires evidence_present=true")

        trip_id = payload.get("trip_id")
        if trip_id is not None and len(str(trip_id)) > cls.MAX_ID_LENGTH:
            raise ValueError("trip_id is too long")

        normalized = {
            "event_name": event_name,
            "event_version": event_version,
            "event_id": event_id,
            "occurred_at": occurred_at.isoformat(),
            "occurred_at_epoch_ms": int(occurred_at.timestamp() * 1000),
            "session_id": session_id,
            "inquiry_id": inquiry_id,
            "trip_id": trip_id,
            "actor_type": actor_type,
            "actor_id": payload.get("actor_id"),
            "workspace_id": payload.get("workspace_id"),
            "channel": channel,
            "locale": payload.get("locale"),
            "currency": payload.get("currency"),
            "properties": properties,
        }
        return normalized

    @classmethod
    def log_event(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = cls.normalize_event(payload)
        cls._ensure_dirs()
        with file_lock(cls.NORMALIZED_FILE):
            if cls._event_id_exists(normalized["event_id"]):
                return {
                    "status": "duplicate",
                    "event_id": normalized["event_id"],
                    "event_name": normalized["event_name"],
                }
            cls._append_jsonl(cls.RAW_FILE, payload)
            cls._append_jsonl(cls.NORMALIZED_FILE, normalized)

        return {
            "status": "accepted",
            "event_id": normalized["event_id"],
            "event_name": normalized["event_name"],
        }

    @classmethod
    def list_events(
        cls,
        *,
        window_days: int = 30,
        event_name: Optional[str] = None,
        inquiry_id: Optional[str] = None,
        trip_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, window_days))
        events = cls._read_jsonl(cls.NORMALIZED_FILE)
        filtered: List[Dict[str, Any]] = []
        for event in events:
            try:
                occurred_at = _parse_iso_utc(str(event.get("occurred_at")))
            except Exception:
                continue
            if occurred_at < cutoff:
                continue
            if event_name and event.get("event_name") != event_name:
                continue
            if inquiry_id and event.get("inquiry_id") != inquiry_id:
                continue
            if trip_id and event.get("trip_id") != trip_id:
                continue
            filtered.append(event)

        filtered.sort(key=lambda e: str(e.get("occurred_at") or ""))
        return filtered

    @classmethod
    def _group_by_inquiry(cls, events: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for event in events:
            inquiry = str(event.get("inquiry_id") or "").strip()
            if inquiry:
                grouped[inquiry].append(event)
        for inquiry_events in grouped.values():
            inquiry_events.sort(key=lambda e: str(e.get("occurred_at") or ""))
        return grouped

    @classmethod
    def _is_qualified_inquiry(cls, inquiry_events: List[Dict[str, Any]]) -> bool:
        has_intake = any(evt.get("event_name") == "intake_started" for evt in inquiry_events)
        has_credible = any(evt.get("event_name") == "first_credible_finding_shown" for evt in inquiry_events)
        return has_intake and has_credible and not cls._qualified_exclusion_reasons(inquiry_events)

    @classmethod
    def _qualified_exclusion_reasons(cls, inquiry_events: List[Dict[str, Any]]) -> List[str]:
        intake = next((evt for evt in inquiry_events if evt.get("event_name") == "intake_started"), None)
        if not intake:
            return []

        props = intake.get("properties") or {}
        reasons: List[str] = []
        if props.get("internal_test_traffic") is True:
            reasons.append("internal_test_traffic")
        if props.get("sufficient_input_quality") is False:
            reasons.append("insufficient_input_quality")
        if props.get("real_trip_intent") is False:
            reasons.append("missing_real_trip_intent")
        return reasons

    @classmethod
    def _kpi_definitions(cls, *, window_days: int) -> Dict[str, Any]:
        data_source = cls.NORMALIZED_DATA_SOURCE_LABEL
        return {
            "qualified_sample_rule": {
                "description": (
                    "Qualified inquiries require both intake_started and "
                    "first_credible_finding_shown in the selected window."
                ),
                "required_events": ["intake_started", "first_credible_finding_shown"],
                "exclusions": [
                    "internal_test_traffic",
                    "insufficient_input_quality",
                    "missing_real_trip_intent",
                ],
                "current_enforcement": "event_presence_plus_explicit_exclusions",
            },
            "kpis": {
                "time_to_first_credible_finding_ms": {
                    "description": "Latency from Product B intake start to first evidence-backed finding.",
                    "numerator": "first_credible_finding_shown.properties.time_from_intake_start_ms values",
                    "denominator": "qualified inquiries with first_credible_finding_shown",
                    "aggregation": "p50 and p90 percentile",
                    "window_days": window_days,
                    "data_source": data_source,
                },
                "forward_without_edit_rate": {
                    "description": "Share of action packets that were forwarded without manual edits.",
                    "numerator": "action_packet_shared where properties.had_manual_edits=false",
                    "denominator": "all action_packet_shared events",
                    "aggregation": "ratio",
                    "window_days": window_days,
                    "data_source": data_source,
                },
                "agency_revision_rate_observed_7d": {
                    "description": "Observed share of shared packets that led to a revised agency itinerary within seven days.",
                    "numerator": (
                        "inquiries with agency_revision_reported revision_outcome=revised "
                        "and confidence_tier=observed"
                    ),
                    "denominator": "inquiries with at least one action_packet_shared event",
                    "aggregation": "ratio",
                    "window_days": window_days,
                    "data_source": data_source,
                },
                "inferred_revision_rate": {
                    "description": "Companion diagnostic for likely revisions; never a primary launch-success KPI.",
                    "numerator": (
                        "inquiries with agency_revision_reported revision_outcome=revised "
                        "and confidence_tier=inferred"
                    ),
                    "denominator": "inquiries with at least one action_packet_shared event",
                    "aggregation": "ratio",
                    "window_days": window_days,
                    "data_source": data_source,
                },
                "dark_funnel_rate": {
                    "description": "Share of shared packets with no observed or inferred revision outcome.",
                    "numerator": "shared inquiries without agency_revision_reported outcome",
                    "denominator": "inquiries with at least one action_packet_shared event",
                    "aggregation": "ratio",
                    "window_days": window_days,
                    "data_source": data_source,
                },
                "product_a_pull_through": {
                    "description": "Product A demand generated by qualified Product B exposure.",
                    "numerator": "product_a_interest_signal events",
                    "denominator": "qualified inquiries",
                    "aggregation": "ratio",
                    "window_days": window_days,
                    "data_source": data_source,
                },
            },
        }

    @classmethod
    def compute_kpis(cls, *, window_days: int = 30, qualified_only: bool = False) -> Dict[str, Any]:
        events = cls.list_events(window_days=window_days)
        grouped = cls._group_by_inquiry(events)

        ttf_values: List[int] = []
        shared_total = 0
        shared_without_edit = 0
        revision_denominator = 0
        observed_revised = 0
        inferred_revised = 0
        unknown_outcomes = 0
        product_a_signals = 0
        qualified_inquiries = 0
        excluded_inquiries = {
            "internal_test_traffic": 0,
            "insufficient_input_quality": 0,
            "missing_real_trip_intent": 0,
        }

        confidence_breakdown = {"observed": 0, "inferred": 0, "unknown": 0}

        for inquiry_id, inquiry_events in grouped.items():
            _ = inquiry_id
            is_qualified = cls._is_qualified_inquiry(inquiry_events)
            if is_qualified:
                qualified_inquiries += 1
            else:
                for reason in cls._qualified_exclusion_reasons(inquiry_events):
                    if reason in excluded_inquiries:
                        excluded_inquiries[reason] += 1
            if qualified_only and not is_qualified:
                continue

            first_credible = next((evt for evt in inquiry_events if evt.get("event_name") == "first_credible_finding_shown"), None)
            if first_credible:
                props = first_credible.get("properties") or {}
                ms = props.get("time_from_intake_start_ms")
                if isinstance(ms, (int, float)) and ms >= 0:
                    ttf_values.append(int(ms))

            share_events = [evt for evt in inquiry_events if evt.get("event_name") == "action_packet_shared"]
            if share_events:
                revision_denominator += 1
                shared_total += len(share_events)
                for share_event in share_events:
                    share_props = share_event.get("properties") or {}
                    if share_props.get("had_manual_edits") is False:
                        shared_without_edit += 1

                revision_events = [evt for evt in inquiry_events if evt.get("event_name") == "agency_revision_reported"]
                if revision_events:
                    latest_revision = revision_events[-1]
                    rev_props = latest_revision.get("properties") or {}
                    outcome = str(rev_props.get("revision_outcome") or "").lower()
                    confidence_tier = str(rev_props.get("confidence_tier") or "observed").lower()

                    if outcome == "revised" and confidence_tier == "observed":
                        observed_revised += 1
                        confidence_breakdown["observed"] += 1
                    elif outcome == "revised" and confidence_tier == "inferred":
                        inferred_revised += 1
                        confidence_breakdown["inferred"] += 1
                    else:
                        unknown_outcomes += 1
                        confidence_breakdown["unknown"] += 1
                else:
                    unknown_outcomes += 1
                    confidence_breakdown["unknown"] += 1

            product_a_signals += sum(1 for evt in inquiry_events if evt.get("event_name") == "product_a_interest_signal")

        forward_without_edit_rate = (shared_without_edit / shared_total) if shared_total > 0 else None
        observed_revision_rate_7d = (observed_revised / revision_denominator) if revision_denominator > 0 else None
        inferred_revision_rate = (inferred_revised / revision_denominator) if revision_denominator > 0 else None
        dark_funnel_rate = (unknown_outcomes / revision_denominator) if revision_denominator > 0 else None

        pull_through_denominator = qualified_inquiries if qualified_inquiries > 0 else 0
        product_a_pull_through = (
            product_a_signals / pull_through_denominator if pull_through_denominator > 0 else None
        )

        return {
            "window_days": window_days,
            "qualified_only": qualified_only,
            "sample": {
                "events": len(events),
                "inquiries_total": len(grouped),
                "qualified_inquiries": qualified_inquiries,
                "excluded_inquiries": excluded_inquiries,
            },
            "kpis": {
                "time_to_first_credible_finding_ms": {
                    "p50": _percentile(ttf_values, 0.50),
                    "p90": _percentile(ttf_values, 0.90),
                    "n": len(ttf_values),
                },
                "forward_without_edit_rate": forward_without_edit_rate,
                "agency_revision_rate_observed_7d": observed_revision_rate_7d,
                "inferred_revision_rate": inferred_revision_rate,
                "dark_funnel_rate": dark_funnel_rate,
                "product_a_pull_through": product_a_pull_through,
            },
            "confidence_tiers": confidence_breakdown,
            "counts": {
                "action_packet_shared": shared_total,
                "revision_denominator": revision_denominator,
                "observed_revised": observed_revised,
                "inferred_revised": inferred_revised,
                "unknown_outcomes": unknown_outcomes,
                "product_a_interest_signal": product_a_signals,
            },
            "definitions": cls._kpi_definitions(window_days=window_days),
        }
