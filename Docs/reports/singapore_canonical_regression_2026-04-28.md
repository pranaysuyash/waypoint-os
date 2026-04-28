# Canonical Singapore Regression Flow

- Generated at: 2026-04-28T16:47:47.957778+00:00
- Scenario: SC-901 - Ravi Singapore messy call - canonical regression

## Input (Exact)

```text
Hi Ravi, I got your number from my wife who is a colleague of Divya.
We are planning to visit Singapore sometime in Jan or Feb 2025.
Tentative dates around 9th to 14th Feb, approx 5 days.
Me, my wife, our 1.7 year old kid, and my parents would be going.
We don't want it rushed. Interested in Universal Studios and nature parks.
```

## Flow Results

### frontend_proxy_async_path

- Endpoint path: `/api/spine/run` via `http://localhost:3000`
- run_id: `af4133bc-cfde-4f93-8f90-3a4e894c23a7`
- Terminal state: `completed`
- trip_id: `trip_db00521bd7fc`
- Runtime (ms): `1133.24`
- Decision state: `ASK_FOLLOWUP`
- Hard constraints: `['relaxed pace']`
- Soft preferences: `['universal studios and nature parks', 'Universal Studios']`
- Negation leak (`it rushed`) present: `False`
- Follow-up questions: `[{'field_name': 'origin_city', 'priority': 'medium', 'question': 'Please provide origin city to generate a quote.'}, {'field_name': 'budget_raw_text', 'priority': 'medium', 'question': 'Please provide budget raw text to generate a quote.'}]`
- Destination status: `definite`

Observed stable behavior:
- Run reached terminal state with persisted output and no timeout stall.

### backend_direct_async_path

- Endpoint path: `/run` via `http://localhost:8000`
- run_id: `2c6ea7de-709e-4854-b625-a5a48164c937`
- Terminal state: `completed`
- trip_id: `trip_3899bf2ab37c`
- Runtime (ms): `223.09`
- Decision state: `ASK_FOLLOWUP`
- Hard constraints: `['relaxed pace']`
- Soft preferences: `['universal studios and nature parks', 'Universal Studios']`
- Negation leak (`it rushed`) present: `False`
- Follow-up questions: `[{'field_name': 'origin_city', 'priority': 'medium', 'question': 'Please provide origin city to generate a quote.'}, {'field_name': 'budget_raw_text', 'priority': 'medium', 'question': 'Please provide budget raw text to generate a quote.'}]`
- Destination status: `definite`

Observed stable behavior:
- Run reached terminal state with persisted output and no timeout stall.

