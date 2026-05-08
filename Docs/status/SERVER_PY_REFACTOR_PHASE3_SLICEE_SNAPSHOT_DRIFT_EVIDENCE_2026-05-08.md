# Slice E Snapshot Drift Evidence

Date: 2026-05-08
Scope: Evidence requested for route/openapi count discrepancy during Phase 3 Slice E review.

## Requested discrepancy
- Earlier recorded baseline: route_count=129, openapi_path_count=113
- Current working-tree fixture values: route_count=131, openapi_path_count=115

## Direct diff evidence (fixtures)
Command:
`git diff -- tests/fixtures/server_route_snapshot.json tests/fixtures/server_openapi_paths_snapshot.json`

Observed changes:
- route_count: 129 -> 131
- openapi_path_count: 113 -> 115
- Added route/path entries:
  - `/trips/{trip_id}/documents/{document_id}/extraction/attempts`
  - `/trips/{trip_id}/documents/{document_id}/extraction/retry`

## Team-slice isolation evidence
Command:
`git diff -- tests/fixtures/server_route_snapshot.json tests/fixtures/server_openapi_paths_snapshot.json | grep -n "team"`

Result:
- No matches

Interpretation:
- Fixture changes are not Team route entries.
- Team extraction itself did not alter fixture team entries.

## Blame evidence
Commands:
- `git blame -L 1,8 tests/fixtures/server_route_snapshot.json`
- `git blame -L 1,8 tests/fixtures/server_openapi_paths_snapshot.json`
- `git blame -L 920,948 tests/fixtures/server_route_snapshot.json`

Observed:
- `route_count` line and `openapi_path_count` line are marked `Not Committed Yet`.
- Added extraction routes (`/extraction/attempts`, `/extraction/retry`) are also marked `Not Committed Yet`.

Interpretation:
- 131/115 is currently an uncommitted working-tree baseline, not a committed baseline.

## Last committed fixture baseline
Commands:
- `git show d3d0554:tests/fixtures/server_route_snapshot.json | rg -n "route_count|extraction/attempts|extraction/retry|api/team"`
- `git show d3d0554:tests/fixtures/server_openapi_paths_snapshot.json | rg -n "openapi_path_count|extraction/attempts|extraction/retry|api/team"`

Observed:
- route_count=129
- openapi_path_count=113
- Team paths already present in that commit
- extraction attempts/retry paths absent in that commit

## Conclusion
- The fixture drift from 129/113 to 131/115 is real in current working tree.
- It is tied to extraction attempts/retry route additions, not Team route extraction.
- These fixture changes are uncommitted and cannot be attributed to a prior committed baseline bump yet.
- Therefore, Slice E Team extraction did not introduce Team-related fixture deltas.
