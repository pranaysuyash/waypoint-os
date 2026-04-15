"""
Operator Workbench — Agency Flow Simulator (Streamlit App).

THIN APP CONTRACT:
- All spine logic lives in src/intake/orchestration.py (run_spine_once)
- This app only calls run_spine_once and displays results
- Switching tabs must NOT rerun the spine
- Spine reruns ONLY when "Run Spine" is clicked or a fixture is loaded/run
- Last successful outputs are held in st.session_state

Five-screen information architecture:
1. Intake — raw input, packet display, validation
2. Decision — decision state, confidence, blockers, risk flags
3. Strategy — session strategy, prompt bundles (internal + traveler)
4. Safety — raw packet → sanitized view → traveler bundle (3-panel)
5. Flow Simulation — scenario fixtures, compare mode, system summary
"""

import json
import os
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path so src.intake imports work
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.intake.orchestration import run_spine_once, SpineResult
from src.intake.packet_models import SourceEnvelope


# =============================================================================
# SECTION 1: PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Operator Workbench",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# SECTION 2: SESSION STATE INITIALIZATION
# =============================================================================
# CRITICAL: These fields hold the last successful spine outputs.
# Switching tabs must NOT rerun the spine — only display stored state.

def init_session_state():
    """Initialize all session state keys with defaults."""
    defaults = {
        # Spine outputs (populated after run)
        "spine_result": None,
        "last_run_timestamp": None,
        "last_run_inputs": None,
        # Current input
        "raw_note": "",
        "owner_note": "",
        "selected_mode": "normal_intake",
        "selected_stage": "discovery",
        # Settings
        "strict_mode": False,
        # Fixture compare
        "selected_fixture": None,
        "compare_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# =============================================================================
# SECTION 3: SIDEBAR — INPUT & CONTROLS
# =============================================================================

with st.sidebar:
    st.header("🧳 Operator Workbench")
    st.caption("Agency Flow Simulator — v0.1.0")

    st.divider()

    # Mode and stage selection
    st.subheader("Configuration")
    st.session_state.selected_mode = st.selectbox(
        "Operating Mode",
        options=["normal_intake", "audit", "emergency", "follow_up", "cancellation", "post_trip", "coordinator_group", "owner_review"],
        index=["normal_intake", "audit", "emergency", "follow_up", "cancellation", "post_trip", "coordinator_group", "owner_review"].index(st.session_state.selected_mode),
    )
    st.session_state.selected_stage = st.selectbox(
        "Stage",
        options=["discovery", "shortlist", "proposal", "booking"],
        index=["discovery", "shortlist", "proposal", "booking"].index(st.session_state.selected_stage),
    )

    st.divider()

    # Strict mode toggle
    st.session_state.strict_mode = st.toggle(
        "Strict Mode",
        value=st.session_state.strict_mode,
        help="When enabled, leakage detection blocks traveler output and marks runs as failed.",
    )

    st.divider()

    # Raw input
    st.subheader("Input")
    st.session_state.raw_note = st.text_area(
        "Raw Note",
        value=st.session_state.raw_note,
        height=150,
        placeholder="Paste agency notes, traveler messages, or CRM entries...",
    )
    st.session_state.owner_note = st.text_area(
        "Owner Note (optional)",
        value=st.session_state.owner_note,
        height=80,
        placeholder="Internal owner instructions...",
    )

    st.divider()

    # Run button — THIS is the only trigger for spine execution
    run_clicked = st.button(
        "▶ Run Spine",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    # Last run info
    if st.session_state.last_run_timestamp:
        st.caption(f"Last run: `{st.session_state.last_run_timestamp}`")
    else:
        st.caption("No spine run yet")


# =============================================================================
# SECTION 4: SPINE EXECUTION (only on button click or fixture load)
# =============================================================================

def execute_spine(raw_note: str, owner_note: str, mode: str, stage: str) -> SpineResult:
    """
    Build envelopes and call run_spine_once.
    This is the ONLY place the spine is invoked.
    """
    envelopes = []

    # Primary raw note envelope
    if raw_note.strip():
        envelopes.append(SourceEnvelope.from_freeform(
            text=raw_note.strip(),
            source="agency_notes",
            actor="agent",
        ))

    # Owner note envelope (if present)
    if owner_note.strip():
        envelopes.append(SourceEnvelope.from_freeform(
            text=owner_note.strip(),
            source="agency_notes",
            actor="owner",
        ))

    if not envelopes:
        st.error("No input provided. Enter a raw note or load a fixture.")
        return None

    # Set strict mode in safety module
    from src.intake.safety import set_strict_mode
    set_strict_mode(st.session_state.strict_mode)

    return run_spine_once(
        envelopes=envelopes,
        stage=stage,
        operating_mode=mode,
    )


if run_clicked:
    with st.spinner("Running spine..."):
        result = execute_spine(
            raw_note=st.session_state.raw_note,
            owner_note=st.session_state.owner_note,
            mode=st.session_state.selected_mode,
            stage=st.session_state.selected_stage,
        )
        if result is not None:
            st.session_state.spine_result = result
            st.session_state.last_run_timestamp = result.run_timestamp
            st.session_state.last_run_inputs = {
                "raw_note": st.session_state.raw_note,
                "owner_note": st.session_state.owner_note,
            }
            st.success(f"Spine completed at {result.run_timestamp}")


# =============================================================================
# SECTION 5: TAB NAVIGATION (no rerun on tab switch)
# =============================================================================

tab_intake, tab_decision, tab_strategy, tab_safety, tab_flow = st.tabs([
    "① Intake",
    "② Decision",
    "③ Strategy",
    "④ Safety",
    "⑤ Flow Simulation",
])


# =============================================================================
# SECTION 6: TAB 1 — INTAKE
# =============================================================================

with tab_intake:
    st.header("Intake & Packet Display")

    if st.session_state.spine_result is None:
        st.info("Run the spine to see packet and validation results here.")
    else:
        result: SpineResult = st.session_state.spine_result

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("CanonicalPacket")
            st.json(result.packet.to_dict(), expanded=False)

        with col_b:
            st.subheader("Validation Report")
            val = result.validation
            if val.is_valid:
                st.success("✅ Valid")
            else:
                st.error(f"❌ Invalid — {val.error_count} error(s)")

            if val.errors:
                for err in val.errors:
                    st.error(f"**{err.code}** ({err.field}): {err.message}")
            if val.warnings:
                for warn in val.warnings:
                    st.warning(f"**{warn.code}** ({warn.field}): {warn.message}")


# =============================================================================
# SECTION 7: TAB 2 — DECISION
# =============================================================================

with tab_decision:
    st.header("Decision State")

    if st.session_state.spine_result is None:
        st.info("Run the spine to see decision results here.")
    else:
        result: SpineResult = st.session_state.spine_result
        dec = result.decision

        # Decision state badge
        state_colors = {
            "ASK_FOLLOWUP": "orange",
            "PROCEED_INTERNAL_DRAFT": "blue",
            "PROCEED_TRAVELER_SAFE": "green",
            "BRANCH_OPTIONS": "purple",
            "STOP_NEEDS_REVIEW": "red",
        }
        color = state_colors.get(dec.decision_state, "gray")
        st.markdown(f"**Decision State:** `:{color}[{dec.decision_state}]`")
        st.metric("Confidence", f"{dec.confidence_score:.2f}")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.subheader("Hard Blockers")
            if dec.hard_blockers:
                for b in dec.hard_blockers:
                    st.error(f"🔴 {b}")
            else:
                    st.success("None")

        with col_b:
            st.subheader("Soft Blockers")
            if dec.soft_blockers:
                for b in dec.soft_blockers:
                    st.warning(f"🟡 {b}")
            else:
                    st.success("None")

        with col_c:
            st.subheader("Risk Flags")
            if dec.risk_flags:
                for r in dec.risk_flags:
                    msg = r.get("message", r.get("flag", str(r)))
                    st.warning(f"⚠️ {msg}")
            else:
                    st.success("None")

        # Follow-up questions (if ASK_FOLLOWUP)
        if dec.follow_up_questions:
            st.subheader("Follow-Up Questions")
            for q in dec.follow_up_questions:
                priority = q.get("priority", "medium")
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(priority, "⚪")
                st.markdown(f"{icon} **{q.get('field_name')}**: {q.get('question', '')}")

        # Rationale
        if dec.rationale:
            st.subheader("Rationale")
            st.json(dec.rationale, expanded=False)


# =============================================================================
# SECTION 8: TAB 3 — STRATEGY
# =============================================================================

with tab_strategy:
    st.header("Session Strategy & Prompt Bundles")

    if st.session_state.spine_result is None:
        st.info("Run the spine to see strategy and bundles here.")
    else:
        result: SpineResult = st.session_state.spine_result
        strat = result.strategy

        st.subheader("Session Strategy")
        st.markdown(f"**Goal:** {strat.session_goal}")
        st.markdown(f"**Suggested Opening:** {strat.suggested_opening}")
        st.markdown(f"**Tone:** `{strat.suggested_tone}`")

        if strat.priority_sequence:
            st.markdown("**Priority Sequence:**")
            for i, step in enumerate(strat.priority_sequence, 1):
                st.markdown(f"{i}. {step}")

        if strat.exit_criteria:
            st.markdown("**Exit Criteria:**")
            for c in strat.exit_criteria:
                st.markdown(f"- {c}")

        st.divider()

        # Internal bundle
        st.subheader("Internal Bundle (Agent-Only)")
        ib = result.internal_bundle
        st.markdown("**System Context:**")
        st.code(ib.system_context, language=None)
        st.markdown("**User Message:**")
        st.code(ib.user_message, language=None)
        if ib.internal_notes:
            st.markdown("**Internal Notes:**")
            st.info(ib.internal_notes)

        st.divider()

        # Traveler bundle
        st.subheader("Traveler-Safe Bundle")
        tb = result.traveler_bundle
        st.markdown("**System Context:**")
        st.code(tb.system_context, language=None)
        st.markdown("**User Message:**")
        st.code(tb.user_message, language=None)


# =============================================================================
# SECTION 9: TAB 4 — SAFETY (3-PANEL: raw → sanitized → traveler)
# =============================================================================

with tab_safety:
    st.header("Safety & Leakage Check")
    st.caption("Boundary transformation: Raw Packet → Sanitized View → Traveler Bundle")

    if st.session_state.spine_result is None:
        st.info("Run the spine to see safety analysis here.")
    else:
        result: SpineResult = st.session_state.spine_result

        # Strict mode leakage check
        leakage = result.leakage_result
        is_safe = leakage.get("is_safe", True)

        if st.session_state.strict_mode and not is_safe:
            # STRICT MODE: Block traveler output
            st.error("🚫 **STRICT MODE: TRAVELER OUTPUT BLOCKED**")
            leaks = leakage.get("leaks", [])
            st.error(f"**{len(leaks)} leakage term(s) detected:**")
            for leak in leaks:
                st.error(f"• {leak}")
            st.warning("Traveler-safe preview is suppressed in strict mode.")
        else:
            # Normal mode or safe: show results
            if is_safe:
                st.success("✅ No leakage detected — output is traveler-safe")
            else:
                st.warning(f"⚠️ {len(leakage.get('leaks', []))} potential leakage term(s) — review below")

        # Three-panel layout: raw → sanitized → traveler
        col_raw, col_sanitized, col_traveler = st.columns(3)

        with col_raw:
            st.subheader("1. Raw Packet")
            st.caption("Full packet with all internal data, hypotheses, contradictions")
            st.json(result.packet.to_dict(), expanded=False)

        with col_sanitized:
            st.subheader("2. Sanitized View")
            st.caption("Filtered facts + safe derived signals only")
            st.json(result.sanitized_view.to_dict(), expanded=False)

        with col_traveler:
            st.subheader("3. Traveler Bundle")
            st.caption("Final output to traveler (user_message + system_context)")
            if st.session_state.strict_mode and not is_safe:
                st.error("**STRICT MODE: OUTPUT BLOCKED**")
                st.warning("This bundle contains leaked terms and is not shown.")
            else:
                tb = result.traveler_bundle
                st.markdown("**User Message:**")
                st.code(tb.user_message, language=None)
                st.markdown("**System Context:**")
                st.code(tb.system_context, language=None)
                if tb.follow_up_sequence:
                    st.markdown("**Follow-Up Sequence:**")
                    for step in tb.follow_up_sequence:
                        st.markdown(f"- {step}")


# =============================================================================
# SECTION 10: TAB 5 — FLOW SIMULATION
# =============================================================================

with tab_flow:
    st.header("Flow Simulation — Scenario Fixtures")

    # Fixture loader
    fixtures_dir = PROJECT_ROOT / "data" / "fixtures" / "scenarios"
    fixtures = {}
    if fixtures_dir.exists():
        for fname in sorted(fixtures_dir.glob("*.json")):
            try:
                with open(fname) as f:
                    fixture = json.load(f)
                fixtures[fixture["scenario_id"]] = fixture
            except (json.JSONDecodeError, KeyError):
                continue

    if fixtures:
        selected_id = st.selectbox(
            "Select Scenario Fixture",
            options=list(fixtures.keys()),
            format_func=lambda sid: f"{sid}: {fixtures[sid]['title']}",
        )
        if selected_id:
            fixture = fixtures[selected_id]
            st.json(fixture, expanded=False)

        col_run, col_compare = st.columns(2)
        with col_run:
            load_and_run = st.button(
                "▶ Load & Run Fixture",
                type="primary",
                use_container_width=True,
            )
        with col_compare:
            st.session_state.compare_mode = st.toggle(
                "Compare Mode",
                value=st.session_state.compare_mode,
            )

        if load_and_run and selected_id:
            fixture = fixtures[selected_id]
            inputs = fixture["inputs"]
            expectations = fixture.get("expected", {})

            with st.spinner(f"Running fixture {selected_id}..."):
                result = execute_spine(
                    raw_note=inputs.get("raw_note", ""),
                    owner_note=inputs.get("owner_note") or "",
                    mode=fixture.get("mode", "normal_intake"),
                    stage=fixture.get("stage", "discovery"),
                )
                if result is not None:
                    # Run fixture compare
                    from src.intake.orchestration import _compare_against_fixture
                    assertion = _compare_against_fixture(
                        packet=result.packet,
                        decision=result.decision,
                        traveler_bundle=result.traveler_bundle,
                        leakage_result=result.leakage_result,
                        expectations=expectations,
                    )
                    result.assertion_result = assertion

                    st.session_state.spine_result = result
                    st.session_state.last_run_timestamp = result.run_timestamp
                    st.session_state.selected_fixture = selected_id

                    if assertion["passed"]:
                        st.success(f"✅ Fixture {selected_id}: {assertion['summary']}")
                    else:
                        st.error(f"❌ Fixture {selected_id}: {assertion['summary']}")
                        for a in assertion["assertions"]:
                            if not a["passed"]:
                                st.error(f"• {a['type']} ({a.get('field', '')}): {a['message']}")

    else:
        st.info("No scenario fixtures found in data/fixtures/scenarios/")

    # System understanding summary (derived from spine outputs only)
    if st.session_state.spine_result is not None:
        result: SpineResult = st.session_state.spine_result

        st.divider()
        st.subheader("System Understanding Summary")
        st.caption("Derived from spine outputs only — no separate UI inference")

        summary_parts = []

        # From packet
        p = result.packet
        summary_parts.append(f"**Packet:** {p.packet_id} | Stage: {p.stage} | Mode: {p.operating_mode}")
        summary_parts.append(f"  - Facts: {len(p.facts)} fields extracted")
        summary_parts.append(f"  - Ambiguities: {len(p.ambiguities)}")
        summary_parts.append(f"  - Contradictions: {len(p.contradictions)}")

        # From validation
        v = result.validation
        summary_parts.append(f"**Validation:** {'✅ Valid' if v.is_valid else f'❌ Invalid ({v.error_count} errors, {v.warning_count} warnings)'}")

        # From decision
        d = result.decision
        summary_parts.append(f"**Decision:** `{d.decision_state}` (confidence: {d.confidence_score:.2f})")
        if d.hard_blockers:
            summary_parts.append(f"  - Hard blockers: {', '.join(d.hard_blockers)}")
        if d.follow_up_questions:
            summary_parts.append(f"  - Follow-up questions: {len(d.follow_up_questions)}")

        # From strategy
        s = result.strategy
        summary_parts.append(f"**Strategy:** {s.session_goal}")
        summary_parts.append(f"  - Opening: {s.suggested_opening}")

        st.markdown("\n".join(summary_parts))

        # Assertion result (if compare mode)
        if st.session_state.compare_mode and result.assertion_result is not None:
            st.divider()
            st.subheader("Compare Results")
            ar = result.assertion_result
            if ar["passed"]:
                st.success(f"✅ {ar['summary']}")
            else:
                st.error(f"❌ {ar['summary']}")
                for a in ar["assertions"]:
                    if not a["passed"]:
                        st.error(f"• {a['type']}: {a['message']}")


# =============================================================================
# SECTION 11: FOOTER
# =============================================================================

st.divider()
st.caption(
    "Operator Workbench v0.1.0 | "
    "Spine: src/intake/orchestration.py | "
    "Fixtures: data/fixtures/scenarios/ | "
    "Specs: specs/scenario_fixture.schema.json"
)
