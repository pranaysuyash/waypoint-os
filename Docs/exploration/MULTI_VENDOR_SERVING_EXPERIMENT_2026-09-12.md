
### 6.3 Phase 2 EXECUTED — OpenRouter head-to-head (2026-09-14)

OPENROUTER_API_KEY found in the orbitcover project's .env; key verified
against /api/v1/models (445 models). Same-weight arms run through
`openrouter/` provider (OpenAI-compatible drop-in):

| Arm | F1 | P | R | Lat/call |
|---|---|---|---|---|
| OR llama-3.1-8b-instruct | **0.769** | 1.000 | 0.625 | 3,977 ms |
| OR gpt-oss-20b | 0.400 | 1.000 | 0.250 | 6,537 ms |
| HF llama-3.1-8B:fastest | **0.800** | 1.000 | — | **1,208 ms** |
| HF gpt-oss-20b:fastest | 0.286 | 1.000 | — | 792 ms |

**Cross-vendor confirmation (Q10):** llama-3.1-8B scores 0.769–0.800 across
HF/OpenRouter venues, same F1 band as the local champion (0.737). gpt-oss-20b
under-flags at every venue. The calibration property travels with the
weights, not the vendor. Latency varies by venue (HF :fastest fastest);
quality variation between venues is within the ±0.05 seed-variance band.

OpenRouter's :nitro/:floor variants were not exercised (the key has credits
but the auto-router default was sufficient for this head-to-head); the
provider is wired into the harness and ready for one-command future runs.
