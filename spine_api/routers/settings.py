"""
Settings router.

Owns agency profile/operational/autonomy settings plus pipeline and approval
configuration endpoints. Extracted from ``spine_api.server`` so the FastAPI app
shell can keep moving toward route-module ownership without changing contracts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException

from src.llm.usage_guard import get_guard_for_agency, reload_guard_for_agency
from src.llm.alert_service import alert_service_from_settings

from spine_api.contract import (
    ApprovalThresholdConfig,
    PipelineStageConfig,
    AgencySeasonalSettingsResponse,
    CreateSeasonalCampaignRequest,
    SeasonDispatchRequest,
    SeasonPreflightCheck,
    SeasonSimulationRequest,
    SeasonalCampaignListResponse,
    SeasonalCampaignPlan,
    UpdateAiAgentSettings,
    UpdateAutonomyPolicy,
    UpdateCommSettings,
    UpdateSeasonalCampaignRequest,
    UpdateOperationalSettings,
    UpdateSeasonalPolicy,
    UpdateSupportSettings,
)
from spine_api.core.auth import require_permission
from src.intake.config.agency_settings import AgencySettingsStore

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

ConfigStore = persistence.ConfigStore

router = APIRouter()


def _build_agency_settings_payload(settings) -> dict:
    return {
        "agency_id": settings.agency_id,
        "tier": settings.tier.value,
        "seasonal": ConfigStore.get_seasonal_policy(settings.agency_id),
        "profile": {
            "agency_name": settings.agency_name,
            "sub_brand": settings.sub_brand,
            "plan_label": settings.plan_label,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            "logo_url": settings.logo_url,
            "website": settings.website,
        },
        "operational": {
            "target_margin_pct": settings.target_margin_pct,
            "default_currency": settings.default_currency,
            "operating_hours": {
                "start": settings.operating_hours_start,
                "end": settings.operating_hours_end,
            },
            "operating_days": settings.operating_days,
            "preferred_channels": settings.preferred_channels,
            "brand_tone": settings.brand_tone,
        },
        "autonomy": {
            "approval_gates": settings.autonomy.approval_gates,
            "mode_overrides": settings.autonomy.mode_overrides,
            "auto_proceed_with_warnings": settings.autonomy.auto_proceed_with_warnings,
            "learn_from_overrides": settings.autonomy.learn_from_overrides,
            "auto_reprocess_on_edit": settings.autonomy.auto_reprocess_on_edit,
            "allow_explicit_reassess": settings.autonomy.allow_explicit_reassess,
            "auto_reprocess_stages": settings.autonomy.auto_reprocess_stages,
            "min_proceed_confidence": settings.autonomy.min_proceed_confidence,
            "min_draft_confidence": settings.autonomy.min_draft_confidence,
        },
    }


@router.get("/api/settings")
def get_agency_settings(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    settings = AgencySettingsStore.load(agency_id)
    return _build_agency_settings_payload(settings)


@router.post("/api/settings/operational")
def update_agency_operational_settings(
    request: UpdateOperationalSettings,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """
    Update agency operational and profile settings.
    Only fields provided in the request are modified; others remain unchanged.
    """
    settings = AgencySettingsStore.load(agency_id)

    if request.agency_name is not None:
        settings.agency_name = request.agency_name
    if request.sub_brand is not None:
        settings.sub_brand = request.sub_brand
    if request.plan_label is not None:
        settings.plan_label = request.plan_label
    if request.contact_email is not None:
        settings.contact_email = request.contact_email
    if request.contact_phone is not None:
        settings.contact_phone = request.contact_phone
    if request.logo_url is not None:
        settings.logo_url = request.logo_url
    if request.website is not None:
        settings.website = request.website

    if request.target_margin_pct is not None:
        settings.target_margin_pct = request.target_margin_pct
    if request.default_currency is not None:
        settings.default_currency = request.default_currency
    if request.operating_hours_start is not None:
        settings.operating_hours_start = request.operating_hours_start
    if request.operating_hours_end is not None:
        settings.operating_hours_end = request.operating_hours_end
    if request.operating_days is not None:
        settings.operating_days = request.operating_days
    if request.preferred_channels is not None:
        settings.preferred_channels = request.preferred_channels
    if request.brand_tone is not None:
        settings.brand_tone = request.brand_tone

    AgencySettingsStore.save(settings)

    return _build_agency_settings_payload(settings)


@router.get("/api/settings/autonomy")
def get_agency_autonomy_settings(agency_id: str = "waypoint-hq"):
    """Return the agency autonomy policy (gates, overrides, flags)."""
    settings = AgencySettingsStore.load(agency_id)
    policy = settings.autonomy
    return {
        "agency_id": settings.agency_id,
        "approval_gates": policy.approval_gates,
        "mode_overrides": policy.mode_overrides,
        "auto_proceed_with_warnings": policy.auto_proceed_with_warnings,
        "learn_from_overrides": policy.learn_from_overrides,
        "auto_reprocess_on_edit": policy.auto_reprocess_on_edit,
        "allow_explicit_reassess": policy.allow_explicit_reassess,
        "auto_reprocess_stages": policy.auto_reprocess_stages,
        "min_proceed_confidence": policy.min_proceed_confidence,
        "min_draft_confidence": policy.min_draft_confidence,
    }


@router.post("/api/settings/autonomy")
def update_agency_autonomy_settings(
    request: UpdateAutonomyPolicy,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """
    Update the agency autonomy policy.

    - Rejects any attempt to set STOP_NEEDS_REVIEW to anything other than block.
    - Persists to the file-backed AgencySettingsStore.
    """
    settings = AgencySettingsStore.load(agency_id)
    policy = settings.autonomy

    if request.approval_gates is not None:
        for state, action in request.approval_gates.items():
            if state == "STOP_NEEDS_REVIEW" and action != "block":
                raise HTTPException(
                    status_code=400,
                    detail="Safety invariant: STOP_NEEDS_REVIEW must always be 'block'",
                )
            if action not in ("auto", "review", "block"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid action '{action}' for state '{state}'. Must be auto|review|block.",
                )
            policy.approval_gates[state] = action

    if request.mode_overrides is not None:
        policy.mode_overrides = {
            k: dict(v) if isinstance(v, dict) else {}
            for k, v in request.mode_overrides.items()
        }

    if request.auto_proceed_with_warnings is not None:
        policy.auto_proceed_with_warnings = request.auto_proceed_with_warnings

    if request.learn_from_overrides is not None:
        policy.learn_from_overrides = request.learn_from_overrides

    if request.auto_reprocess_on_edit is not None:
        policy.auto_reprocess_on_edit = request.auto_reprocess_on_edit

    if request.allow_explicit_reassess is not None:
        policy.allow_explicit_reassess = request.allow_explicit_reassess

    if request.auto_reprocess_stages is not None:
        allowed_stages = {"discovery", "shortlist", "proposal", "booking"}
        sanitized = {
            stage: bool(enabled)
            for stage, enabled in request.auto_reprocess_stages.items()
            if stage in allowed_stages
        }
        for stage in allowed_stages:
            sanitized.setdefault(stage, policy.auto_reprocess_stages.get(stage, True))
        policy.auto_reprocess_stages = sanitized

    AgencySettingsStore.save(settings)

    return _build_agency_settings_payload(settings)


def _to_float(value) -> Optional[float]:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _to_float_or_default(value, default: float) -> float:
    parsed = _to_float(value)
    return parsed if parsed is not None else default


def _to_int_month(value) -> Optional[int]:
    parsed = _to_float(value)
    if parsed is None:
        return None
    if parsed != int(parsed):
        return None
    return int(parsed)


def _coerce_campaign_channels(plan: dict) -> dict:
    normalized = dict(plan)
    raw_mix = plan.get("channel_mix", {})
    if isinstance(raw_mix, dict):
        normalized["channel_mix"] = {}
        for channel, weight in raw_mix.items():
            channel_key = str(channel).strip()
            if not channel_key:
                continue
            try:
                normalized_weight = float(weight)
            except (TypeError, ValueError):
                continue
            if normalized_weight != normalized_weight:
                continue
            normalized["channel_mix"][channel_key] = normalized_weight
    return normalized


def _build_simulation_notes(plan: dict, scenario: str) -> list[str]:
    notes = [
        f"Simulating scenario '{scenario}' for campaign '{plan.get('name')}'",
    ]
    if not plan.get("destination"):
        notes.append("Destination is open-ended; forecast uses demand baseline profile.")
    if plan.get("status") == "active":
        notes.append("Active campaign policy uses live channel mix and live guardrails.")
    return notes


def _simulation_profile(scenario: str) -> dict[str, float | str]:
    normalized = str(scenario).strip().lower()
    if normalized == "aggressive":
        return {
            "lead_multiplier": 1.18,
            "booking_rate": 0.40,
            "margin_adjust": -1.8,
            "confidence": 0.66,
            "note": "Aggressive pacing increases reach while trading off some margin discipline.",
        }
    if normalized == "conservative":
        return {
            "lead_multiplier": 0.84,
            "booking_rate": 0.44,
            "margin_adjust": 1.2,
            "confidence": 0.79,
            "note": "Conservative pacing protects margin and narrows the top-of-funnel forecast.",
        }
    return {
        "lead_multiplier": 1.0,
        "booking_rate": 0.42,
        "margin_adjust": 0.0,
        "confidence": 0.72,
        "note": "Baseline pacing reflects the current plan shape with neutral risk assumptions.",
    }


@router.get("/api/settings/seasonal")
def get_agency_seasonal_settings(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    payload = ConfigStore.get_seasonal_policy(agency_id)
    return AgencySeasonalSettingsResponse(**payload)


@router.put("/api/settings/seasonal")
def update_agency_seasonal_settings(
    request: UpdateSeasonalPolicy,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    payload = request.model_dump(exclude_none=True)
    if not payload:
        payload = {}
    ConfigStore.update_seasonal_policy(agency_id, payload)
    return _build_agency_settings_payload(
        AgencySettingsStore.load(agency_id)
    )


@router.get("/api/settings/seasonal/campaigns", response_model=SeasonalCampaignListResponse)
def list_seasonal_campaigns(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    plans = ConfigStore.list_seasonal_campaigns(agency_id)
    return SeasonalCampaignListResponse(items=[SeasonalCampaignPlan(**plan) for plan in plans], total=len(plans))


@router.post("/api/settings/seasonal/campaigns", response_model=SeasonalCampaignPlan)
def create_seasonal_campaign(
    request: CreateSeasonalCampaignRequest,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    payload = request.model_dump()
    try:
        created = ConfigStore.create_seasonal_campaign(agency_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SeasonalCampaignPlan(**_coerce_campaign_channels(created))


@router.get("/api/settings/seasonal/campaigns/{plan_id}", response_model=SeasonalCampaignPlan)
def get_seasonal_campaign(
    plan_id: str,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    plan = ConfigStore.get_seasonal_campaign(agency_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Seasonal campaign not found")
    return SeasonalCampaignPlan(**_coerce_campaign_channels(plan))


@router.put("/api/settings/seasonal/campaigns/{plan_id}", response_model=SeasonalCampaignPlan)
def update_seasonal_campaign(
    plan_id: str,
    request: UpdateSeasonalCampaignRequest,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    payload = request.model_dump(exclude_none=True)
    updated = ConfigStore.update_seasonal_campaign(agency_id, plan_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Seasonal campaign not found")
    return SeasonalCampaignPlan(**_coerce_campaign_channels(updated))


@router.delete("/api/settings/seasonal/campaigns/{plan_id}")
def delete_seasonal_campaign(
    plan_id: str,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    deleted = ConfigStore.delete_seasonal_campaign(agency_id, plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Seasonal campaign not found")
    return {"ok": True, "plan_id": plan_id}


@router.post("/api/settings/seasonal/campaigns/{plan_id}/simulate")
def simulate_seasonal_campaign(
    plan_id: str,
    request: SeasonSimulationRequest,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    plan = ConfigStore.get_seasonal_campaign(agency_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Seasonal campaign not found")

    base_budget = _to_float(plan.get("target_budget_min"))
    if base_budget is None:
        base_budget = _to_float(plan.get("target_budget_max"))
    if base_budget is None:
        base_budget = 10000.0

    mix_weight = sum(_to_float_or_default(v, 0.0) for v in (plan.get("channel_mix") or {}).values())
    month_window = 3
    start_month = _to_int_month(plan.get("campaign_window_start_month"))
    end_month = _to_int_month(plan.get("campaign_window_end_month"))
    if start_month is not None and end_month is not None:
        start = start_month
        end = end_month
        month_window = max(1, abs(end - start) + 1)

    profile = _simulation_profile(request.scenario)
    projected_leads = int(
        base_budget * max(1.0, mix_weight + 0.5) * month_window / 900 * float(profile["lead_multiplier"])
    )
    projected_bookings = max(1, int(projected_leads * float(profile["booking_rate"])))
    projected_margin_pct = max(
        0.0,
        min(42.0, 8.0 + (base_budget / 2000.0) + float(profile["margin_adjust"])),
    )
    confidence = float(profile["confidence"])
    notes = _build_simulation_notes(plan, request.scenario)
    notes.append(str(profile["note"]))

    return {
        "plan_id": plan_id,
        "scenario": request.scenario,
        "projected_leads": projected_leads,
        "projected_bookings": projected_bookings,
        "projected_margin_pct": round(projected_margin_pct, 2),
        "confidence": round(confidence, 3),
        "notes": notes,
    }


@router.post("/api/settings/seasonal/campaigns/{plan_id}/preflight")
def preflight_seasonal_campaign(
    plan_id: str,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    plan = ConfigStore.get_seasonal_campaign(agency_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Seasonal campaign not found")

    checks = []
    blocklist = plan.get("blocklist")
    if not isinstance(blocklist, list):
        blocklist = []

    target_budget_min = _to_float(plan.get("target_budget_min"))
    budget_check_status = (
        "warn"
        if target_budget_min is None
        else ("pass" if target_budget_min >= 0 else "fail")
    )
    budget_check_message = (
        "Budget target is unset; set lower bound for stronger preflight confidence."
        if target_budget_min is None
        else "Lower budget target must be non-negative."
    )
    checks.append(
        SeasonPreflightCheck(
            check="budget_boundaries",
            status=budget_check_status,
            details=budget_check_message,
        )
    )
    checks.append(
        SeasonPreflightCheck(
            check="channel_mix_present",
            status="pass" if isinstance(plan.get("channel_mix"), dict) else "warn",
            details="Campaign channel mix controls distribution weighting for future planning.",
        )
    )
    checks.append(
        SeasonPreflightCheck(
            check="window_defined",
            status="pass" if plan.get("campaign_window_start_month") and plan.get("campaign_window_end_month") else "warn",
            details="Define campaign start/end months for stronger simulation confidence.",
        )
    )

    risk_score = round(
        0.15
        + 0.2 * len(blocklist)
        + (0.45 if checks[0].status == "fail" else (0.2 if checks[0].status == "warn" else 0))
        + (0 if checks[1].status == "pass" else 0.15)
        + (0 if checks[2].status == "pass" else 0.15),
        2,
    )
    return {
        "plan_id": plan_id,
        "ok": all(check.status != "fail" for check in checks),
        "checks": checks,
        "risk_score": risk_score,
    }


@router.post("/api/settings/seasonal/campaigns/{plan_id}/dispatch")
def dispatch_seasonal_campaign(
    plan_id: str,
    request: SeasonDispatchRequest,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    plan = ConfigStore.get_seasonal_campaign(agency_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Seasonal campaign not found")

    channels = sorted((plan.get("channel_mix") or {}).keys())
    return {
        "plan_id": plan_id,
        "ok": True,
        "dispatched_channels": channels,
        "dry_run": bool(request.dry_run),
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/settings/llm-guard")
def get_llm_guard_state(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    """Return the current LLM usage guard state for an agency."""
    guard = get_guard_for_agency(agency_id)
    return guard.get_state()


# ---------------------------------------------------------------------------
# Alert Destinations (P4-05/P4-11)
# ---------------------------------------------------------------------------

@router.get("/api/settings/alert-destinations")
def get_alert_destinations(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    """Return alert delivery destinations for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    ad = settings.alert_destinations
    # Redact SMTP passwords in the response
    redacted_dests = []
    for d in ad.destinations:
        d_dict = {
            "id": d.id,
            "label": d.label,
            "enabled": d.enabled,
            "type": d.type,
            "url": d.url,
            "email_to": d.email_to,
            "email_cc": d.email_cc,
            "smtp_host": d.smtp_host,
            "smtp_port": d.smtp_port,
            "smtp_user": d.smtp_user,
            "smtp_use_tls": d.smtp_use_tls,
            "sender": d.sender,
            "min_severity": d.min_severity,
            "event_types": d.event_types,
            "has_smtp_password": bool(d.smtp_password),
        }
        redacted_dests.append(d_dict)
    return {
        "enabled": ad.enabled,
        "destinations": redacted_dests,
    }


