"""
Settings router.

Owns agency profile/operational/autonomy settings plus pipeline and approval
configuration endpoints. Extracted from ``spine_api.server`` so the FastAPI app
shell can keep moving toward route-module ownership without changing contracts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException

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
    UpdateAutonomyPolicy,
    UpdateSeasonalCampaignRequest,
    UpdateOperationalSettings,
    UpdateSeasonalPolicy,
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

    projected_leads = int(base_budget * max(1.0, mix_weight + 0.5) * month_window / 900)
    projected_bookings = max(1, int(projected_leads * 0.42))
    projected_margin_pct = max(0.0, min(42.0, 8.0 + (base_budget / 2000.0)))
    confidence = 0.72 if request.scenario == "baseline" else 0.66

    return {
        "plan_id": plan_id,
        "scenario": request.scenario,
        "projected_leads": projected_leads,
        "projected_bookings": projected_bookings,
        "projected_margin_pct": round(projected_margin_pct, 2),
        "confidence": round(confidence, 3),
        "notes": _build_simulation_notes(plan, request.scenario),
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
