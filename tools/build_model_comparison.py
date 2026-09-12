#!/usr/bin/env python3
"""Build the full model-comparison sheet from KDD lane runs + run manifest.

Every model ever tested in the hybrid risk-flag lane appears here — kept,
deleted, failed, or partial — so no result is lost when models are pruned
from the local store. Grades come from the per-run JSONL files (graded live by
tools/grade_kdd_flags.py logic); metadata (tier, size, cost, status, notes)
comes from the curated manifest below.

Usage:
    python3 tools/build_model_comparison.py            # writes CSV + MD
    # outputs: data/experiments/hybrid_kdd_v1/comparison_sheet.csv
    #          Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md (table block)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from grade_kdd_flags import load_labels, grade_arm  # noqa: E402

RUNS = REPO / "data/experiments/hybrid_kdd_v1"
LABELS_PATH = REPO / "data/fixtures/risk_flags/ground_truth_labels.json"

# Curated run manifest: one row per model arm ever run. status ∈
# kept | deleted | partial-killed | blocked | failed-run.
# Sizes: GB on disk (local) or "-" (API). cost = ₹ per cold run (API only).
MANIFEST: List[Dict[str, Any]] = [
    # --- API ladder (post-fix grades where re-run; pre-fix noted) ---
    {"id": "gpt-5.4-nano",    "tier": "API", "size": "-", "cost": 0.28,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.4-nano",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.4-nano",
     "notes": "Co-champion overall (F1 0.909 post-fix); cheapest tier"},
    {"id": "gpt-4.1-nano",    "tier": "API", "size": "-", "cost": 0.09,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-4.1-nano",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-4.1-nano",
     "notes": "Co-champion overall (F1 0.909 post-fix)"},
    {"id": "gpt-5.6-terra",   "tier": "API", "size": "-", "cost": 2.32,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.6-terra",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.6-terra", "notes": "F1 0.857"},
    {"id": "gpt-5.1",         "tier": "API", "size": "-", "cost": 2.70,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.1",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.1", "notes": "F1 0.857"},
    {"id": "gpt-6-astra",     "tier": "API", "size": "-", "cost": 11.45, "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-6-astra",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-6-astra",
     "notes": "Flagship: F1 0.829 — no advantage over nanos at 40× cost"},
    {"id": "gpt-5-mini",      "tier": "API", "size": "-", "cost": 0.58,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5-mini",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5-mini", "notes": "15.9s/call (reasoning)"},
    {"id": "gpt-5.2",         "tier": "API", "size": "-", "cost": 3.15,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.2",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.2", "notes": ""},
    {"id": "gpt-5.4",         "tier": "API", "size": "-", "cost": 3.26,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.4",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.4", "notes": ""},
    {"id": "gpt-4.1-mini",    "tier": "API", "size": "-", "cost": 0.38,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-4.1-mini",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-4.1-mini", "notes": "sev 1.00"},
    {"id": "o4-mini",         "tier": "API", "size": "-", "cost": 0.90,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-o4-mini",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-o4-mini", "notes": ""},
    {"id": "gpt-4o-mini",     "tier": "API", "size": "-", "cost": 0.11,  "status": "kept-api",
     "run": "records_final_single.jsonl", "arm": "B-gpt-4o-mini",
     "notes": "Cheapest acceptable (F1 0.857 pre-ladder2; 0.769 in patterns run — run variance)"},
    {"id": "gpt-5.6-luna",    "tier": "API", "size": "-", "cost": 0.23,  "status": "kept-api",
     "run": "records_final_single.jsonl", "arm": "B-gpt-5.6-luna", "notes": "F1 0.545 post-fix"},
    {"id": "gpt-4o",          "tier": "API", "size": "-", "cost": 2.10,  "status": "kept-api",
     "run": "records.jsonl", "arm": "B-gpt-4o",
     "notes": "PRE-FIX run (records.jsonl): grade includes the 11 fabricated "
              "default-flags, hence P=0.5 — kept for lineage only; post-fix "
              "equivalent is the nano tier (same quality at 1/10 cost)"},
    {"id": "gpt-4.1",         "tier": "API", "size": "-", "cost": 1.87,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-4.1",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-4.1", "notes": ""},
    {"id": "gpt-5.4-mini",    "tier": "API", "size": "-", "cost": 0.96,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.4-mini",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.4-mini", "notes": ""},
    {"id": "gpt-3.5-turbo",   "tier": "API", "size": "-", "cost": 0.27,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-3.5-turbo",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-3.5-turbo", "notes": "2022 baseline"},
    {"id": "gpt-4-turbo",     "tier": "API", "size": "-", "cost": 7.10,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-4-turbo",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-4-turbo",
     "notes": "Most conservative ladder model (under-flags)"},
    {"id": "gpt-5.5",         "tier": "API", "size": "-", "cost": 5.99,  "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5.5",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5.5",
     "notes": "Flagship under-flags: F1 0.154 — anti-recommendation"},
    {"id": "gpt-5-nano",      "tier": "API", "size": "-", "cost": 0.009, "status": "kept-api",
     "run": "records_ladder2.jsonl", "arm": "B-gpt-5-nano",
     "run_prefix": "records_ladder.jsonl", "arm_prefix": "B-gpt-5-nano",
     "notes": "Cache-collapse anomaly (2 escalations → all-cache replay)"},
    # --- Local: old stock (2024-era, tested 2026-09-12) ---
    {"id": "llama3.2:3b",     "tier": "local-8GB", "size": "2.0", "cost": 0.0, "status": "kept",
     "run": "records_loc_llama32_3b.jsonl", "arm": "B-llama3.2:3b",
     "notes": "LOCAL CHAMPION — recommended local default; deleted from store 2026-09-12 (all hosted alternatives beat it; re-pull one-command)"},
    {"id": "gemma3:12b",      "tier": "local-16GB", "size": "8.1", "cost": 0.0, "status": "kept",
     "run": "records_local_ladder.jsonl", "arm": "B-gemma3:12b",
     "notes": "16GB-tier representative; deleted from store 2026-09-12 (tested+graded, zero code refs)"},
    {"id": "qwen2.5vl:7b",    "tier": "local-vision", "size": "6.0", "cost": 0.0, "status": "kept",
     "run": "records_ollama.jsonl", "arm": "B-qwen2.5vl:7b",
     "notes": "Deleted from store 2026-09-12 (zero code references found; was kept as vision-coupled precaution); re-pull if multimodal extraction needs a local VLM"},
    {"id": "gemma3:4b",       "tier": "local-8GB", "size": "3.3", "cost": 0.0, "status": "deleted",
     "run": "records_loc_gemma3_4b.jsonl", "arm": "B-gemma3:4b", "notes": "F1 0.400"},
    {"id": "aya-expanse:8b",  "tier": "local-multilingual", "size": "5.1", "cost": 0.0, "status": "deleted",
     "run": "records_loc_aya_8b.jsonl", "arm": "B-aya-expanse:8b",
     "notes": "Multilingual-special; slow (22.5s)"},
    {"id": "qwen2.5:7b",      "tier": "local-16GB", "size": "4.7", "cost": 0.0, "status": "deleted",
     "run": "records_loc_qwen25_7b.jsonl", "arm": "B-qwen2.5:7b",
     "notes": "Bigger ≠ better: 0.400 at 19.7s"},
    {"id": "mistral:7b",      "tier": "local-8GB", "size": "4.4", "cost": 0.0, "status": "deleted",
     "run": "records_local_ladder.jsonl", "arm": "B-mistral:7b", "notes": "First deletion"},
    {"id": "qwen2.5:3b",      "tier": "local-8GB", "size": "1.9", "cost": 0.0, "status": "deleted",
     "run": "records_loc_qwen25_3b.jsonl", "arm": "B-qwen2.5:3b", "notes": ""},
    # --- Local: new generation (2025-26, tested 2026-09-12) ---
    {"id": "qwen3.5:4b",      "tier": "local-newgen", "size": "3.4", "cost": 0.0, "status": "deleted",
     "run": "records_loc_qwen35_4b.jsonl", "arm": "B-qwen3.5:4b",
     "notes": "Thinking mode: 97s/call AND F1 0.588 < llama3.2:3b — loses both axes"},
    {"id": "phi4-mini",       "tier": "local-newgen", "size": "2.5", "cost": 0.0, "status": "deleted",
     "run": "records_loc_phi4mini.jsonl", "arm": "B-phi4-mini",
     "notes": "F1 0.737 = champion quality but 13.5s vs 2.5s — llama wins on speed"},
    {"id": "qwen3:4b",        "tier": "local-newgen", "size": "2.6", "cost": 0.0, "status": "partial-killed",
     "run": "records_loc_qwen3_4b.jsonl", "arm": "B-qwen3:4b",
     "notes": "PARTIAL (8/35 records, killed per owner load directive): F1 0.000 on its "
              "records, 96s/call thinking latency; model deleted; re-pull to complete"},
    # --- Not pulled (documented candidates) ---
    {"id": "gpt-oss:20b",     "tier": "local-16GB", "size": "~13-14 (pull)", "cost": 0.0, "status": "blocked",
     "run": None, "arm": None,
     "notes": "16GB MoE SOTA; pull killed at 13.8GB partial (disk crisis, owner hold); "
              "one-command: ollama pull gpt-oss:20b → run_local recipe"},
    {"id": "qwen3:1.7b",      "tier": "local-4GB", "size": "1.4 (pull)", "cost": 0.0, "status": "blocked",
     "run": None, "arm": None, "notes": "Sub-2B tier candidate; pull aborted (load hold)"},
    {"id": "gemma3:1b",       "tier": "local-1B/browser", "size": "0.8 (pull)", "cost": 0.0, "status": "blocked",
     "run": None, "arm": None, "notes": "Browser-adjacent tier; pull aborted (load hold)"},
    # --- Phase 1: HF router venue arms (2026-09-12; hosted serving) ---
    {"id": "llama-3.1-8B:fastest",   "tier": "hf-router", "size": "-", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf1_llama8b_fastest.jsonl", "arm": "B-meta-llama/Llama-3.1-8B-Instruct:fastest",
     "notes": "3-seed confirmed: F1 0.829/0.769/0.737 (±0.05), P=1.000 and 15 escalations every pass; beats-or-matches local champion (0.737) on all seeds"},
    {"id": "llama-3.1-8B:cheapest",  "tier": "hf-router", "size": "-", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf1_llama8b_cheapest.jsonl", "arm": "B-meta-llama/Llama-3.1-8B-Instruct:cheapest",
     "notes": "Same weights as :fastest — F1 0.629 @ 5.0s (venue/quantization drift, single-pass caveat)"},
    {"id": "gpt-oss-20b:fastest",    "tier": "hf-router", "size": "-", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf1_gptoss_fastest.jsonl", "arm": "B-openai/gpt-oss-20b:fastest",
     "notes": "Under-flags (R 0.167) at 792ms — quality is a model trait, hosting can't fix it"},
    {"id": "gpt-oss-20b:cheapest",   "tier": "hf-router", "size": "-", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf1_gptoss_cheapest.jsonl", "arm": "B-openai/gpt-oss-20b:cheapest",
     "notes": "Same F1 as :fastest; 3.9x slower"},
    {"id": "Qwen3-4B-2507:fastest",  "tier": "hf-router", "size": "-", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf1_qwen4b_fastest.jsonl", "arm": "B-Qwen/Qwen3-4B-Instruct-2507:fastest",
     "notes": "F1 0.500"},
    {"id": "Qwen3-4B-2507:cheapest", "tier": "hf-router", "size": "-", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf1_qwen4b_cheapest.jsonl", "arm": "B-Qwen/Qwen3-4B-Instruct-2507:cheapest",
     "notes": "F1 0.345 — :fastest beat :cheapest on all 3 models (3/3 direction)"},
    # --- Phase 1b: large models hosted (owner directive: don't limit to small
    # models when serving hosted — caching/speed/quantization; tested 2026-09-12) ---
    {"id": "gemma-3-27b-it (hosted)",       "tier": "hf-router-large", "size": "27B", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf2_gemma27b.jsonl", "arm": "B-google/gemma-3-27b-it:fastest",
     "notes": "BEST large model: F1 0.629 — still below hosted 8B (0.800)"},
    {"id": "Qwen3-235B-A22B-2507 (hosted)", "tier": "hf-router-large", "size": "235B MoE", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf2_qwen235b.jsonl", "arm": "B-Qwen/Qwen3-235B-A22B-Instruct-2507:fastest",
     "notes": "235B flagship-class: F1 0.452, sev-agreement 0.14 (worst)"},
    {"id": "gpt-oss-120b (hosted)",         "tier": "hf-router-large", "size": "120B MoE", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf2_gptoss120b.jsonl", "arm": "B-openai/gpt-oss-120b:fastest",
     "notes": "F1 0.286 @ 734ms — 11 providers, fastest large arm, under-flags"},
    {"id": "GLM-5.3-Flash (hosted)",        "tier": "hf-router-large", "size": "Flash", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf2_glm53flash.jsonl", "arm": "B-zai-org/GLM-5.3-Flash:fastest",
     "notes": "F1 0.286"},
    {"id": "Llama-3.3-70B (hosted)",        "tier": "hf-router-large", "size": "70B", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf2_llama70b.jsonl", "arm": "B-meta-llama/Llama-3.3-70B-Instruct:fastest",
     "notes": "F1 0.222 — scale did not help llama family"},
    {"id": "DeepSeek-V4-Flash (hosted)",    "tier": "hf-router-large", "size": "Flash", "cost": 0.0, "status": "kept-hosted",
     "run": "records_hf2_dsv4flash.jsonl", "arm": "B-deepseek-ai/DeepSeek-V4-Flash-0731:fastest",
     "notes": "F1 0.154; 1M-ctx model; required the JSON-recovery fix (doubled-brace output)"},
    {"id": "Qwen3.5-9B (hosted)",           "tier": "hf-router-large", "size": "9B", "cost": 0.0, "status": "failed-run",
     "run": "records_hf2_qwen35_9b.jsonl", "arm": "B-Qwen/Qwen3.5-9B:fastest",
     "notes": "Thinking model: 7/15 calls empty-content even at 4096 tokens, 23s/call — "
              "unrecoverable client-side; same anti-suitability as local qwen3.5"},
]


def grade_row(m: Dict[str, Any], labels, excluded) -> Dict[str, Any]:
    out = {
        "model": m["id"], "tier": m["tier"], "size_gb": m["size"],
        "cost_inr_per_run": m["cost"], "status": m["status"],
        "F1": "", "P": "", "R": "", "sev": "", "lat_ms": "", "records": "",
        "F1_prefix": "", "notes": m["notes"],
    }
    # Pre-fix lineage grade where a pre-fix run file carries this arm.
    if m.get("run_prefix"):
        gp = _grade_file(m["run_prefix"], m["arm_prefix"] or m["arm"], labels, excluded)
        if gp:
            out["F1_prefix"] = gp["f1"]
    if not m.get("run"):
        return out
    g = _grade_file(m["run"], m["arm"], labels, excluded)
    if g is None:
        return out
    lat = g["lat_ms"]
    out.update({
        "F1": g["f1"], "P": g["p"], "R": g["r"],
        "sev": g["sev"] if g["sev"] is not None else "",
        "lat_ms": round(lat) if lat else 0,
        "records": g["records"],
    })
    return out


def _grade_file(run_file: str, arm: str, labels, excluded) -> Optional[Dict[str, Any]]:
    """Grade one arm from one run file; None if file/arm/records missing."""
    path = RUNS / run_file
    if not path.exists():
        return None
    rows = [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    ar = [r for r in rows if r["arm"] == arm]
    if not ar:
        return None
    g = grade_arm(ar, labels, excluded)
    if g is None:
        return None
    lat = [d["latency_ms"] for r in ar for d in r.get("decide_log", []) if d["source"] == "llm"]
    return {
        "f1": g["f1"], "p": g["precision"], "r": g["recall"],
        "sev": g["severity_exact"], "records": g["graded_records"],
        "lat_ms": sum(lat) / len(lat) if lat else 0.0,
        "cost": sum(d.get("cost_inr", 0) or 0 for r in ar for d in r.get("decide_log", [])),
        "n": len(ar),
    }


# Sheet 2 — architecture patterns (pre-fix vs post-fix grades).
PATTERNS: List[Dict[str, Any]] = [
    {"id": "single (rules→LLM fallback)", "model": "gpt-4o-mini",
     "pre": ("records_patterns.jsonl", "B-gpt-4o-mini"),
     "post": ("records_final_patterns.jsonl", "B-gpt-4o-mini"),
     "verdict": "RECOMMENDED — best F1 with engine abstention gate"},
    {"id": "guard (LLM + fact-gate)", "model": "gpt-4o-mini",
     "pre": ("records_patterns.jsonl", "P-guard-gpt-4o-mini"),
     "post": ("records_final_patterns.jsonl", "P-guard-gpt-4o-mini"),
     "verdict": "superseded: gate moved into the engine (§8)"},
    {"id": "vote (2-model ensemble)", "model": "gpt-4o-mini",
     "pre": ("records_patterns.jsonl", "P-vote-gpt-4o-mini"),
     "post": ("records_final_patterns.jsonl", "P-vote-gpt-4o-mini"),
     "verdict": "recall-killer (agree-to-flag suppresses true positives)"},
    {"id": "critic (creator→validator)", "model": "gpt-4o-mini",
     "pre": ("records_patterns.jsonl", "P-critic-gpt-4o-mini"),
     "post": ("records_final_patterns.jsonl", "P-critic-gpt-4o-mini"),
     "verdict": "unreliable gate — F1 0.08; validator tracks creator identity"},
    {"id": "llm_first (no rules)", "model": "gpt-4o-mini",
     "pre": ("records_patterns.jsonl", "P-llm_first-gpt-4o-mini"),
     "post": ("records_final_patterns.jsonl", "P-llm_first-gpt-4o-mini"),
     "verdict": "DISQUALIFIED — P 0.156; fabricates elderly/toddler risks"},
    {"id": "guard (LLM + fact-gate)", "model": "gpt-5.6-luna",
     "pre": ("records_patterns.jsonl", "P-guard-gpt-5.6-luna"),
     "post": ("records_final_patterns.jsonl", "P-guard-gpt-5.6-luna"),
     "verdict": "same pattern, second model"},
    {"id": "vote (2-model ensemble)", "model": "gpt-5.6-luna",
     "pre": ("records_patterns.jsonl", "P-vote-gpt-5.6-luna"),
     "post": ("records_final_patterns.jsonl", "P-vote-gpt-5.6-luna"),
     "verdict": "same pattern, second model"},
    {"id": "critic (creator→validator)", "model": "gpt-5.6-luna",
     "pre": ("records_patterns.jsonl", "P-critic-gpt-5.6-luna"),
     "post": ("records_final_patterns.jsonl", "P-critic-gpt-5.6-luna"),
     "verdict": "same pattern, second model (F1 0.345 post-fix)"},
    {"id": "llm_first (no rules)", "model": "gpt-5.6-luna",
     "pre": ("records_patterns.jsonl", "P-llm_first-gpt-5.6-luna"),
     "post": ("records_final_patterns.jsonl", "P-llm_first-gpt-5.6-luna"),
     "verdict": "DISQUALIFIED — 84 FPs"},
]

# Sheet 4 — runs inventory: every records_*.jsonl artifact accounted for.
RUNS_STATUS = {
    "records.jsonl": ("superseded", "v1 full matrix pre-fix (175 rows; incl. fabricated default-flags)"),
    "records_ladder.jsonl": ("superseded", "pre-fix 19-model ladder (replaced by ladder2 post-fix; kept for lineage)"),
    "records_ladder2.jsonl": ("valid-reference", "post-fix 17-model ladder — the API grades of record"),
    "records_patterns.jsonl": ("superseded", "pre-fix pattern matrix"),
    "records_final_patterns.jsonl": ("valid-reference", "post-fix pattern matrix — pattern grades of record"),
    "records_final_single.jsonl": ("valid-reference", "post-fix variance run: 3 passes × mini+luna"),
    "records_postguard.jsonl": ("superseded", "post-gate-layer-1 only (default-flag bug still live)"),
    "records_postguard2.jsonl": ("valid-reference", "both fixes live: spurious 11→0 confirmation"),
    "records_local_ladder.jsonl": ("superseded", "overwritten twice by tag reuse (retains 12b+mistral grades)"),
    "records_loc_llama32_3b.jsonl": ("valid-reference", "local champion run"),
    "records_loc_gemma3_4b.jsonl": ("valid-reference", "deleted model, grade preserved"),
    "records_loc_qwen25_3b.jsonl": ("valid-reference", "deleted model, grade preserved"),
    "records_loc_qwen25_7b.jsonl": ("valid-reference", "deleted model, grade preserved"),
    "records_loc_aya_8b.jsonl": ("valid-reference", "deleted model, grade preserved"),
    "records_ollama.jsonl": ("valid-reference", "qwen2.5vl:7b 2-pass run (vision-coupled keeper)"),
    "records_loc_qwen35_4b.jsonl": ("valid-reference", "new-gen deleted model, grade preserved"),
    "records_loc_phi4mini.jsonl": ("valid-reference", "new-gen deleted model, grade preserved"),
    "records_loc_qwen3_4b.jsonl": ("partial-killed", "15/70 rows — run killed per owner load directive"),
    "records_ollamasmoke.jsonl": ("smoke", "3-record ollama provider smoke"),
    "records_patternsmoke.jsonl": ("smoke", "2-record pattern smoke (llm_first/guard/vote/critic wiring)"),
    "records_seedsmoke.jsonl": ("smoke", "--runs 3 variance-protocol smoke"),
}


def main() -> int:
    labels, excluded = load_labels()
    rows = [grade_row(m, labels, excluded) for m in MANIFEST]

    out_csv = RUNS / "comparison_sheet.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md = REPO / "Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md"
    lines = [
        "# KDD model comparison — full sheet (every model tested, kept, deleted, failed)",
        "",
        "Generated by `tools/build_model_comparison.py` — regenerate after any new",
        "run; do not hand-edit the tables. Grades vs",
        "`data/fixtures/risk_flags/ground_truth_labels.json` (note-level rubric).",
        "Deleted models remain here so no result is lost; each has a one-command",
        "re-pull via `ollama pull <id>`.",
        "",
        "| Model | Tier | Size GB | ₹/run | Status | F1 (post-fix) | F1 (pre-fix lineage) | P | R | sev✓ | lat ms | rec | Notes |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            "| {model} | {tier} | {size_gb} | {cost_inr_per_run} | {status} | "
            "{F1} | {F1_prefix} | {P} | {R} | {sev} | {lat_ms} | {records} | {notes} |".format(**r)
        )

    # Sheet 2: architecture patterns
    lines += [
        "",
        "## Sheet 2 — decision-architecture patterns (pre-fix vs post-fix, F1)",
        "",
        "| Pattern | Model | F1 pre-fix | F1 post-fix | Verdict |",
        "|---|---|---|---|---|",
    ]
    for p in PATTERNS:
        pre = _grade_file(*p["pre"], labels, excluded)
        post = _grade_file(*p["post"], labels, excluded)
        lines.append(
            f"| {p['id']} | {p['model']} | {pre['f1'] if pre else '-'} | "
            f"{post['f1'] if post else '-'} | {p['verdict']} |"
        )

    # Sheet 3: run-to-run variance (post-fix, 3 cold passes)
    lines += [
        "",
        "## Sheet 3 — run-to-run variance (post-fix, 3 independent cold passes)",
        "",
        "| Model | F1 r0 | F1 r1 | F1 r2 | Escalation-set stability |",
        "|---|---|---|---|---|",
    ]
    for model in ("gpt-4o-mini", "gpt-5.6-luna"):
        f1s = []
        for arm in (f"B-{model}", f"B-{model}-r1", f"B-{model}-r2"):
            g = _grade_file("records_final_single.jsonl", arm, labels, excluded)
            f1s.append(f"{g['f1']:.3f}" if g else "-")
        lines.append(f"| {model} | {f1s[0]} | {f1s[1]} | {f1s[2]} | 35/35 records identical |")

    # Sheet 4: runs inventory — every artifact accounted for
    lines += [
        "",
        "## Sheet 4 — runs inventory (every records_*.jsonl artifact, nothing orphaned)",
        "",
        "| Run file | Rows | Status | Why |",
        "|---|---|---|---|",
    ]
    for f in sorted(RUNS.glob("records*.jsonl")):
        n = sum(1 for line in f.read_text().splitlines() if line.strip())
        status, why = RUNS_STATUS.get(f.name, ("unclassified", ""))
        lines.append(f"| {f.name} | {n} | {status} | {why} |")

    lines += [
        "",
        "## Failure / ops log (all documented, nothing hidden)",
        "",
        "- **401 dry run** (2026-09-11): first full matrix ran with a revoked key —",
        "  124/124 attempts failed; arm B measured \"hybrid with dead LLM\" (honest",
        "  failover datapoint, records.jsonl superseded by records_final_*).",
        "- **Background-pull sandbox failure**: detached/background shells silently",
        "  failed every ollama pull (empty logs, exit 0) — pulls must run foreground.",
        "- **Partial-blob leak**: killing an ollama pull leaves the `-partial` blob",
        "  on disk (13.8GB for gpt-oss:20b) — manual cleanup required.",
        "- **Harness overwrite bug**: reusing a `--tag` overwrote previously-run",
        "  arms (\"w\" mode) — per-model tags are now mandatory for ladders.",
        "- **Thinking-mode latency**: qwen3.5:4b / qwen3:4b run 40–96s/call —",
        "  unusable for the decision lane regardless of quality.",
        "- **Partial-killed runs**: qwen3:4b (8/35 records) killed per owner load",
        "  directive; gpt-oss:20b pull killed at 13.8GB (disk crisis).",
        "- **Grader self-trap**: first FP-check iterated the filtered emitted-dict",
        "  (precision stuck at 1.000 even for flag floods) — fixed before any",
        "  conclusions were drawn; the \"eval grading the grader\" hazard.",
        "- **Labeling correction**: `traveler_safe_leakage_risk` (pipeline-integrity",
        "  family) initially scored as FPs — excluded by vocabulary, not deleted.",
        "",
        "## Re-pull recipes (any deleted/blocked model)",
        "",
        "```bash",
        "ollama pull <model-id>",
        ".venv/bin/python scripts/run_hybrid_kdd_experiment.py --skip-baseline \\",
        "  --models \"local-ollama/<model-id>\" --tag \"_loc_<safe-name>\"",
        ".venv/bin/python tools/grade_kdd_flags.py records_<tag>.jsonl",
        "```",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[comparison] {len(rows)} model rows -> {out_csv}")
    print(f"[comparison] md (4 sheets + ops log) -> {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
