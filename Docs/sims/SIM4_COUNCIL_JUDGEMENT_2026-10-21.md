# Sim #4 Council Judgement — "Eleven Doors" (2026-10-21)

- **Orchestrator:** `$council-orchestrator` (adapter
  `/Users/pranay/.agents/skills/council-orchestrator/SKILL.md`; canonical source
  `/Users/pranay/Projects/Council Orchestrator Skill.md`, manifest
  `/Users/pranay/Projects/agent-start/COUNCIL_AND_AUDIT_SOURCES.json`,
  `integration_current: true`).
- **Canonical persona repository:** `/Users/pranay/Downloads/Understanding_Personas_24sep`
  (resolver: explicit current canonical pointer, confidence high; index
  freshness gate `action: use`, 2,349 filesystem records / 2,318 DOCX
  candidates — filesystem counts, not canonical persona counts).
- **Subject:** `Docs/sims/SIM4_RESULTS_2026-10-21.md` (predictions
  `SIM4_DESIGN_2026-10-21.md` P1–P47; evidence under `Docs/sims/assets/sim4/`).
- **Requested outcome:** assess + prioritise. **Explicit Lead requested:**
  launch-readiness owner → **PER-0100** (sticky).
- **Execution note (honest):** subagent seats were unavailable this session
  (provider usage limit until 07:36); every seat below was executed by the
  orchestrating agent in sequence, with persona judgement, inference, and
  repository/runtime evidence kept separate as the skill requires. Seat labels
  are the canonical index titles (validated with `validate_seat_labels.py`).
- **Doctrines active:** OPERATING_DOCTRINE v8.2 (§2 truth taxonomy, §3 S2
  gate + visual pairs, §9 candidate dispositions, §13 claim reality),
  SECURITY_PRIVACY_SAFETY (R-15 matrix), ADR-008 (rungs: asks/sends are
  operator actions; system never moves money).

## 1. Council manifest

### Lead
**PER-0100 — Launch Readiness Director.** Reason: the sim's purpose is a
launch-readiness probe of doors shipped as "SHIPPED"; decision ownership is
the go/no-go register, and the Lead must deduplicate against the 2026-10-12
council (`Docs/review/COUNCIL_FULL_REPO_AND_WAVE_AUDIT_2026-10-12.md`).

### Supporting seats
| Seat | Persona | Canonical label | Type | Skills | Mission | Removal test |
|------|---------|-----------------|------|--------|---------|--------------|
| 1 | PER-0442 | Travel Operating Systems Architect | Persona+Skill | `state-audit`, `async-audit` | Persistence boundary (FND-0326), decrypt/key rotation (0327), loop teardown (0321), inbound duplicate leads (0334), reprocess supersession loss (P41) | Without it the at-rest/state findings have no architectural owner |
| 2 | PER-0443 | Agentic Travel Systems Architect | Persona+Skill | `agentic-eval-loop` (`AGENTIC_EVAL_RULES.md`) | Extraction truthfulness (0329/0341/0349/0350; 0331 retracted in-session), answer consumption (0328), fabricated outputs (0333/0337/0338/0339) | Without it the honesty-taxonomy verdicts lose the eval-doctrine lens |
| 3 | PER-0362 | Security and Privacy Architect | Persona+Skill | `security-review` | Privacy posture matrix, PAN handling, Art.15/17 completeness (0335/0336), guard message (0347), key-rotation data availability (0327) | Without it DSR/PCI consequences are unowned |
| 4 | PER-0468 | Missing-Workflow Red Team | Persona **(also Skeptic/counterposition)** | — | Door-completion gaps: group share 401 (0330), gate dead-end (0332), BFF parity (0340), send idempotency (0348); falsify the emerging plan | Without it "it works in the API" passes as "it works" |
| 5 | PER-1098 | Travel Agency / TMC UX Designer | Persona | — | Operator/traveler experience: "1 pax" (0343), scope/multi-city display (0344), ask compose template, documents stage gate UX | Without it UI contradictions are graded as cosmetic |
| 6 | Elena Rostova | Agency Owner (project persona, `Docs/personas/PERSONA_AGENCY_OWNER_ELENA.md`) | Persona (project) | — | Commercial consequence ranking: which failures lose a booking or a client; money ops (I) acceptance | Without it priorities are engineering-shaped, not business-shaped |

