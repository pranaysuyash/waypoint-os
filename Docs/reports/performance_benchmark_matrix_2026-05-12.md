# Performance Benchmark Matrix

- Generated: `2026-05-12T04:21:07.799223Z`
- Base URL: `http://127.0.0.1:3000`
- Iterations per endpoint: `2`

## Scenario: `otel_off`

- Description: Tracing disabled for frontend + backend.
- Smoke pass: `True`

| Endpoint | Avg (ms) | P50 | P95 | P99 | Max | Status OK |
|---|---:|---:|---:|---:|---:|---|
| `/api/auth/me` | 207.16 | 207.16 | 188.5 | 188.5 | 225.83 | yes |
| `/overview` | 185.55 | 185.55 | 105.5 | 105.5 | 265.6 | yes |
| `/trips` | 85.15 | 85.15 | 50.2 | 50.2 | 120.09 | yes |
| `/workbench?draft=new&tab=safety` | 49.72 | 49.72 | 48.24 | 48.24 | 51.21 | yes |
| `/api/inbox?page=1&limit=1` | 351.71 | 351.71 | 284.05 | 284.05 | 419.37 | yes |
| `/api/trips?view=workspace&limit=5` | 81.02 | 81.02 | 79.2 | 79.2 | 82.85 | yes |
| `/api/trips?view=workspace&limit=100` | 111.55 | 111.55 | 98.11 | 98.11 | 124.99 | yes |
| `/api/reviews?status=pending` | 201.61 | 201.61 | 170.93 | 170.93 | 232.3 | yes |
| `/api/inbox/stats` | 178.42 | 178.42 | 134.11 | 134.11 | 222.73 | yes |
| `/api/pipeline` | 364.35 | 364.35 | 259.83 | 259.83 | 468.87 | yes |
| `/settings` | 96.62 | 96.62 | 76.67 | 76.67 | 116.56 | yes |
| `/documents` | 215.54 | 215.54 | 182.92 | 182.92 | 248.15 | yes |

## Scenario: `otel_unreachable`

- Description: Tracing enabled but collector endpoints unreachable.
- Smoke pass: `True`

| Endpoint | Avg (ms) | P50 | P95 | P99 | Max | Status OK |
|---|---:|---:|---:|---:|---:|---|
| `/api/auth/me` | 22.98 | 22.98 | 21.21 | 21.21 | 24.75 | yes |
| `/overview` | 59.56 | 59.56 | 58.55 | 58.55 | 60.56 | yes |
| `/trips` | 84.24 | 84.24 | 57.43 | 57.43 | 111.04 | yes |
| `/workbench?draft=new&tab=safety` | 299.56 | 299.56 | 66.74 | 66.74 | 532.38 | yes |
| `/api/inbox?page=1&limit=1` | 661.28 | 661.28 | 352.28 | 352.28 | 970.28 | yes |
| `/api/trips?view=workspace&limit=5` | 44.77 | 44.77 | 41.34 | 41.34 | 48.19 | yes |
| `/api/trips?view=workspace&limit=100` | 85.49 | 85.49 | 84.17 | 84.17 | 86.81 | yes |
| `/api/reviews?status=pending` | 143.32 | 143.32 | 114.53 | 114.53 | 172.11 | yes |
| `/api/inbox/stats` | 84.55 | 84.55 | 81.1 | 81.1 | 87.99 | yes |
| `/api/pipeline` | 290.03 | 290.03 | 210.87 | 210.87 | 369.19 | yes |
| `/settings` | 71.69 | 71.69 | 51.58 | 51.58 | 91.79 | yes |
| `/documents` | 71.27 | 71.27 | 47.45 | 47.45 | 95.08 | yes |

