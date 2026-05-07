# Pre-Mortem 05: Security & Privacy

**Project:** Waypoint OS
**Role:** Privacy / Trust Prosecutor
**Emotional Register:** Principled outrage — every ambiguity is treated as a deliberate violation.
**Date:** 2026-05-05

*"It is 3 months after beta launch. The launch went badly."*

---

## Finding 1: Production Encryption Key Is Hardcoded in Source

**What goes wrong:** The encryption key `v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8=` is hardcoded as a literal string at `src/security/encryption.py:25`. Anyone with repo access — developer, CI pipeline, compromised machine — can decrypt all stored PII.

**Chain of events:**
- Encryption key lives in code, not env var. The env var fallback exists but is never actually required before the dev key is used.
- `DATA_PRIVACY_MODE=production` raises only if ENCRYPTION_KEY is missing entirely — but since the code falls through to the hardcoded key on line 25 first, production mode with that key still works.
- Any contributor with read access to the repo now has the master key to decrypt all user data.

**User experience:** User has no idea their PII is encrypted with a publicly known key. They trust the system because of the security module.

**Emotional impact:** Betrayal — users believed their data was protected.

**Why team misses it:** The code has all the right structure (Fernet, env var, lru_cache pattern). It looks correct. The hardcoded string blends in with legitimate defaults.

**Likelihood x Impact:** High x Catastrophic
**Trust damage:** Catastrophic
**Recoverability:** Hard — key cannot be un-leaked; every user's data must be re-encrypted with a new key.
**Earliest signal:** A team member notices the literal key in source review.
**Verify by:** Check any non-dogfood deployment: `grep -n "v-k_y8Y5C8h7" .env` or similar; verify no deployment uses the source file's default.

---

## Finding 2: Decryption Silently Returns Plaintext on Failure

**What goes wrong:** `decrypt()` at line 51-53 catches ALL exceptions and returns the raw ciphertext unchanged. When the key rotates, old data decrypts to garbage and is silently returned as-is — unencrypted ciphertext presented to the application as valid data.

**Chain of events:**
- Admin rotates encryption key (correct practice).
- Old trip data was encrypted with old key.
- `decrypt()` fails (wrong key), exception is caught.
- The raw Fernet token string (binary garbage) is returned.
- Application tries to use this as valid trip data, producing crashes, corrupted reports, or silently persisted garbage.

**User experience:** "My trip vanished" — the data is technically present but unreadable, and the system doesn't tell anyone.

**Emotional impact:** Confusion and loss of confidence, then anger when the truth emerges.

**Why team misses it:** The fallback comment says "might be plaintext from old data." This assumes pre-encryption data, not post-key-rotation data. The error path treats decryption failure as a migration compatibility feature, not a security boundary.

**Likelihood x Impact:** Medium x Catastrophic
**Trust damage:** High
**Recoverability:** Hard — once decrypt returns garbage that gets persisted, original data is gone. Requires backup restoration.
**Earliest signal:** Application logs show "Decryption failed" warnings in prod but no one monitors them because they're `logger.warning`, not an alert.
**Verify by:** Rotate the key in a staging environment and verify the system catches the mismatch before serving corrupted data.

---

## Finding 3: Privacy Guard Only Checks Persistence, Not Transmission

**What goes wrong:** `check_trip_data()` in `privacy_guard.py` only blocks PII from being WRITTEN TO DISK in dogfood mode. The data was already sent to OpenAI/Gemini APIs before this check runs. In beta/production, the guard does nothing at all.

**Chain of events:**
- Agency operator submits a trip with traveler name, phone, email, medical notes.
- Pipeline sends the full trip data to LLM (OpenAI/Gemini) for extraction and decision-making.
- PII is now on OpenAI/Gemini servers in the US, processed through their models.
- Privacy guard then runs and checks whether to persist the data — but the data has already left the building.
- In beta/production, the guard is completely disabled (no-op on line 325-327).

**User experience:** Invisible — user never knows their data left their jurisdiction.

**Emotional impact:** Violation — if discovered, the user feels surveilled and deceived.

**Why team misses it:** The privacy guard is architected correctly for dogfood (block storage of real data). The docstring says "encryption should be active" for beta/prod. But there's no guard on what data leaves the server to LLM providers.

**Likelihood x Impact:** High x Catastrophic
**Trust damage:** Catastrophic
**Recoverability:** Hard — data already sent to third-party servers, potentially used for model training.
**Earliest signal:** A beta agency submits a trip with a real client's passport number. No one notices until the traveler complains.
**Verify by:** Check the LLM client code paths — trace what data is included in the prompt sent to each provider.