### Coverage
- decision ownership: PER-0100 · domain: travel ops + intake + compliance ·
  user/stakeholder: Elena (owner), PER-1098 (advisor/traveler UX) ·
  implementation: PER-0442/0443 · risk: PER-0362 · methods: unit probes
  (Tier 2), live API + DB row scans + screenshots (Tier 4) · counterposition:
  PER-0468.

### Rejected candidates
| Candidate | Reason |
|-----------|--------|
| PER-0400 SMB Owner Operator | Elena is the established project owner persona with Waypoint-specific context (two prior councils); PER-0400 adds no travel-specific mandate |
| PER-0384 Legal Compliance Workflow Architect | Overlaps PER-0362 on DSR; the legal determination surfaces (visa, claims) are already covered by 0362 + 0443 |
| PER-0983 / PER-0754 Accessibility seats | The accessibility lead's failure is a privacy-posture refusal, not an accessibility-UX defect; 0362 owns it |
| PER-0338 Product Manager | Prioritisation is owned by the Lead + Elena; no distinct contribution |

### Known gaps
- No live LLM-lane (hybrid engine) judgement — posture is ratified-0; out of scope.
- No real-provider dispatch/OCR/visa-API evidence — honest NOT_CONFIGURED tiers were the grade.
- PCI posture for card numbers in free text has no ratified owner rule yet (surfaced below as a decision).

## 2. Seat reports

