# Random Document Audit — Creator Travel Regulatory Playbook (Australia & Oceania)

**Date:** 2026-09-09
**Method:** Random Repository Document Audit v2 (canonical source per `~/Projects/agent-start/COUNCIL_AND_AUDIT_SOURCES.json`, SHA-256 `62d1d1ca…c737`)
**Mode:** Read-only audit; follow-on docs work executed same session per owner instruction ("work on all open items as per the doctrines").

## Selection record

| Field | Value |
| --- | --- |
| Sampling mode | `random_probe` (uniform) |
| Seed | `2026090914` |
| Pool size | 3,619 eligible documents |
| Pool hash | `dfd6b99dddcc36c9b2bed65db93659f3a739df24a4425527b4d5138b0bf3fc34` |
| Repository revision | `cfdf19e` (master, dirty: 24 files — parallel PER-0443 Part N work in spine_api/frontend; no overlap with edited files) |
| Selected path | `Docs/industry_domain/regulatory_compliance/CREATOR_TRAVEL_REGULATORY_PLAYBOOK_AUSTRALIA_OCEANIA.md` |
| Exclusions | instruction surfaces (`AGENTS.md`, doctrine, generated context), vendored trees, caches (builder defaults) |

## Chosen document

76-line market/regulatory playbook for creator travel in Australia & Oceania. One of 11 regional
playbooks produced under the parent framework
(`CREATOR_TRAVEL_MARKET_SPECIFIC_REGULATORY_PLAYBOOKS.md`, which lists Australia & Oceania as a
priority market at line 37). Structure conforms to the parent's 5-part scaffolding.

## Persona resolution & council

- Canonical persona repository: `/Users/pranay/Desktop/Understanding_Personas_sept6` (resolver
  confidence: high; explicit current pointer + master registry; birth-time corroborating only).
- Council (fallback in-process orchestration, single-agent mode): **Lead** Product-Strategy/Owner
  lens; **Seats:** Compliance-Domain (speciality), Research-Corpus Governance, Platform/Implementation,
  Skeptic/Do-Nothing. **Rejected seats:** Security/Privacy (no doc-driven PII surface; passport PII
  in visa_radar is pre-existing and VA-tracked), UX (no creator product surface), Ops (no runtime claims).

## Key verified evidence

| Claim/hook in doc | Repository reality | Status |
| --- | --- | --- |
| §2.1 visa categories incl. commercial filming; leisure-vs-commercial flagging | `spine_api/services/visa_radar.py:48-56` — 7 leisure pairs (US/UK/IN → FR/GB/JP/US/TH); zero AU/NZ/Pacific pairs; no purpose-of-travel field; VA-01/02/03 hardening present but uncommitted (parallel agent) | Missing (DECIDE-gated) |
| §2.5 "GST applies in Australia and New Zealand" | `spine_api/routers/tax_compliance.py` — India-only (TCS/GST/LRS, INR, PAN); `fx_sentinel.py` partially adjacent | Missing (DECIDE-gated) |
| §2.2–2.3 permits / environmental / Indigenous protocols | No code anchor; zero mentions in corpus meta-docs | Research gap (was orphaned) |
| §3.1–3.3 agent compliance checks, partner categories, creator messaging | No surfaces; only creator touchpoint: `spine_api/routers/social_inbound.py:42` `creator_id`, `frontend/src/app/intake/fast/page.tsx:8` `creator_paste` | Missing (DECIDE-gated) |
| §4 SEO hooks | No marketing/content surface exists (public checker is the wedge funnel) | Not worth doing now |
| §5 playbook structure | Conforms to parent framework | Already done |
| Registration | `Docs/industry_domain/INDEX.md:106` `[x]`, `CREATOR_TRAVEL_DOCUMENT_INVENTORY.md:118`, `CREATOR_TRAVEL_RESEARCH_TAXONOMY_MATRIX.md:141` | Already done |
| §6 "Next research actions" | Zero matches in roadmap / gap list / coverage matrix / gap audit | **Orphaned → now registered** |
| Corpus-wide pattern | **11 playbooks** (SEA, US, LATAM, JP/KR, India, AU/Oceania, Africa, China, EU/Schengen, GCC, Complaints/Enforcement) each carry untracked "Next research actions" | Systematic governance gap → now registered |
| Doc quality | Zero citations/sources/as-of dates; "Maori" missing macron | Fixed/annotated (see below) |

