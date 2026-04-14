# E2E Scenario Run — rest

- Generated at: 2026-04-14T00:51:18.427995

| ID | Name | Stage | Decision | Mode | Confidence | Hard Blockers | Soft Blockers | Contradictions | Ambiguities |
|---|---|---|---|---|---:|---|---|---:|---:|
| S06 | CRM Return with Fresh Data | discovery | ASK_FOLLOWUP | normal_intake | 0.708 | budget_feasibility | trip_purpose, soft_preferences | 1 | 0 |
| S07 | Elderly Pilgrimage | discovery | ASK_FOLLOWUP | normal_intake | 0.486 | origin_city, date_window | trip_purpose | 0 | 0 |
| S08 | Last-Minute Booker | discovery | ASK_FOLLOWUP | emergency | 0.588 | date_window | - | 0 | 0 |
| S09 | Stage Progression Shortlist | shortlist | ASK_FOLLOWUP | normal_intake | 0.191 | origin_city, date_window, party_size | budget_min, trip_style | 0 | 0 |
| S10 | Partial Proposal | proposal | ASK_FOLLOWUP | normal_intake | 0.229 | origin_city, date_window, party_size, selected_itinerary | special_requests, dietary_restrictions | 0 | 0 |
| S11 | Budget Stretch Signal | discovery | ASK_FOLLOWUP | normal_intake | 0.481 | origin_city, date_window | trip_purpose, soft_preferences | 0 | 1 |
| S12 | Inferred Destination | discovery | ASK_FOLLOWUP | normal_intake | 0.576 | date_window, party_size | soft_preferences | 0 | 0 |
| S13 | Multi-Envelope Accumulation | discovery | ASK_FOLLOWUP | normal_intake | 0.181 | origin_city, date_window, party_size | budget_raw_text, budget_min, trip_purpose, soft_preferences | 0 | 0 |