### Seat 1 — PER-0442 Travel Operating Systems Architect
**Mandate:** state authority and persistence boundaries.
**Evidence (Tier 4):** `GET /runs/fc6315c2…` returns the full packet incl.
"wheelchair" and the traveler's name for a run whose TripStore write the guard
refused; `GET /trips/trip_e39ecce2f7cc` → 500 with traceback at
`persistence.py:851 _decrypt_blob → json.loads`; inbound parse created
`trip_6c6599169c18` while the seeded lead was `trip_efdc99be41b2`; six
`RuntimeError … attached to a different loop` entries across both backend logs.
**Analysis/inference:** The privacy guard is implemented as a TripStore
pre-write check, but the system has at least three persistence doors for the
same note (drafts, run ledger, trips) and only one is guarded — so the posture
is partial by construction, not by bug (inference: no finding ever enumerated
the doors). `_decrypt_blob`'s "return original on InvalidToken" is a correct
legacy-plaintext accommodation that becomes a landmine when the value is a
valid token under another key — there is no key id on the ciphertext and no
re-encryption tool. Inbound parse is a lead-creation door with no identity
join to existing trips (FND-0284's duplicate-lead class on a new door).
**Risks:** silent PII sprawl outside the guarded table; key rotation = outage;
duplicate leads corrupt pipeline metrics and operator queues.
**Recommendation:** (1) make the guard a persistence-layer concern applied to
drafts + run ledger + message store (or encrypt those stores with the same
`_PII_FIELDS` discipline); (2) version ciphertext (`{"__encrypted_blob":…,"kid":…}`)
and add a reusable re-encryption tool; discriminate legacy plaintext (parse
first) from foreign ciphertext (typed 4xx + telemetry) instead of 500; (3)
inbound parse must resolve an existing lead by contact/booking-ref before
creating one, and write the message row. **Confidence:** high on 0326/0327
(runtime proof); medium on 0321 residual stores (need per-store audit).
**Unknowns:** which store emits the loop errors now (check: wrap each
session-maker with a loop-id assertion in a probe).

### Seat 2 — PER-0443 Agentic Travel Systems Architect
**Mandate:** extraction truthfulness and agentic loop closure.
**Evidence (Tier 2 + 4):** unit probes: `_extract_destination_candidates`
returns `(['Solo'],'definite')` for the Japan note and `(['Young'],'definite')`
for "too young"; W3: answer `origin_city=kolkata` recorded, reassess leaves
`follow_up_questions` unchanged; `noop_extractor` emits nationality "US" at
0.85; compiler emits `optimized_take_rate_pct: 1240.0`.
**Analysis/inference:** Three honesty-taxonomy violations of different kinds:
(a) *fabrication* — a hypothesis wearing a fact's clothes (Solo/Young
definite; US nationality; 1240% take rate); (b) *loss* — true facts the system
computed and then dropped (answers; the purpose/duration 'loss' was a runner
digest artifact — FND-0331 retracted with live evidence); (c) *non-disclosure* —
a default asserted as a determination (visa E_VISA for a registry miss, a
violation derived from an estimated cost). Per `AGENTIC_EVAL_RULES.md`, (a)
and (c) are the classes that destroy operator trust fastest; (b) makes the
ask loop insult the customer by re-asking what they said. The Sim #3
membership-proof + stoplist posture is necessary but insufficient: the
remaining trigger is *grammatical position* (a sentence-leading epithet that
is also a gazetteer name) and *missing region layer*; the definite status
must require corroboration (a destination cue such as "trip to"/"in"/"visit",
or ≥2 mentions), never bare membership.
**Recommendation:** (1) `definite` ⇒ cue-corroborated OR agentic resolver
agreement; leading-token epithets (solo/young/nice/mobile/…) demoted to
hypothesis unless cued; (2) add an IN state/region gazetteer layer with
`destination_kind: region`; (3) surface `trip_purpose` + `duration` slots into
`extracted.facts` (the packet already has `derived_signals`; they belong in
facts with provenance); (4) `reassess` merges `traveler_answers` through
`field_merge` with `authority=explicit_user`, `channel=ask_link`, then recomputes
`blocking_unknowns`; (5) noop extractor must emit `status: NOT_EXTRACTED`,
`confidence: null`; (6) compiler: budget-feasibility gate + INR-native costing
or an explicit FX line; `provenance_assertions` must be returned, not counted.
**Confidence:** high (unit + live agree). **Unknowns:** whether the agentic
destination resolver (f2b14aef) would have corrected 'Solo' with the LLM lane
on — test under the X-09 posture when authorised.

### Seat 3 — PER-0362 Security and Privacy Architect
**Mandate:** privacy posture, PCI, DSR completeness.
**Evidence (Tier 4):** dogfood: accessibility lead refused at persistence
(health keyword) while the identical packet sits in the run ledger; beta: PAN
note persisted as a blocked trip with no PAN in any trips column (DB row
scan) — the text survives only in the draft store; Art.15 export
`personal_data:{}`; Art.17 (beta) leaves `name` on the trip and the full
`CustomerMemoryProfile` while `/customers/memory/forget` erases with a
certificate; guard message instructs `ENCRYPTION_KEY` although the matrix's
door-opener is `DATA_PRIVACY_MODE`.
**Analysis/inference:** R-15 is owner-ratified and must not be weakened; the
defect is *coverage*, not *strength*. Card numbers are a special case: no
mode should ever persist a PAN — they are never needed by the product
(tracking-only money boundary) — so PAN detection should be *redact-at-ingest*
in every mode, independent of the fail-closed matrix (inference: Layer-2 missed
the spaced form; redaction with Luhn validation closes it). Art.17 that leaves
a profile is a reportable breach of the erasure right; Art.15 that exports
nothing is a non-answer to a DSAR.
**Recommendation:** (1) extend the guard to all persistence doors (0326) OR
make beta+encryption the default *dev* posture with ledger/drafts encrypted —
owner decision; (2) PAN redact-at-ingest (Luhn) in all modes — propose as a
new R-15 row; (3) erasure orchestrates memory forget + name/contact scrub +
draft/message tombstones; export reads `extracted.facts`, booking data, and
messages; (4) fix the message text (0347). **Confidence:** high.
**Unknowns:** whether the message store holds inbound text today (it holds
zero rows for both trips — may be a write-path absence rather than a leak).

