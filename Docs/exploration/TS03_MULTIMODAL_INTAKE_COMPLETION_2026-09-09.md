# TS-03 — Multi-Modal Intake Completion (customer path)

**Status:** exploration → implementation plan — 2026-09-09
**Source:** training-session register TS-03; tutor's input model ("raw messages, attachments, voice notes, links, dates, names, partial bookings") + the D-01-decided open verifier/marketplace where messy inbound *is* the funnel.
**Doctrine:** Exploration 1.1 (frontier expansion before pruning); Security/Privacy 1.0 (SSRF, PII posture); Architecture 1.1 (extend canonical paths, no parallel intake).

---

## 1. Current state (Observed, verified 2026-09-09)

| Modality | Customer-message path | Operator path | Gap |
|---|---|---|---|
| Text | ✅ full pipeline (`src/intake/inbound.py` → extract → packet) | ✅ | — |
| Image | ❌ | ✅ vision extraction (OpenAI + Gemini, `src/extraction/vision_client.py:238-250`; `spine_api/routers/trip_documents.py:225,484,649` upload→extract→apply) | Customer path text-only; `/api/v1/multimodal/image-ocr` accepts only **pre-OCR'd text** (`spine_api/routers/multimodal.py:211-258`) |
| PDF | ❌ | ✅ same vision lane (`src/extraction/pdf_utils.py` page-count prevalidation) | Not reachable from customer inbound |
| Voice | ❌ (requires pre-supplied `transcript_text`, `multimodal.py:161-208`; `src/intake/audio_intake.py:50` takes `simulated_transcript`) | ❌ | **No ASR anywhere in the repo** |
| URL | ❌ (URL fetching exists only in agent live-tools / public checker) | ❌ | No customer-link fetch; adjacent to open Mimosa SSRF findings |

**Strategic read (Inferred):** the D-01 decision (open verifier: "any itinerary self/LLM/vendor") makes the *screenshot of a competitor's quote or a vendor's PDF* the highest-value modality — it is both demand capture and checker input. Voice matters for the WhatsApp corridor (Ravi use-case); URL paste is the long tail.

## 2. Modality priority (Proposed)

1. **Image via the existing operator vision lane** — do NOT build a second extractor. Extend the customer inbound path to accept an attachment envelope and route it through `trip_documents`' extraction service into the canonical packet (`Slot.extraction_mode = ATTACHMENT_EXTRACT`, `EvidenceRef` already models attachment evidence, `src/intake/packet_models.py:126-181`). This is an extension of the canonical intake, not a parallel system.
2. **PDF** — same lane, same envelope (vision providers already handle `application/pdf`).
3. **Voice** — needs an ASR DECIDE (below); transcript then flows into the normal text path with `actor_type=traveler` provenance.
4. **URL fetch** — last; SSRF-gated design prerequisite.

## 3. Decisions required (DECIDE rows)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D-ASR | ASR provider | OpenAI Whisper API (already a vision provider relationship) vs Deepgram vs WhatsApp-native voice transcripts (channel-side, zero marginal cost, arrives as text webhook) | **WhatsApp-native first** if the WhatsApp channel (C5) lands — the corridor's voice notes arrive already transcribed by Meta; Whisper as the generic fallback. No ASR spend until a non-WhatsApp voice need is observed. |
| D-ENV | Attachment envelope shape | Extend existing inbound message schema vs EX-04 capability-token BYO flow | Extend inbound (one canonical envelope: `attachments: [{kind: image|pdf|voice|url, storage_ref, mime}]`), keep EX-04 tokens for the public checker side |
| D-PII | PII posture for images/voice | Extract-then-discard media vs retain for audit | Retain encrypted (aligns with A4 encryption-migration lane), extract facts + evidence refs, media not exposed on traveler surfaces |

## 4. Security prerequisites (hard gates, not optional)

- **URL fetch:** server-side allowlist (scheme https, DNS-resolves-to-public, size cap, redirect policy, no private/loopback/metadata ranges) — the same class as the open Mimosa SSRF findings (`frontend/src/app/api/inbox/route.ts` et al.); build the allowlist helper once in `tools/`-shared form and reuse for any fetch surface. Until then: **no URL modality**.
- **Upload validation:** mime sniffing (not client-declared), max size, image/PDF only at launch, virus-scan hook left as a documented TODO with the exact check named.
- **Prompt-injection:** OCR'd/vision-extracted text is untrusted input — it must flow through the same extraction-trust boundary as customer text (E-H adversarial corpus already seeds injection cases; add screenshot-of-quote fixtures).

## 5. Implementation sketch (Proposed, sized)

| Step | Size | Note |
|---|---|---|
| S1 attachment envelope on inbound + storage | S | extends message schema; no new router |
| S2 route image/PDF through existing extraction service into packet slots | M | reuses `trip_documents` extract/apply; needs agency-scope on the storage ref |
| S3 screenshot-of-quote fixture set + injection cases in E-H corpus | S | failure-becomes-fixture rule |
| S4 WhatsApp inbound media webhook (blocked on C5 channel decision) | M | voice arrives as transcript; images as media refs → S2 |
| S5 URL fetch with allowlist helper | M | after Mimosa SSRF remediation pattern exists |

**Sequencing:** S1–S3 whenever the marketplace funnel moves; S4 gated on C5; S5 last. Nothing here blocks, or is blocked by, the current Wave A work.
