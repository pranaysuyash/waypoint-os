# ripgrep vs FFF benchmark (travel_agency_agent)

Date: 2026-05-08
Repo: `/Users/pranay/Projects/travel_agency_agent`

## Objective

Benchmark real search behavior for `ripgrep` (`rg`) vs `FFF` (`@ff-labs/fff-node`) on this codebase and decide what should be the default search tool in instructions.

Scope requested:
- speed
- match accuracy/coverage
- memory usage

## Tooling tested

- `rg` version: `ripgrep 14.1.1`
- `FFF` runtime: `@ff-labs/fff-node` (native Rust-backed library)

Benchmark harness:
- `tools/benchmarks/rg_vs_fff/benchmark.mjs`
- Output JSON: `tools/benchmarks/rg_vs_fff/benchmark_results.json`
- Run log with process-level peak RSS: `tools/benchmarks/rg_vs_fff/benchmark_run.log`

## Methodology

1. Same repository searched by both tools.
2. Content-search queries:
   - `TODO`
   - `FastAPI`
   - `Trip`
   - `confidence`
   - one runtime-generated guaranteed-miss token
3. `rg` execution:
   - `rg --no-heading --line-number --color never --smart-case --max-filesize 10M <query> .`
4. `FFF` execution:
   - `finder.grep(query, { mode: "plain", smartCase: true, maxFileSize: 10MB, maxMatchesPerFile: 0 })`
5. Accuracy comparison key:
   - normalized `file_path:line_number`
6. Memory measurement:
   - `rg`: `/usr/bin/time -l` max RSS per query run
   - `FFF`: process RSS after scan + live process RSS during query run
   - whole benchmark process max RSS from `/usr/bin/time -l node benchmark.mjs`

## Results (latest run)

Source: `tools/benchmarks/rg_vs_fff/benchmark_results.json` generated `2026-05-08T05:31:57.868Z`

### 1) Speed

- Query `TODO`
  - rg: 119.769 ms
  - FFF: 13.958 ms
  - FFF faster: 8.58x

- Query `FastAPI`
  - rg: 53.353 ms
  - FFF: 41.787 ms
  - FFF faster: 1.28x

- Query `Trip` (high match volume)
  - rg: 71.406 ms
  - FFF: 828.085 ms
  - rg faster: 11.60x

- Query `confidence` (high match volume)
  - rg: 74.962 ms
  - FFF: 673.811 ms
  - rg faster: 8.99x

- Query `random-miss-token` (0 matches)
  - rg: 47.577 ms
  - FFF: 0.295 ms
  - FFF faster: 161.28x

Net effect on this repo:
- FFF is very strong on miss/low-volume lookups.
- rg is dramatically faster on broad, high-match content searches.

### 2) Accuracy / coverage

- `TODO`: exact parity (`rgOnly=0`, `fffOnly=0`)
- `FastAPI`: FFF has +19 lines (`rgOnly=0`, `fffOnly=19`)
- `Trip`: FFF has +52 lines (`rgOnly=0`, `fffOnly=52`)
- `confidence`: FFF has +591 lines (`rgOnly=0`, `fffOnly=591`)
- miss token: exact parity at zero

Interpretation:
- FFF returns a strict superset vs rg in several queries on this repo.
- Main operational implication: result set consistency is not identical; switching defaults changes what users see.

### 3) Memory

- `rg` per-query max RSS: ~10–11 MB.
- `FFF` RSS after initial scan: ~71.8 MB.
- `FFF` live RSS grows with heavy queries: up to ~200+ MB in benchmark process.
- Whole benchmark process max RSS (`/usr/bin/time -l node benchmark.mjs`): 202,424,320 bytes.

Interpretation:
- rg is far more memory-efficient for one-off content search.
- FFF has significant resident-memory overhead due index/state and native engine lifecycle.

## Decision

For this project, keep **ripgrep (`rg`) as the default content search tool**.

Why:
1. Better worst-case behavior on high-volume search, which is common in engineering workflows.
2. Much lower memory footprint.
3. Stable, predictable output set already aligned with existing workflows.

When to use FFF:
- Interactive/fuzzy file-finding workflows.
- Very frequent repeated miss/needle lookups where warmed indexing helps.
- Cases where expanded recall is intentionally desired and memory overhead is acceptable.

## Practical policy update

Default policy to add to instructions:

- Use `rg` for content search by default.
- Do not use `grep` for repo search.
- Use FFF only when explicitly needed for fuzzy/indexed behavior and when available in environment.

## Repro commands

From repo root:

```bash
cd tools/benchmarks/rg_vs_fff
node benchmark.mjs
/usr/bin/time -l node benchmark.mjs > benchmark_run.log 2>&1
```

## Known caveats

- FFF is currently exercised via Node binding (`@ff-labs/fff-node`), not a standalone `fff` CLI binary.
- Results are repo-shape dependent. If repo composition changes significantly, rerun this benchmark.
- Query mix strongly affects winner; broad/high-hit queries favor rg on this codebase.
