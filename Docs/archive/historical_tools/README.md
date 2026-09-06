# Historical source-writing tools

Archived on 2026-09-05 after semantic comparison and a passing frontend full
test/typecheck/lint/build baseline. The `.py.txt.gz` files preserve exact original
bytes as historical provenance. The adjacent `.py.txt` files are readable
transcripts, with trailing whitespace normalized in the visualizer writer.
Neither representation is a supported command; do not import or execute them.
Their former top-level writes could overwrite maintained UI.

| Former path | Preserved artifact | Canonical maintained target |
|---|---|---|
| `scripts/update_council_panel.py` | [Updater source](update_council_panel.py.txt) | `frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx` |
| `scripts/write_visualizers.py` | [Visualizer writer source](write_visualizers.py.txt) | `JourneyGraphVisualizer.tsx` and `TimeTravelScrubber.tsx` in the same workbench directory |

## Original-byte preservation and recovery

Created with `gzip -n -k` before transcript normalization on 2026-09-05.
No timestamp or original filename is embedded in the gzip header. Decoding
both archives reproduced the original SHA-256 values below. The payloads were
reviewed as text before compression; a clean binary Git diff is not a payload
scan. Only the five trailing-whitespace lines in the visualizer transcript
differ from its decoded original. The updater transcript is byte-identical.

| Original archive | Decoded bytes | Decoded SHA-256 | Compressed SHA-256 |
|---|---|---|---|
| [Updater original](update_council_panel.py.txt.gz) | 1538 | `798d05ff4730ff3c86087c34c0a948519e11d472f087637137fef6a4ec65d8a9` | `7945771e0417df518493557f1b2011e2f2802b55cab1e967414760b895d52776` |
| [Visualizer original](write_visualizers.py.txt.gz) | 14748 | `753e1572e8f17525ff60330e3372f63cf1dfb68f48b0bf2122f272f085db50e2` | `29c4397ce5d4cce6738e15ad513f8bdb84dc152c756714119f71a2c0802c7440` |

From the repository root, inspect the original without restoring execution:

```bash
gzip -cd Docs/archive/historical_tools/write_visualizers.py.txt.gz | less
gzip -cd Docs/archive/historical_tools/write_visualizers.py.txt.gz | shasum -a 256
```

The maintained TSX files remain the only product source of truth; transcripts
are not an independently editable generator. After delivery whitespace cleanup,
the Journey Graph target differs from its historical embedded output only by
the same five trailing-whitespace repairs. The earlier byte-equality receipt
is explicitly a pre-formatting comparison.

The updater's imports, union members and renders already exist; rerunning it
duplicates imports/renders and misses changed text. The writer's embedded
outputs are byte-identical to the two maintained targets. No unique product
behavior was discarded. No supported code invocation was found outside
historical documentation/CSV references.

Detailed comparison, original hashes, recovery and delivery boundaries:
[A1-1 artifact review](../../review/A1_1_DELIVERY_ARTIFACT_REVIEW_2026-09-05.md).
To inspect historical intent, read these text artifacts; do not restore their
execution path as a workaround. Any future generator needs an explicit recurring
use case, preconditions, idempotence, dry run and refusal of unknown targets.