### Seat 4 — PER-0468 Missing-Workflow Red Team (and Skeptic)
**Mandate:** find the inch that makes a "shipped" door unusable; falsify the
plan.
**Evidence (Tier 4):** `GET /api/v1/group/token/{t}` → 401 for the invitee;
second `send` mints a token whose page lists no questions; BFF probe: eleven
door families return the BFF's own `{"error":"Not found"}`; PlanningStageGate
demands fields the packet holds.
**Analysis:** Four doors fail at the LAST step after every earlier step
passes — exactly the class the 10-12 council predicted for T1 and that is
now proven for group share too. BFF parity is the structural cause: a door
with no `route-map.ts` entry is backend-only by definition, so "SHIPPED"
claims for DSR/visa/corporate/accounting are claims about the API, not the
product.
**Skeptic pass on the emerging plan:** (i) "Just open `/group/token` publicly"
— falsified as insufficient: the share page exposes deposit shares and
passenger names; it needs the same signed-capability + TTL posture as
`/a/{token}` and `/p/{token}`, not a bare auth removal. (ii) "Set the dev
posture to beta" — falsified as a complete fix: the beta lane still blocked
nothing it should (PAN) and still leaked via drafts/ledger; posture is
orthogonal to coverage. (iii) "Gazetteer stoplist for Solo/Young" — the
Sim #3 self-audit already rejected whack-a-mole; cue-corroboration is the
invariant. (iv) "Quotes for blocked leads is by design" — partially true;
but the owner-visible consequence is an empty Quotes page for 100% of leads
in the deterministic lane; a labelled partial preview or an explicit "unlocks
at planning-ready" state is required for trust (0342 stays P2).
**Recommendation:** treat every BFF-unmapped door as *not shipped* in the
launch inventory until mapped + UI-walked; add a CI parity gate (route-map
keys vs backend routes tagged "product-facing"). **Confidence:** high.

### Seat 5 — PER-1098 Travel Agency / TMC UX Designer
**Mandate:** what the advisor and the traveler actually see.
**Evidence (Tier 4 screenshots):** "1 pax" for a 2-traveler accessibility
couple; "₹18,000" for a 12-person trip; "Jaipur" for a Jaipur+Udaipur split;
"Complete budget range and destination…" on a lead that has both; a compose
sentence with a blank subject; "Workspace unavailable" on two leads.
**Analysis:** Each is a trust break at the moment the advisor decides whether
to believe the tool. The pax/scope errors are money-adjacent (per-person math
is how Indian agencies quote); the gate dead-end is the single most expensive
UX defect because it blocks the operator from the Options/Quote tabs with no
recovery path.
**Recommendation:** FE must read packet party and scope (never default to 1;
"party not set" is honest); show derived totals with the scope label; gate on
canonical `blocking_unknowns` only (one source of truth); visual pairs for
each fix (doctrine §3). **Confidence:** high.