Targeted baseline: `pytest tests/test_visa_radar.py` → 4 passed (0.26s, dirty tree). Full suite not
run: parallel-agent contention risk (F-19 phantom-failure lesson); docs-only changes made this
session, so targeted evidence is proportionate.

## Findings/task register (final)

### EXPLORE (research & documentation)

| ID | Task | Gate | Disposition |
| --- | --- | --- | --- |
| AU-1..AU-3 | Doc §6 actions: AU/NZ media-visa + permit-timeline map; Pacific Island permit/cultural-consent catalog; supplier-category prioritization | QG (quota reset 2026-10-06, owner directive a030190) | **Registered** in roadmap registry |
| IN-1..IN-3, SEA-1..3, US-1..3, LATAM-1..2, JPKR-1..3, AF-1..3, CN-1..3, EU-1..2, GCC-1..3, CDF-1..2 | Sibling playbooks' research actions (corpus-wide orphan sweep) | QG | **Registered** (27 research rows) |
| EX-02 | Source-citation pass for the AU playbook's §2 claims (with as-of dates) | Partially ungated: status annotation done now; sourced verification QG | **Scaffolded** (verification-status block added); citation pass joins AU-1..3 at quota reset |

### IMPLEMENT (product)

| ID | Task | Gate |
| --- | --- | --- |
| LATAM-3 | Cash-payout/escrow/permit-tracking agent features | DG (D-01 conflict) |
| EU-3 | GDPR-specific platform controls for creator data | DG |
| US-1 (second half) | Enforcement examples → platform policy language | DG after QG research |
| CDF-3 | Unified dispute taxonomy | DG |
| IM-AU1 (audit register) | Purpose-of-travel dimension + AU/NZ pairs in visa_radar | DG; also blocked by parallel VA hardening (uncommitted) and VD-02 live-source decision |
| IM-AU2/3/4 (audit register) | AU/NZ GST engine; partner-onboarding model; SEO content surface | DG / not-worth-now |

## Work executed this session (docs-only, additive)

1. `Docs/industry_domain/CREATOR_TRAVEL_RESEARCH_ROADMAP.md` — new section
   "Regional playbook research-actions registry (2026-09-09)": all 33 actions from 11 playbooks
   registered with class + gate (QG/DG), India rows marked priority-at-reset; "How to use" bullet added.
2. `regulatory_compliance/CREATOR_TRAVEL_REGULATORY_PLAYBOOK_AUSTRALIA_OCEANIA.md` —
   verification-status block added (unsourced claims flagged, gate + registry pointer);
   "Maori" → "Māori"; §6 pointer to registry rows AU-1..AU-3.
3. This audit record.

Nothing was deleted; no code files touched; no commits made (commit requires explicit owner approval + gate).

## Doctrine compliance

| Rule | Source | Compliance |
| --- | --- | --- |
| FOR LATER external research until 2026-10-06 quota reset | `Docs/review/OPEN_WORK_ROADMAP_2026-09-08.md` (owner directive, a030190) | Satisfied — no web research performed; gated rows registered instead |
| Additive docs; never delete historical documentation | repo `AGENTS.md` | Satisfied — all changes additive or single-word correction |
| No durable implementation without instruction | audit skill / canonical source | Satisfied — product items registered as DECIDE-gated, not built |
| Corpus governance theme #1 (keep research discoverable/actionable) | `CREATOR_TRAVEL_RESEARCH_ROADMAP.md` | Advanced — orphaned actions now tracked in the corpus's own prioritization lens |
| Read-only git | repo `AGENTS.md` | Satisfied |

## Council verdict

Do **not** build anything from this document now: the product's live decision state (D-01
Tenant-of-One Ravi page, Hand-Carried Pilot; FOR-LATER directive) puts AU/Oceania out of scope, and
`visa_radar` is mid-flight under a parallel agent. The valuable, ungated work was corpus governance
(33 registered research actions + doc-quality scaffolding) — executed. The skeptic's
"build it so the doc isn't wasted" counterargument was rejected on evidence.

## Open items for the owner

1. At the 2026-10-06 quota reset: run AU-1..AU-3 (or re-prioritize toward IN-1..IN-3, which the
   registry marks first-in-queue given the India-first platform).
2. Decide whether the creator corpus itself should be formally marked FOR LATER like B6/B7-B8, or
   remain an active reference corpus.
3. If AU/Oceania activates: build purpose-of-travel into the checker/visa_radar only after the
   parallel VA hardening lands and VD-02 (live visa source) is decided.
