# E2E Scenario Run — existing_plus_new

- Generated at: 2026-04-14T10:15:57.236197

| ID | Name | Stage | Decision | Mode | Confidence | Hard Blockers | Soft Blockers | Contradictions | Ambiguities |
|---|---|---|---|---|---:|---|---|---:|---:|
| S01 | Vague Lead | discovery | ASK_FOLLOWUP | normal_intake | 0.301 | origin_city, date_window, party_size | budget_raw_text, budget_min, soft_preferences | 0 | 0 |
| S02 | Confused Couple | discovery | STOP_NEEDS_REVIEW | normal_intake | 0.502 | origin_city, date_window | trip_purpose, soft_preferences | 2 | 0 |
| S03 | Dreamer Luxury vs Budget | discovery | ASK_FOLLOWUP | normal_intake | 0.177 | origin_city, date_window, party_size | budget_raw_text, budget_min, trip_purpose, soft_preferences | 0 | 0 |
| S04 | Ready to Buy | discovery | PROCEED_INTERNAL_DRAFT | normal_intake | 0.704 | - | trip_purpose, soft_preferences, budget_feasibility | 1 | 0 |
| S05 | WhatsApp Dump | discovery | ASK_FOLLOWUP | normal_intake | 0.598 | destination_candidates, date_window, party_size | soft_preferences | 0 | 2 |
| S06 | CRM Return with Fresh Data | discovery | PROCEED_INTERNAL_DRAFT | normal_intake | 0.708 | - | trip_purpose, soft_preferences, budget_feasibility | 1 | 0 |
| S07 | Elderly Pilgrimage | discovery | ASK_FOLLOWUP | normal_intake | 0.486 | origin_city, date_window | trip_purpose | 0 | 0 |
| S08 | Last-Minute Booker | discovery | ASK_FOLLOWUP | emergency | 0.588 | date_window | - | 0 | 0 |
| S09 | Stage Progression Shortlist | shortlist | ASK_FOLLOWUP | normal_intake | 0.191 | origin_city, date_window, party_size | budget_min, trip_style | 0 | 0 |
| S10 | Partial Proposal | proposal | ASK_FOLLOWUP | normal_intake | 0.229 | origin_city, date_window, party_size, selected_itinerary | special_requests, dietary_restrictions | 0 | 0 |
| S11 | Budget Stretch Signal | discovery | ASK_FOLLOWUP | normal_intake | 0.481 | origin_city, date_window | trip_purpose, soft_preferences | 0 | 1 |
| S12 | Inferred Destination | discovery | ASK_FOLLOWUP | normal_intake | 0.576 | date_window, party_size | soft_preferences | 0 | 0 |
| S13 | Multi-Envelope Accumulation | discovery | ASK_FOLLOWUP | normal_intake | 0.181 | origin_city, date_window, party_size | budget_raw_text, budget_min, trip_purpose, soft_preferences | 0 | 0 |
| N01 | Emergency Medical Routing | discovery | ASK_FOLLOWUP | emergency | 0.181 | origin_city, date_window, party_size | - | 0 | 0 |
| N02 | Hard Date Conflict | discovery | STOP_NEEDS_REVIEW | normal_intake | 0.478 | date_window, party_size | trip_purpose, soft_preferences | 2 | 0 |
| N03 | Booking Stage Fully Ready | booking | ASK_FOLLOWUP | normal_intake | 0.298 | origin_city, date_window, party_size | - | 0 | 0 |
| N04 | Budget Branching Candidate | discovery | ASK_FOLLOWUP | normal_intake | 0.181 | origin_city, date_window, party_size | budget_raw_text, budget_min, trip_purpose, soft_preferences | 1 | 0 |
| N05 | Coordinator Group Lead | discovery | ASK_FOLLOWUP | coordinator_group | 0.181 | origin_city, date_window, party_size | budget_raw_text, budget_min, trip_purpose, soft_preferences | 0 | 0 |
