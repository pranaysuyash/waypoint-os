# Field Authority and Provenance v0.1

## Purpose
To prevent silent hallucinations and false confidence, every field in the `CanonicalPacket` must have an auditable trail of provenance.

---

## Authority Levels
Authority defines the precedence of a value. A lower authority level cannot overwrite a higher authority level without a recorded `manual_override` event.

| Level | Name | Description |
| :--- | :--- | :--- |
| **1** | `manual_override` | Highest authority. Explicitly set by a human planner. |
| **2** | `explicit_user` | Directly stated by the traveler during a session. |
| **3** | `imported_structured` | Value from a trusted structured source (e.g., CRM API, MakeMyTrip). |
| **4** | `explicit_owner` | Explicitly stated by the agency owner in notes. |
| **5** | `derived_signal` | A high-confidence implication (e.g., "Toddler" $\rightarrow$ "Needs nap time"). |
| **6** | `soft_hypothesis` | A pattern-level guess (e.g., "Likely comfort-first family"). |
| **7** | `unknown` | Field is unresolved. |

---

## Extraction Modes
Describes *how* the value was obtained:
- `direct_extract`: Lifted verbatim from raw text.
- `normalized`: Standardized (e.g., "B'lore" $\rightarrow$ "Bangalore").
- `inferred`: Derived from other facts.
- `imported`: Loaded from structured source.
- `manual_override`: Set by human user.
- `unknown`: No value.

---

## Evidence References
A field is only "Fact" if it has at least one `EvidenceRef`.

**Evidence Types:**
- `text_span`: Excerpt from raw text.
- `structured_field`: Path in a source JSON.
- `attachment_extract`: Data from a PDF/Image.
- `transcript_segment`: Timestamped segment from voice.
- `manual_note`: Reference to an internal planner note.

---

## Provenance Rules
1. **No Orphan Facts**: Every field with `authority_level < 6` must have at least one `evidence_ref`.
2. **No Silent Overwrites**: If a `derived_signal` conflicts with an `explicit_owner` fact, the `explicit_owner` value is kept, and a `Contradiction` is logged.
3. **Auditability**: Any change to a field must emit an event in the `Event Log` containing the `actor_id` and `reason`.
