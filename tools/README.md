# Tools

This directory stores reusable helper utilities for this project.

## 1) `context_digest.py`

Purpose:
- Convert large exported conversation/context `.txt` files into structured summaries.
- Keep the full source context intact while generating a quick navigation layer.

Use cases:
- Ingest large chat exports from Downloads into project documentation.
- Produce action candidates and theme clustering for planning.
- Generate JSON + Markdown digest artifacts for traceability.

Usage:
```bash
python tools/context_digest.py \
  --input Archive/context_ingest/travelagency_context_2026-04-14.txt \
  --output-md Docs/context/CONTEXT_DIGEST_2026-04-14.md \
  --output-json Docs/context/context_digest_2026-04-14.json
```

Outputs:
- Markdown digest (`--output-md`) with sections, themes, top terms, and action candidates.
- JSON digest (`--output-json`) for automation or downstream tooling.

Notes:
- Heuristic summarization only; keep archived source as system-of-record.
- Works offline and has no third-party dependencies.