@router.post("/api/settings/alert-destinations")
def update_alert_destinations(
    request: dict,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """Update alert delivery destinations. SMTP passwords are only updated if provided."""
    from src.intake.config.agency_settings import AlertDestinationsSettings, AlertDestination

    settings = AgencySettingsStore.load(agency_id)
    new_enabled = request.get("enabled", settings.alert_destinations.enabled)
    raw_dests = request.get("destinations", [])

    # Build destination list, preserving existing passwords when not provided
    existing_map = {d.id: d for d in settings.alert_destinations.destinations}
    destinations = []
    for raw in raw_dests:
        dest_id = raw.get("id", "")
        existing = existing_map.get(dest_id)
        destinations.append(AlertDestination(
            id=dest_id,
            label=raw.get("label", ""),
            enabled=raw.get("enabled", True),
            type=raw.get("type", "webhook"),
            url=raw.get("url", ""),
            email_to=raw.get("email_to", ""),
            email_cc=raw.get("email_cc", ""),
            smtp_host=raw.get("smtp_host", ""),
            smtp_port=raw.get("smtp_port", 25),
            smtp_user=raw.get("smtp_user", ""),
            smtp_password=raw.get("smtp_password") or (existing.smtp_password if existing else ""),
            smtp_use_tls=raw.get("smtp_use_tls", True),
            sender=raw.get("sender", "no-reply@waypoint.ai"),
            min_severity=raw.get("min_severity", "warning"),
            event_types=raw.get("event_types", []),
        ))

    settings.alert_destinations = AlertDestinationsSettings(
        enabled=new_enabled,
        destinations=destinations,
    )
    AgencySettingsStore.save(settings)

    # Hot-reload the per-agency guard so changes take effect immediately
    try:
        reload_guard_for_agency(agency_id)
    except Exception:
        logger.warning("Failed to hot-reload guard after alert destinations update (agency=%s)", agency_id)

    return {"ok": True}


@router.post("/api/settings/alert-destinations/test")
def test_alert_destination(
    request: dict,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """Send a test alert to a destination."""
    from src.llm.alert_service import AlertPayload, AlertEventType

    dest_type = request.get("type", "webhook")
    payload = AlertPayload(
        event_type=AlertEventType.THRESHOLD_WARNING,
        agency_id=agency_id,
        title="Test Alert",
        detail="This is a test alert from Waypoint AI to verify your alert destination configuration.",
        severity="warning",
    )

    if dest_type == "webhook":
        from src.llm.alert_service import WebhookChannel
        url = request.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="Webhook URL is required")
        channel = WebhookChannel([url])
        ok = channel.send(payload)
        return {"ok": ok, "detail": "Webhook delivered" if ok else "Webhook delivery failed"}

    elif dest_type == "email":
        from src.llm.alert_service import EmailChannel
        email_to = request.get("email_to", "")
        if not email_to:
            raise HTTPException(status_code=400, detail="Email recipient is required")
        recipients = [r.strip() for r in email_to.split(",") if r.strip()]
        channel = EmailChannel(
            recipients=recipients,
            sender=request.get("sender", "no-reply@waypoint.ai"),
            smtp_host=request.get("smtp_host", "localhost"),
            smtp_port=request.get("smtp_port", 25),
            smtp_user=request.get("smtp_user") or None,
            smtp_password=request.get("smtp_password") or None,
        )
        ok = channel.send(payload)
        return {"ok": ok, "detail": "Email sent" if ok else "Email delivery failed"}

    raise HTTPException(status_code=400, detail=f"Unknown destination type: {dest_type}")


# ---------------------------------------------------------------------------
# AI Agent Settings (P4-07)
# ---------------------------------------------------------------------------

@router.get("/api/settings/ai-agent")
def get_ai_agent_settings(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    """Return AI agent behavior settings for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    ai = settings.ai_agent
    return {
        "agency_id": settings.agency_id,
        "enable_auto_intake": ai.enable_auto_intake,
        "enable_auto_shortlist": ai.enable_auto_shortlist,
        "enable_auto_proposal": ai.enable_auto_proposal,
        "enable_auto_negotiation": ai.enable_auto_negotiation,
        "enable_frontier_orchestration": ai.enable_frontier_orchestration,
        "enable_checker_agent": ai.enable_checker_agent,
        "enable_call_capture": ai.enable_call_capture,
        "enable_document_extraction": ai.enable_document_extraction,
        "preferred_model": ai.preferred_model,
        "fallback_model": ai.fallback_model,
        "extraction_model": ai.extraction_model,
        "checker_model": ai.checker_model,
        "max_negotiation_rounds": ai.max_negotiation_rounds,
        "proposal_confidence_threshold": ai.proposal_confidence_threshold,
        "auto_advance_stages": ai.auto_advance_stages,
        "require_owner_review_above_value": ai.require_owner_review_above_value,
        "brand_voice": ai.brand_voice,
        "response_language": ai.response_language,
        "max_follow_up_questions": ai.max_follow_up_questions,
    }


@router.post("/api/settings/ai-agent")
def update_ai_agent_settings(
    request: UpdateAiAgentSettings,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """Update AI agent behavior settings for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    ai = settings.ai_agent

    if request.enable_auto_intake is not None:
        ai.enable_auto_intake = request.enable_auto_intake
    if request.enable_auto_shortlist is not None:
        ai.enable_auto_shortlist = request.enable_auto_shortlist
    if request.enable_auto_proposal is not None:
        ai.enable_auto_proposal = request.enable_auto_proposal
    if request.enable_auto_negotiation is not None:
        ai.enable_auto_negotiation = request.enable_auto_negotiation
    if request.enable_frontier_orchestration is not None:
        ai.enable_frontier_orchestration = request.enable_frontier_orchestration
    if request.enable_checker_agent is not None:
        ai.enable_checker_agent = request.enable_checker_agent
    if request.enable_call_capture is not None:
        ai.enable_call_capture = request.enable_call_capture
    if request.enable_document_extraction is not None:
        ai.enable_document_extraction = request.enable_document_extraction
    if request.preferred_model is not None:
        ai.preferred_model = request.preferred_model
    if request.fallback_model is not None:
        ai.fallback_model = request.fallback_model
    if request.extraction_model is not None:
        ai.extraction_model = request.extraction_model
    if request.checker_model is not None:
        ai.checker_model = request.checker_model
    if request.max_negotiation_rounds is not None:
        ai.max_negotiation_rounds = max(1, request.max_negotiation_rounds)
    if request.proposal_confidence_threshold is not None:
        ai.proposal_confidence_threshold = max(0.0, min(1.0, request.proposal_confidence_threshold))
    if request.auto_advance_stages is not None:
        ai.auto_advance_stages = request.auto_advance_stages
    if request.require_owner_review_above_value is not None:
        ai.require_owner_review_above_value = request.require_owner_review_above_value
    if request.brand_voice is not None:
        if request.brand_voice in ("professional", "friendly", "luxury", "budget"):
            ai.brand_voice = request.brand_voice
    if request.response_language is not None:
        ai.response_language = request.response_language
    if request.max_follow_up_questions is not None:
        ai.max_follow_up_questions = max(0, request.max_follow_up_questions)

    AgencySettingsStore.save(settings)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Support Settings (P4-08)
# ---------------------------------------------------------------------------

@router.get("/api/settings/support")
def get_support_settings(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    """Return support channel configuration for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    s = settings.support
    return {
        "agency_id": settings.agency_id,
        "enable_email_support": s.enable_email_support,
        "enable_chat_support": s.enable_chat_support,
        "enable_phone_support": s.enable_phone_support,
        "enable_whatsapp_support": s.enable_whatsapp_support,
        "default_response_sla_hours": s.default_response_sla_hours,
        "urgent_response_sla_hours": s.urgent_response_sla_hours,
        "auto_route_by_destination": s.auto_route_by_destination,
        "auto_route_by_language": s.auto_route_by_language,
        "escalation_after_sla_breach": s.escalation_after_sla_breach,
        "escalation_contact_email": s.escalation_contact_email,
        "escalation_contact_phone": s.escalation_contact_phone,
        "support_hours_start": s.support_hours_start,
        "support_hours_end": s.support_hours_end,
        "support_days": s.support_days,
        "timezone": s.timezone,
        "enable_auto_acknowledgement": s.enable_auto_acknowledgement,
        "auto_acknowledgement_message": s.auto_acknowledgement_message,
        "out_of_hours_message": s.out_of_hours_message,
        "enable_csat_survey": s.enable_csat_survey,
        "csat_trigger": s.csat_trigger,
    }


@router.post("/api/settings/support")
def update_support_settings(
    request: UpdateSupportSettings,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """Update support channel configuration for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    s = settings.support

    if request.enable_email_support is not None:
        s.enable_email_support = request.enable_email_support
    if request.enable_chat_support is not None:
        s.enable_chat_support = request.enable_chat_support
    if request.enable_phone_support is not None:
        s.enable_phone_support = request.enable_phone_support
    if request.enable_whatsapp_support is not None:
        s.enable_whatsapp_support = request.enable_whatsapp_support
    if request.default_response_sla_hours is not None:
        s.default_response_sla_hours = max(1, request.default_response_sla_hours)
    if request.urgent_response_sla_hours is not None:
        s.urgent_response_sla_hours = max(1, request.urgent_response_sla_hours)
    if request.auto_route_by_destination is not None:
        s.auto_route_by_destination = request.auto_route_by_destination
    if request.auto_route_by_language is not None:
        s.auto_route_by_language = request.auto_route_by_language
    if request.escalation_after_sla_breach is not None:
        s.escalation_after_sla_breach = request.escalation_after_sla_breach
    if request.escalation_contact_email is not None:
        s.escalation_contact_email = request.escalation_contact_email
    if request.escalation_contact_phone is not None:
        s.escalation_contact_phone = request.escalation_contact_phone
    if request.support_hours_start is not None:
        s.support_hours_start = request.support_hours_start
    if request.support_hours_end is not None:
        s.support_hours_end = request.support_hours_end
    if request.support_days is not None:
        s.support_days = request.support_days
    if request.timezone is not None:
        s.timezone = request.timezone
    if request.enable_auto_acknowledgement is not None:
        s.enable_auto_acknowledgement = request.enable_auto_acknowledgement
    if request.auto_acknowledgement_message is not None:
        s.auto_acknowledgement_message = request.auto_acknowledgement_message
    if request.out_of_hours_message is not None:
        s.out_of_hours_message = request.out_of_hours_message
    if request.enable_csat_survey is not None:
        s.enable_csat_survey = request.enable_csat_survey
    if request.csat_trigger is not None:
        if request.csat_trigger in ("after_resolution", "after_first_response", "never"):
            s.csat_trigger = request.csat_trigger

    AgencySettingsStore.save(settings)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Communication Settings (P4-09)
# ---------------------------------------------------------------------------

@router.get("/api/settings/comm")
def get_comm_settings(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    """Return communication preferences for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    c = settings.comm
    return {
        "agency_id": settings.agency_id,
        "default_outbound_channel": c.default_outbound_channel,
        "allow_channel_switching": c.allow_channel_switching,
        "enable_template_library": c.enable_template_library,
        "default_greeting": c.default_greeting,
        "default_sign_off": c.default_sign_off,
        "respect_operating_hours": c.respect_operating_hours,
        "send_immediately_during_hours": c.send_immediately_during_hours,
        "queue_outside_hours": c.queue_outside_hours,
        "max_emails_per_day_per_trip": c.max_emails_per_day_per_trip,
        "max_whatsapp_per_day_per_trip": c.max_whatsapp_per_day_per_trip,
        "auto_detect_language": c.auto_detect_language,
        "default_language": c.default_language,
        "supported_languages": c.supported_languages,
        "translate_outbound": c.translate_outbound,
        "enable_auto_followup": c.enable_auto_followup,
        "auto_followup_delay_days": c.auto_followup_delay_days,
        "max_auto_followups": c.max_auto_followups,
        "followup_escalate_after_max": c.followup_escalate_after_max,
        "notify_on_customer_reply": c.notify_on_customer_reply,
        "notify_on_sla_warning": c.notify_on_sla_warning,
        "notify_on_escalation": c.notify_on_escalation,
        "digest_frequency": c.digest_frequency,
        "include_agency_signature": c.include_agency_signature,
        "include_unsubscribe_link": c.include_unsubscribe_link,
        "compliance_footer": c.compliance_footer,
    }


@router.post("/api/settings/comm")
def update_comm_settings(
    request: UpdateCommSettings,
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:write"),
):
    """Update communication preferences for the agency."""
    settings = AgencySettingsStore.load(agency_id)
    c = settings.comm

    if request.default_outbound_channel is not None:
        if request.default_outbound_channel in ("email", "whatsapp", "sms"):
            c.default_outbound_channel = request.default_outbound_channel
    if request.allow_channel_switching is not None:
        c.allow_channel_switching = request.allow_channel_switching
    if request.enable_template_library is not None:
        c.enable_template_library = request.enable_template_library
    if request.default_greeting is not None:
        c.default_greeting = request.default_greeting
    if request.default_sign_off is not None:
        c.default_sign_off = request.default_sign_off
    if request.respect_operating_hours is not None:
        c.respect_operating_hours = request.respect_operating_hours
    if request.send_immediately_during_hours is not None:
        c.send_immediately_during_hours = request.send_immediately_during_hours
    if request.queue_outside_hours is not None:
        c.queue_outside_hours = request.queue_outside_hours
    if request.max_emails_per_day_per_trip is not None:
        c.max_emails_per_day_per_trip = max(0, request.max_emails_per_day_per_trip)
    if request.max_whatsapp_per_day_per_trip is not None:
        c.max_whatsapp_per_day_per_trip = max(0, request.max_whatsapp_per_day_per_trip)
    if request.auto_detect_language is not None:
        c.auto_detect_language = request.auto_detect_language
    if request.default_language is not None:
        c.default_language = request.default_language
    if request.supported_languages is not None:
        c.supported_languages = request.supported_languages
    if request.translate_outbound is not None:
        c.translate_outbound = request.translate_outbound
    if request.enable_auto_followup is not None:
        c.enable_auto_followup = request.enable_auto_followup
    if request.auto_followup_delay_days is not None:
        c.auto_followup_delay_days = max(1, request.auto_followup_delay_days)
    if request.max_auto_followups is not None:
        c.max_auto_followups = max(0, request.max_auto_followups)
    if request.followup_escalate_after_max is not None:
        c.followup_escalate_after_max = request.followup_escalate_after_max
    if request.notify_on_customer_reply is not None:
        c.notify_on_customer_reply = request.notify_on_customer_reply
    if request.notify_on_sla_warning is not None:
        c.notify_on_sla_warning = request.notify_on_sla_warning
    if request.notify_on_escalation is not None:
        c.notify_on_escalation = request.notify_on_escalation
    if request.digest_frequency is not None:
        if request.digest_frequency in ("realtime", "hourly", "daily", "never"):
            c.digest_frequency = request.digest_frequency
    if request.include_agency_signature is not None:
        c.include_agency_signature = request.include_agency_signature
    if request.include_unsubscribe_link is not None:
        c.include_unsubscribe_link = request.include_unsubscribe_link
    if request.compliance_footer is not None:
        c.compliance_footer = request.compliance_footer

    AgencySettingsStore.save(settings)
    return {"ok": True}


@router.get("/api/settings/pipeline")
def get_pipeline_stages():
    """Get pipeline stage configuration."""
    stages = ConfigStore.get_pipeline_stages()
    return {"items": stages}


@router.put("/api/settings/pipeline")
def set_pipeline_stages(request: List[PipelineStageConfig]):
    """Update pipeline stage configuration."""
    ConfigStore.set_pipeline_stages([s.model_dump() for s in request])
    return {"success": True}


@router.get("/api/settings/approvals")
def get_approval_thresholds():
    """Get approval threshold configuration."""
    thresholds = ConfigStore.get_approval_thresholds()
    return {"items": thresholds}


@router.put("/api/settings/approvals")
def set_approval_thresholds(request: List[ApprovalThresholdConfig]):
    """Update approval threshold configuration."""
    ConfigStore.set_approval_thresholds([t.model_dump() for t in request])
    return {"success": True}