---

## Finding 4: Jurisdiction Policy Is Dead Code

**What goes wrong:** The `jurisdiction_policy.py` file defines comprehensive policies for GDPR, DPDP, CCPA — but `should_block_pii()` and `requires_erasure_capability()` are never called from any production code path.

**Chain of events:**
- Agency signs up from EU, their jurisdiction is set to "eu".
- No code path ever reads this jurisdiction to apply GDPR rules.
- EU traveler data flows to US-based LLM providers without consent, without data residency checks, without breach notification capability.
- If a traveler requests data erasure, there's no endpoint or tool to execute it.

**User experience:** Agency believes the system handles compliance. EU travelers are unprotected.

**Emotional impact:** Betrayal of professional trust — the agency promised compliance to their travelers.

**Why team misses it:** The jurisdiction module is well-written and tested. It looks complete. The gap is in the integration — no code calls it.

**Likelihood x Impact:** High x Major
**Trust damage:** High (if discovered by regulator)
**Recoverability:** Hard — retroactive compliance is expensive.
**Earliest signal:** First EU agency tries to onboard.
**Verify by:** Search for calls to `should_block_pii`, `requires_erasure_capability`, or any jurisdiction policy function: `grep -rn "jurisdiction_policy\|should_block_pii\|requires_erasure\|get_jurisdiction" src/ --include="*.py"`

---

## Finding 5: Data Accumulation With No Lifecycle

**What goes wrong:** 814 run directories, 144 per_trip override files, 4 audit corruption recoveries, and no cleanup mechanism. Data grows unbounded.

**Chain of events:**
- Each pipeline run creates a new directory under `data/runs/`.
- Override files accumulate in `data/overrides/per_trip/` and get synced to `index.json`.
- Audit log appends to a single `events.jsonl` file that will eventually hit filesystem limits.
- After months of use, storage swells with stale data. No GC. No archival. No retention policy.

**User experience:** Invisible — until disk fills and the system stops processing trips.

**Emotional impact:** Frustration and loss of trust when "it just stopped working."

**Why team misses it:** Growth is slow at first. The system works fine for months before hitting limits. By then, cleanup is disruptive.

**Likelihood x Impact:** High x Major
**Trust damage:** Medium
**Recoverability:** Hard — need to build cleanup tooling while system is down.
**Earliest signal:** `df -h` shows >80% disk usage.
**Verify by:** Project growth curve: 814 run dirs from how many development sessions? Multiply by expected daily rate for 5 agencies.

---

## Finding 6: Beta/Production Mode Has No Encryption Enforcement

**What goes wrong:** The privacy guard's beta/production mode (line 325-327) does nothing — it just returns. The docstring says "encryption should be active for real users" but there's zero enforcement. A deployment in `DATA_PRIVACY_MODE=beta` will store all PII in plaintext JSON files with no warning.

**Chain of events:**
- Founder deploys beta, sets DATA_PRIVACY_MODE=beta.
- First real trip data from a beta agency arrives.
- Privacy guard passes (beta mode allows everything).
- Data is stored in plaintext JSON on disk at `data/trips/trip_*.json`.
- No encryption key check. No warning log. No prompt to configure.

**User experience:** Zero indicators of a problem. Nothing breaks. But data is wide open.

**Emotional impact:** Invisible until discovered — then devastating.

**Why team misses it:** The guard doesn't blow up. The app works fine. The failure is silent by design.

**Likelihood x Impact:** Near-certain x Catastrophic
**Trust damage:** Catastrophic
**Recoverability:** Moderate if caught early; impossible if data already breached.
**Earliest signal:** A team member reviews the privacy guard behavior.
**Verify by:** Run in beta mode, submit a trip, cat the JSON file — is it plaintext?

---

## The Failure Nobody Wants to Talk About

The system will never have a "data breach" as a single event. Instead, data leaks continuously through multiple channels — LLM API calls to third parties, plaintext storage in JSON files, a publicly known encryption key, and silent failures on key rotation — and nobody will notice because the privacy guard only checks one of these paths and the rest are invisible to monitoring. The first anyone learns of it is when a traveler asks "how did OpenAI get my passport details?" or when a regulator shows up asking about the unencrypted JSON files containing traveler medical data. Every single security control was correctly conceived and then incompletely wired, creating the illusion of protection without its substance.