### Seat 6 — Elena Rostova, Agency Owner (project persona)
**Mandate:** rank by lost bookings and client trust.
**Judgement (persona lens, not evidence):** "If my junior sends a group link
that says 'Not authenticated', the group is gone. If a wheelchair family's
inquiry silently vanishes, that is the story that follows us. If a proposal
says my take rate is 1240%, nobody on my team will open that page again. If
an erasure request leaves the client in my memory, I am the one who gets the
regulator's letter." Ranking by business damage: 0326/0330/0337/0335/0332
first; 0329/0328 next (they make the AI look like it doesn't listen);
0343/0344 are cheap and visible; the money-ops door (I) is the one surface I
would demo today.
**Confidence:** n/a (judgement). **Unknown to verify:** how often real leads
carry health words — if common, 0326's dogfood refusal is a daily event.

## 3. Cross-examination

| Issue | Position A | Position B | Type | Resolution |
|-------|-----------|------------|------|------------|
| FND-0326 severity | 0442/0362: P0 — posture is partial in *every* mode (ledger/drafts unencrypted in production too) | Lead: dogfood is dev-only; production control is RLS+encryption | factual | **Evidence wins for P0**: `_encrypt_pii` applies to the trips table only; run ledger packets and drafts hold the same PII in production posture — the 10-12 AUD-02 scope was incomplete. P0 stands; the remediation is an owner posture decision (guard-all-doors vs encrypt-all-doors) |
| PAN handling | 0362: redact-at-ingest all modes | 0468: beta "fail-open" is ratified | value/trade-off | PAN is never product-needed (money boundary) → redaction does not weaken any ratified matrix row; **propose as a new R-15 row (owner ratify)** |
| Quotes for blocked leads | 0468: design, not defect | 1098/Elena: empty page = distrust | stakeholder | Keep P2; require an explicit state label in the UI, not silent emptiness |
| 'Solo'/'Young' | 0443: cue-corroboration invariant | — (stoplist rejected in Sim #3 already) | architectural | cue-corroboration + region layer; stoplist only as a last-mile list |
| Posture for dev | 0442: beta+key default in dev | 0362: dogfood intent is "no real PII in dev" | value | **Owner decision** (P-1 of Sim #3 reappears with stronger evidence): either posture is coherent only if coverage is complete |

## 4. Lead synthesis (PER-0100)

### Recommendation
Launch verdict remains **NO-GO**; the 10-12 register gains one P0
(FND-0326, a scope extension of AUD-02/03 to the run ledger, drafts, and
message store) and twelve P1s that are mostly *last-inch* and
*honesty* defects on doors already marked SHIPPED. Sequence: persistence
boundary + key safety → answer consumption + fact-loss → fabrication honesty
(extractor, compiler, visa, policy) → DSR completeness → door-reachability
(group share, BFF parity, gate source) → UI truth (pax/scope). Every
fix ships with an S2 fail-before/pass-after probe and, for UI-affecting
items, a visual pair.

### Why
Evidence tiers were runtime (Tier 4) for every registered finding and unit
(Tier 2) for the extraction root causes; persona judgement only shaped the
ranking. The defects cluster on three invariants the doctrine already names:
one persistence boundary, facts never silently lost, no number without a
basis.

### Important trade-offs
Guard-all-doors (strict dev posture) vs encrypt-all-doors (dev=beta): both
are coherent; the owner picks. PAN redaction is a strict improvement in
either.

### Material dissent
PER-0468 holds that "quotes unlock at planning-ready" is correct product
behaviour; the council keeps it P2 with a UI-label requirement rather than
P1. Elena would rank group-share (0330) above the persistence boundary for
near-term revenue; the Lead keeps 0326 first because it is a data-protection
exposure in production posture.

### Unknowns / what would change the recommendation
- If the owner designates dev posture = beta with encrypted ledger/drafts,
  0326 collapses into an implementation task (not a posture debate).
- If the LLM-lane destination resolver corrects 'Solo'/'Young', 0329 narrows
  to the deterministic lane (still the production posture today).
- If inbound's lack of message rows is a write-path absence (not a leak), the
  0334 fix is additive, not corrective.

### Next action
Execute `Docs/sims/SIM4_META_AUDIT_AND_PLAN_2026-10-21.md` Phase 1 (this
session), register decisions needing the owner in `Docs/DECISIONS_PENDING.md`,
and re-run `tools/sim4_runner.py` doors A/D/G/J/K as the S2 proof.

**Falsifiers:** a Phase-1 re-run where (a) a key change no longer 500s a
read, (b) a recorded answer clears its unknown after reassess, (c) [retracted], (d) 'solo trip to japan' yields Japan/Tokyo/Kyoto
with 'Solo' absent or hypothesis-only, (e) the noop extractor reports
NOT_EXTRACTED — any of these failing refutes the corresponding fix.
