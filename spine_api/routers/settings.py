"""
Settings router.

Owns agency profile/operational/autonomy settings plus pipeline and approval
configuration endpoints. Extracted from ``spine_api.server`` so the FastAPI app
shell can keep moving toward route-module ownership without changing contracts.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from spine_api.contract import (
    ApprovalThresholdConfig,
    PipelineStageConfig,
    UpdateAutonomyPolicy,
    UpdateOperationalSettings,
)
from spine_api.core.auth import require_permission
from src.intake.config.agency_settings import AgencySettingsStore

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

ConfigStore = persistence.ConfigStore

router = APIRouter()


@router.get("/api/settings")
def get_agency_settings(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
):
    """Return the complete agency configuration (profile + operational + autonomy)."""
    settings = AgencySettingsStore.load(agency_id)
    return {
        "agency_id": settings.agency_id,
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
    changes: list[str] = []

    if request.agency_name is not None:
        settings.agency_name = request.agency_name
        changes.append("agency_name")
    if request.sub_brand is not None:
        settings.sub_brand = request.sub_brand
        changes.append("sub_brand")
    if request.plan_label is not None:
        settings.plan_label = request.plan_label
        changes.append("plan_label")
    if request.contact_email is not None:
        settings.contact_email = request.contact_email
        changes.append("contact_email")
    if request.contact_phone is not None:
        settings.contact_phone = request.contact_phone
        changes.append("contact_phone")
    if request.logo_url is not None:
        settings.logo_url = request.logo_url
        changes.append("logo_url")
    if request.website is not None:
        settings.website = request.website
        changes.append("website")

    if request.target_margin_pct is not None:
        settings.target_margin_pct = request.target_margin_pct
        changes.append("target_margin_pct")
    if request.default_currency is not None:
        settings.default_currency = request.default_currency
        changes.append("default_currency")
    if request.operating_hours_start is not None:
        settings.operating_hours_start = request.operating_hours_start
        changes.append("operating_hours_start")
    if request.operating_hours_end is not None:
        settings.operating_hours_end = request.operating_hours_end
        changes.append("operating_hours_end")
    if request.operating_days is not None:
        settings.operating_days = request.operating_days
        changes.append("operating_days")
    if request.preferred_channels is not None:
        settings.preferred_channels = request.preferred_channels
        changes.append("preferred_channels")
    if request.brand_tone is not None:
        settings.brand_tone = request.brand_tone
        changes.append("brand_tone")

    AgencySettingsStore.save(settings)

    return {
        "agency_id": settings.agency_id,
        "changes": changes,
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
    }


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
    changes: list[str] = []

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
        changes.append("approval_gates")

    if request.mode_overrides is not None:
        policy.mode_overrides = {
            k: dict(v) if isinstance(v, dict) else {}
            for k, v in request.mode_overrides.items()
        }
        changes.append("mode_overrides")

    if request.auto_proceed_with_warnings is not None:
        policy.auto_proceed_with_warnings = request.auto_proceed_with_warnings
        changes.append("auto_proceed_with_warnings")

    if request.learn_from_overrides is not None:
        policy.learn_from_overrides = request.learn_from_overrides
        changes.append("learn_from_overrides")

    if request.auto_reprocess_on_edit is not None:
        policy.auto_reprocess_on_edit = request.auto_reprocess_on_edit
        changes.append("auto_reprocess_on_edit")

    if request.allow_explicit_reassess is not None:
        policy.allow_explicit_reassess = request.allow_explicit_reassess
        changes.append("allow_explicit_reassess")

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
        changes.append("auto_reprocess_stages")

    AgencySettingsStore.save(settings)

    return {
        "agency_id": settings.agency_id,
        "approval_gates": policy.approval_gates,
        "mode_overrides": policy.mode_overrides,
        "auto_proceed_with_warnings": policy.auto_proceed_with_warnings,
        "learn_from_overrides": policy.learn_from_overrides,
        "auto_reprocess_on_edit": policy.auto_reprocess_on_edit,
        "allow_explicit_reassess": policy.allow_explicit_reassess,
        "auto_reprocess_stages": policy.auto_reprocess_stages,
        "changes": changes,
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
