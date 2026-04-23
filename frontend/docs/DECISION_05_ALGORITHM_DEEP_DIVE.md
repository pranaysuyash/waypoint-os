# DECISION_05_ALGORITHM_DEEP_DIVE.md

## Decision Engine & Strategy System — Algorithm Deep Dive

> Comprehensive exploration of scoring algorithms, threshold optimization, and decision heuristics

---

## Table of Contents

1. [Algorithm Architecture](#algorithm-architecture)
2. [Confidence Scoring](#confidence-scoring)
3. [Completeness Scoring](#completeness-scoring)
4. [Urgency Scoring](#urgency-scoring)
5. [Risk Scoring](#risk-scoring)
6. [Ensemble Decision Making](#ensemble-decision-making)
7. [Threshold Optimization](#threshold-optimization)
8. [Feature Engineering](#feature-engineering)
9. [Model Training Pipeline](#model-training-pipeline)
10. [Algorithm Reference](#algorithm-reference)

---

## 1. Algorithm Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ALGORITHM SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        INPUT LAYER                              │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Trip Packet Data                                         │  │    │
│  │  │  • Customer demographics, history                          │  │    │
│  │  │  • Destination, dates, travelers, budget                    │  │    │
│  │  │  • Communication history, engagement signals               │  │    │
│  │  │  • Current state, days in stage, SLA info                  │  │    │
│  │  │  • Past overrides, feedback                                │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     FEATURE ENGINEERING                         │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Extract 50+ features from raw data:                      │  │    │
│  │  │  • Temporal: response_time, days_since_contact, etc.      │  │    │
│  │  │  • Engagement: email_opens, whatsapp_responses, etc.       │  │    │
│  │  │  • Content: budget_specified, dates_confirmed, etc.        │  │    │
│  │  │  • Historical: past_conversions, avg_value, etc.           │  │    │
│  │  │  • Context: seasonality, destination_type, etc.            │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      SCORING ENGINES                             │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │    │
│  │  │   CONFIDENCE   │  │ COMPLETENESS  │  │    URGENCY     │    │    │
│  │  │     SCORE      │  │    SCORE      │  │    SCORE       │    │    │
│  │  │                │  │               │  │                │    │    │
│  │  │ • Rule Engine  │  │ • Field Check │  │ • Time Decay   │    │    │
│  │  │ • ML Model     │  │ • Weighted    │  │ • SLA Calc     │    │    │
│  │  │ • Ensemble     │  │   Sum         │  │ • Stage Rules  │    │    │
│  │  └────────────────┘  └────────────────┘  └────────────────┘    │    │
│  │                                                                  │    │
│  │  ┌────────────────┐                                            │    │
│  │  │     RISK      │                                            │    │    │
│  │  │    SCORE      │                                            │    │    │
│  │  │               │                                            │    │    │
│  │  │ • Budget      │                                            │    │    │
│  │  │ • Compliance  │                                            │    │    │
│  │  │ • Historical  │                                            │    │    │
│  │  └────────────────┘                                            │    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    DECISION ORCHESTRATION                        │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  1. Check current state and valid transitions             │  │    │
│  │  │  2. Evaluate transition rules based on scores            │  │    │
│  │  │  3. Generate candidate actions with confidence            │  │    │
│  │  │  4. Apply risk filters and budget constraints             │  │    │
│  │  │  5. Rank actions and select top recommendation           │  │    │
│  │  │  6. Generate explanation with contributing factors       │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        OUTPUT LAYER                              │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  • Recommended action with confidence                      │  │    │
│  │  │  • Alternative actions with scores                         │  │    │
│  │  │  • Explanation with feature contributions                  │  │    │
│  │  │  • Confidence intervals                                    │  │    │
│  │  │  • Risk flags and warnings                                 │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Confidence Scoring

### Algorithm Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CONFIDENCE SCORING ALGORITHM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DEFINITION: How likely is this the right action for this trip?          │
│  RANGE: 0-100 (higher = more confident)                                 │
│                                                                          │
│  ENSEMBLE APPROACH                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  FINAL_CONFIDENCE = w1 × RULE_CONFIDENCE                        │    │
│  │                  + w2 × ML_CONFIDENCE                           │    │
│  │                  + w3 · HISTORICAL_CONFIDENCE                   │    │
│  │                                                                  │    │
│  │  Where weights sum to 1.0:                                       │    │
│  │  • w1 (rules) = 0.30  // Reliable, transparent                 │    │
│  │  • w2 (ML) = 0.50     // Learns patterns                       │    │
│  │  • w3 (historical) = 0.20  // Similar trip outcomes             │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  COMPONENT 1: RULE-BASED CONFIDENCE                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  rule_confidence = BASE_SCORE                                   │    │
│  │                   + engagement_boost                            │    │
│  │                   + completeness_boost                          │    │
│  │                   + timing_boost                                │    │
│  │                   - uncertainty_penalty                         │    │
│  │                                                                  │    │
│  │  BASE_SCORE = 50 (neutral starting point)                       │    │
│  │                                                                  │    │
│  │  engagement_boost:                                              │    │
│  │    • Customer responded within 2h: +15                          │    │
│  │    • Customer opened 3+ emails: +10                              │    │
│  │    • Customer asked specific questions: +12                     │    │
│  │    • Active WhatsApp conversation: +8                          │    │
│  │                                                                  │    │
│  │  completeness_boost:                                             │    │
│  │    • All required fields present: +20                           │    │
│  │    • Budget specified: +8                                       │    │
│  │    • Dates confirmed: +10                                       │    │
│  │    • Traveler count confirmed: +5                               │    │
│  │                                                                  │    │
│  │  timing_boost:                                                   │    │
│  │    • Quoted within optimal window (4-8h): +15                   │    │
│  │    • Follow-up at optimal interval: +10                         │    │
│  │    • No previous delays: +5                                     │    │
│  │                                                                  │    │
│  │  uncertainty_penalty:                                            │    │
│  │    • Budget range >50% of typical: -15                          │    │
│  │    • Dates ambiguous: -10                                       │    │
│  │    • First-time customer: -8                                    │    │
│  │    • Destination unusual for customer: -5                       │    │
│  │                                                                  │    │
│  │  Capped at 0-100 range                                          │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  COMPONENT 2: ML-BASED CONFIDENCE                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Model: Gradient Boosted Trees (XGBoost/LightGBM)               │    │
│  │  Input: 50+ features (see Feature Engineering section)           │    │
│  │  Output: Probability of action being correct                    │    │
│  │                                                                  │    │
│  │  Training:                                                      │    │
│  │  • Historical trip outcomes (converted, lost, stalled)          │    │
│  │  • Agent feedback (approved overrides, rejected suggestions)    │    │
│  │  • Temporal validation (prevent leakage)                        │    │
│  │                                                                  │    │
│  │  Features (top contributors):                                   │    │
│  │  1. engagement_score (0.32 importance)                          │    │
│  │  2. response_time_hours (0.18)                                  │    │
│  │  3. days_since_first_contact (0.12)                             │    │
│  │  4. budget_alignment_score (0.10)                               │    │
│  │  5. customer_history_conversions (0.08)                         │    │
│  │  6. communication_frequency (0.07)                              │    │
│  │  7. stage_days_ratio (0.06)                                    │    │
│  │  8. seasonal_factor (0.04)                                     │    │
│  │  9. destination_type (0.02)                                    │    │
│  │  10. traveler_count (0.01)                                     │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  COMPONENT 3: HISTORICAL CONFIDENCE                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  historical_confidence = SIMILARITY_WEIGHT × SUCCESS_RATE       │    │
│  │                                                                  │    │
│  │  Where:                                                         │    │
│  │  • SIMILARITY_WEIGHT = 0 to 1 based on feature similarity      │    │
│  │  • SUCCESS_RATE = conversion rate of similar trips             │    │
│  │                                                                  │    │
│  │  Similarity calculation (cosine similarity):                    │    │
│  │  • Compare current trip to historical trips in vector space     │    │
│  │  • Top K similar trips weighted by recency                     │    │
│  │  • Recency decay: 0.9^days_ago                                 │    │
│  │                                                                  │    │
│  │  Minimum 5 similar trips required; otherwise return 0.5         │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Confidence Calibration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIDENCE CALIBRATION                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  THE PROBLEM: Raw model probabilities often don't match real frequency  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Example: Model says 80% confidence, but only 65% of those      │    │
│  │          predictions are actually correct                       │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  THE SOLUTION: Platt Scaling / Isotonic Regression                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  1. Collect predictions vs outcomes on validation set          │    │
│  │  2. Fit calibration curve:                                     │    │
│  │                                                                  │    │
│  │     calibrated_p = f(raw_p)                                     │    │
│  │                                                                  │    │
│  │     Where f is learned from validation data                    │    │
│  │                                                                  │    │
│  │  3. Apply calibration to all future predictions                 │    │
│  │                                                                  │    │
│  │  4. Recalibrate monthly to prevent drift                        │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  RELIABILITY DIAGRAMS                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Confidence Bucket │ Predicted │ Actual │ Error               │    │
│  │  ─────────────────┼──────────┼────────┼────────              │    │
│  │  0-10%            │    5%    │   6%   │  +1%                 │    │
│  │  10-20%           │   15%    │  17%   │  +2%                 │    │
│  │  20-30%           │   25%    │  28%   │  +3%                 │    │
│  │  30-40%           │   35%    │  33%   │  -2%                 │    │
│  │  40-50%           │   45%    │  42%   │  -3%                 │    │
│  │  50-60%           │   55%    │  58%   │  +3%                 │    │
│  │  60-70%           │   65%    │  63%   │  -2%                 │    │
│  │  70-80%           │   75%    │  78%   │  +3%                 │    │
│  │  80-90%           │   85%    │  87%   │  +2%                 │    │
│  │  90-100%          │   95%    │  93%   │  -2%                 │    │
│  │                                                                  │    │
│  │  Well-calibrated model has error <5% across all buckets         │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Completeness Scoring

### Algorithm Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETENESS SCORING ALGORITHM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DEFINITION: How complete is the trip information?                       │
│  RANGE: 0-100 (higher = more complete)                                  │
│                                                                          │
│  FORMULA:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  completeness = Σ(field_weight × field_score) / Σ(field_weights) │    │
│  │                                                                  │    │
│  │  Where each field has:                                           │    │
│  │  • weight: importance (0-1)                                     │    │
│  │  • score: quality of data (0-1)                                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  FIELD DEFINITIONS                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  CRITICAL FIELDS (weight = 1.0)                                 │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ FIELD              │ WEIGHT │ SCORE CALCULATION         │    │    │
│  │  │ ───────────────────┼────────┼───────────────────────────│    │    │
│  │  │ destination        │  1.0   │ 1 if present, 0 if not   │    │    │
│  │  │ travel_dates       │  1.0   │ 1 if exact, 0.5 if range │    │    │
│  │  │ traveler_count     │  1.0   │ 1 if exact, 0.5 if range │    │    │
│  │  │ contact_info       │  1.0   │ 1 if phone+email        │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  IMPORTANT FIELDS (weight = 0.7)                                 │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ FIELD              │ WEIGHT │ SCORE CALCULATION         │    │    │
│  │  │ ───────────────────┼────────┼───────────────────────────│    │    │
│  │  │ budget             │  0.7   │ Based on specificity     │    │    │
│  │  │ travel_class       │  0.7   │ 1 if specified          │    │    │
│  │  │ trip_type          │  0.7   │ 1 if specified          │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  ENHANCING FIELDS (weight = 0.4)                                 │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ FIELD              │ WEIGHT │ SCORE CALCULATION         │    │    │
│  │  │ ───────────────────┼────────┼───────────────────────────│    │    │
│  │  │ preferences        │  0.4   │ Count of prefs / 5       │    │    │
│  │  │ special_requests   │  0.4   │ 1 if present             │    │    │
│  │  │ past_trips         │  0.4   │ Based on history depth    │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  CONTEXT FIELDS (weight = 0.2)                                  │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ FIELD              │ WEIGHT │ SCORE CALCULATION         │    │    │
│  │  │ ───────────────────┼────────┼───────────────────────────│    │    │
│  │  │ source             │  0.2   │ 1 if known               │    │    │
│  │  │ referral_info      │  0.2   │ 1 if known               │    │    │
│  │  │ occasion           │  0.2   │ 1 if known               │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  BUDGET SPECIFICITY SCORE                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  budget_score = base_score + specificity_bonus                  │    │
│  │                                                                  │    │
│  │  base_score:                                                     │    │
│  │  • No budget mentioned: 0                                      │    │
│  │  • "Budget" mentioned without numbers: 0.3                     │    │
│  │  • Range given (e.g., "50-60k"): 0.6                            │    │
│  │  • Specific number: 0.8                                        │    │
│  │                                                                  │    │
│  │  specificity_bonus:                                              │    │
│  │  • Per-person breakdown: +0.1                                   │    │
│  │  • Component breakdown (flight, hotel, etc.): +0.05            │    │
│  │  • Flexibility noted: +0.05                                     │    │
│  │                                                                  │    │
│  │  Maximum score: 1.0                                              │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Urgency Scoring

### Algorithm Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       URGENCY SCORING ALGORITHM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DEFINITION: How time-sensitive is this trip?                            │
│  RANGE: 0-100 (higher = more urgent)                                    │
│                                                                          │
│  FORMULA:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  urgency = MAX(time_urgency, sla_urgency, stage_urgency)        │    │
│  │                                                                  │    │
│  │  Where we take the maximum of three urgency dimensions           │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DIMENSION 1: TIME URGENCY                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  time_urgency = f(travel_date, today, booking_window)            │    │
│  │                                                                  │    │
│  │  Booking windows (days before travel):                           │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ DAYS TO TRAVEL    │ URGENCY │ RATIONALE                 │    │    │
│  │  │ ──────────────────┼─────────┼───────────────────────────│    │    │
│  │  │ 0-7 days         │  100   │ Critical (very soon)      │    │    │
│  │  │ 8-21 days        │   90   │ High (3 weeks)             │    │    │
│  │  │ 22-45 days       │   70   │ Medium (6 weeks)           │    │    │
│  │  │ 46-90 days       │   50   │ Normal (3 months)          │    │    │
│  │  │ 91-180 days      │   30   │ Low (6 months)             │    │    │
│  │  │ 180+ days        │   10   │ Very low                   │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Adjustments:                                                    │    │
│  │  • Peak season (Dec-Jan, May-Jun): +10 urgency                 │    │
│  │  • Holiday periods: +15 urgency                                 │    │
│  │  │ Visa-required destinations: +20 urgency                    │    │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DIMENSION 2: SLA URGENCY                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  sla_urgency = f(days_since_last_action, response_sla)          │    │
│  │                                                                  │    │
│  │  SLA Breach calculation:                                         │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ SLA STATUS        │ URGENCY │ CALCULATION               │    │    │
│  │  │ ──────────────────┼─────────┼───────────────────────────│    │    │
│  │  │ Breached          │  100   │ Overdue                   │    │    │
│  │  │ Warning (80% SLA) │   80   │ Approaching deadline      │    │    │
│  │  │ Normal            │   40   │ Within SLA                │    │    │
│  │  │ Recent action     │   20   │ <25% of SLA elapsed       │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Standard SLAs by stage:                                         │    │
│  │  • New inquiry: 4 hours                                        │    │
│  │  • Price request: 8 hours                                       │    │
│  │  • Quote sent: 24 hours                                        │    │
│  │  │ Negotiation: 12 hours                                       │    │
│  │  • Awaiting decision: 48 hours                                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DIMENSION 3: STAGE URGENCY                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  stage_urgency = base_stage_urgency × days_in_stage_multiplier  │    │
│  │                                                                  │    │
│  │  Base stage urgency:                                             │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ STAGE                      │ BASE URGENCY               │    │    │
│  │  │ ───────────────────────────┼────────────────────────────│    │    │
│  │  │ INQUIRY_RECEIVED            │ 30                         │    │    │
│  │  │ PRICE_REQUEST_RECEIVED      │ 50                         │    │    │
│  │  │ QUOTE_SENT                  │ 70                         │    │    │
│  │  │ NEGOTIATION_ACTIVE          │ 60                         │    │    │
│  │  │ AWAITING_CUSTOMER_DECISION  │ 80                         │    │    │
│  │  │ BOOKING_CONFIRMED           │ 20                         │    │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Days in stage multiplier:                                       │    │
│  │  • < 25% of typical stage duration: 0.8                         │    │
│  │  • 25-75% of typical: 1.0                                       │    │
│  │  • 75-100% of typical: 1.2                                      │    │
│  │  • > 100% of typical: 1.5                                       │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Risk Scoring

### Algorithm Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        RISK SCORING ALGORITHM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DEFINITION: What is the risk level of this trip?                        │
│  RANGE: 0-100 (higher = more risky)                                     │
│                                                                          │
│  FORMULA:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  risk = MAX(budget_risk, compliance_risk, operational_risk)      │    │
│  │                                                                  │    │
│  │  We take the maximum because any single risk type can block     │    │
│  │  progress. The overall risk is the worst dimension.             │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DIMENSION 1: BUDGET RISK                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  budget_risk = f(requested_budget, market_norm, customer_history) │    │
│  │                                                                  │    │
│  │  Market norm comparison:                                          │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ DEVIATION FROM NORM  │ RISK  │ THRESHOLD                 │    │    │
│  │  │ ─────────────────────┼───────┼───────────────────────────│    │    │
│  │  │ Within ±10%          │   0   │ Normal                    │    │    │
│  │  │ +10% to +25%         │  20   │ Slightly high             │    │    │
│  │  │ +25% to +50%         │  50   │ Moderately high           │    │    │
│  │  │ +50% to +100%        │  80   │ Significantly high         │    │    │
│  │  │ Above +100%           │  100  │ Extremely high            │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Customer history adjustment:                                    │    │
│  │  • First-time customer: +10 risk                                │    │
│  │  • Past budget overruns: +15 risk                               │    │
│  │  • Consistent budget history: -10 risk                          │    │
│  │  • High-value customer: -5 risk                                 │    │
│  │                                                                  │    │
│  │  Destination-specific adjustments:                               │    │
│  │  • Luxury destinations (Maldives, Europe): +10 risk tolerance   │    │
│  │  • Budget destinations (Southeast Asia): -5 risk               │    │
│  │  • Peak season travel: +15 risk                                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DIMENSION 2: COMPLIANCE RISK                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  compliance_risk = f(customer_type, destination, trip_value)    │    │
│  │                                                                  │    │
│  │  Risk factors:                                                   │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ FACTOR                    │ IMPACT │ CONDITION             │    │    │
│  │  │ ──────────────────────────┼────────┼───────────────────────│    │    │
│  │  │ Corporate without PAN       │  +30   │ TCS compliance      │    │    │
│  │  │ International >₹5L          │  +25   │ Forex compliance     │    │    │
│  │  │ Visa-required destination    │  +20   │ Document risk       │    │    │
│  │  │ First-time international     │  +15   │ Documentation        │    │    │
│  │  │ Group booking >10 pax       │  +20   │ Coordination risk    │    │    │
│  │  │ Unusual payment pattern     │  +35   │ Fraud risk          │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Mitigating factors:                                            │    │
│  │  • GST number provided: -10                                   │    │
│  │  • Corporate with history: -15                                │    │
│  │  │ Verified payment method: -10                              │    │
│  │  • Standard itinerary: -5                                     │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DIMENSION 3: OPERATIONAL RISK                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  operational_risk = f(itinerary_complexity, supplier_risk,       │    │
│  │                        timing_constraints)                        │    │
│  │                                                                  │    │
│  │  Itinerary complexity:                                           │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ COMPLEXITY               │ RISK │ EXAMPLE                  │    │    │
│  │  │ ──────────────────────────┼──────┼──────────────────────────│    │    │
│  │  │ Point-to-point          │   0  │ Direct flight             │    │    │
│  │  │ Round-trip              │  10  │ One destination           │    │    │
│  │  │ Multi-city (2-3)        │  30  │ Multiple destinations     │    │    │
│  │  │ Complex multi-city      │  50  │ 4+ destinations           │    │    │
│  │  │ Group with add-ons      │  40  │ Custom arrangements        │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Timing constraints:                                            │    │
│  │  • Travel within 7 days: +30 risk                              │    │
│  │  • Travel during peak holiday: +20 risk                        │    │
│  │  │ • Multiple connections: +15 risk                            │    │
│  │  • Special requests (wheelchair, etc.): +25 risk               │    │
│  │                                                                  │    │
│  │  Supplier risk (from historical data):                         │    │
│  │  • New supplier: +10 risk                                       │    │
│  │  • Past cancellation issues: +20 risk                           │    │
│  │  │ Limited availability: +15 risk                               │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Ensemble Decision Making

### Combining Scores for Decisions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ENSEMBLE DECISION FRAMEWORK                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DECISION GRID                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  The decision is a function of all four scores:                │    │
│  │                                                                  │    │
│  │  decision = f(confidence, completeness, urgency, risk)          │    │
│  │                                                                  │    │
│  │  Different actions have different score requirements:           │    │
│  │                                                                  │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ ACTION            │ CONF │ COMP │ URG │ RISK │ RULE    │    │    │
│  │  │ ───────────────────┼──────┼──────┼─────┼──────┼─────────│    │    │
│  │  │ Send Quote        │ ≥70 │ ≥80 │ ≥40 │ ≤50 │ All     │    │    │
│  │  │ Request Budget    │ ≥60 │ ≥60 │ ≥60 │ ≤40 │ Any     │    │    │
│  │  │ Send Reminder     │ ≥50 │ ≥70 │ ≥70 │ ≤60 │ Any     │    │    │
│  │  │ Escalate          │ ≤40 │ Any  │ ≥80 │ ≤70 │ Urgent  │    │    │
│  │  │ Archive           │ ≤30 │ Any  │ ≤20 │ ≤30 │ Stalled │    │    │
│  │  │ Auto-approve      │ ≥90 │ ≥90 │ Any  │ ≤20 │ Strict  │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Thresholds are adaptive based on:                              │    │
│  │  • Time of day (lower thresholds during business hours)         │    │
│  │  • Workload (lower thresholds when overloaded)                  │    │
│  │  • Agent performance (higher for new agents)                    │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  CONFLICT RESOLUTION                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  When scores conflict (e.g., high urgency but high risk):       │    │
│  │                                                                  │    │
│  │  1. RISK TAKES PRECEDENCE                                      │    │
│  │     • High risk (>70) always blocks automated actions          │    │
│  │     • Requires human review regardless of other scores         │    │
│  │                                                                  │    │
│  │  2. URGENCY SECOND                                              │    │
│  │     • If urgent (>80) but low confidence, escalate             │    │
│  │     • Don't auto-act, but flag for immediate attention         │    │
│  │                                                                  │    │
│  │  3. CONFIDENCE THIRDS                                           │    │
│  │     • High confidence (>80): Can override moderate risk         │    │
│  │     • Medium confidence (50-80): Follow standard rules          │    │
│  │     • Low confidence (<50): Requires human confirmation        │    │
│  │                                                                  │    │
│  │  4. COMPLETENESS GATES                                          │    │
│  │     • Certain actions require minimum completeness              │    │
│  │     • Can't send quote without destination and dates            │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DECISION TREE EXAMPLE                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │                       START                                      │    │
│  │                          │                                        │    │
│  │                          ▼                                        │    │
│  │                 ┌─────────────────┐                              │    │
│  │                 │ Risk > 70?      │───YES──▶ ESCALATE          │    │
│  │                 └────────┬────────┘                              │    │
│  │                          │ NO                                     │    │
│  │                          ▼                                        │    │
│  │                 ┌─────────────────┐                              │    │
│  │                 │ Urgency > 80?   │───YES──▶ FLAG URGENT       │    │
│  │                 └────────┬────────┘                              │    │
│  │                          │ NO                                     │    │
│  │                          ▼                                        │    │
│  │                 ┌─────────────────┐                              │    │
│  │                 │ Confidence > 90?│───YES──▶ AUTO-APPROVE      │    │
│  │                 └────────┬────────┘                              │    │
│  │                          │ NO                                     │    │
│  │                          ▼                                        │    │
│  │                 ┌─────────────────┐                              │    │
│  │                 │ Confidence > 70?│───YES──▶ RECOMMEND         │    │
│  │                 └────────┬────────┘                              │    │
│  │                          │ NO                                     │    │
│  │                          ▼                                        │    │
│  │                       REQUEST REVIEW                              │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Threshold Optimization

### Dynamic Threshold Adjustment

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THRESHOLD OPTIMIZATION STRATEGY                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  THE PROBLEM: Fixed thresholds don't adapt to changing conditions       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Example: 70% confidence threshold                              │    │
│  │  • During busy season: Too conservative, misses opportunities    │    │
│  │  • With new model: May be miscalibrated                          │    │
│  │  • For experienced agents: Too cautious                         │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  SOLUTION: MULTI-DIMENSIONAL THRESHOLD ADJUSTMENT                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  adjusted_threshold = base_threshold × context_multiplier      │    │
│  │                                                                  │    │
│  │  Context multipliers:                                           │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │ CONTEXT                  │ MULTIPLIER │ RANGE             │    │    │
│  │  │ ──────────────────────────┼────────────┼───────────────────│    │    │
│  │  │ Base (normal)            │    1.00    │ 70%               │    │    │
│  │  │ High workload            │    0.90    │ 63%               │    │    │
│  │  │ Low workload             │    1.10    │ 77%               │    │    │
│  │  │ Peak season              │    0.85    │ 59.5%             │    │    │
│  │  │ New agent (ramp)         │    1.20    │ 84%               │    │    │
│  │  │ Experienced agent        │    0.80    │ 56%               │    │    │
│  │  │ High-value trip          │    1.15    │ 80.5%             │    │    │
│  │  │ Low-value trip           │    0.90    │ 63%               │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Final threshold is bounded: 50% ≤ threshold ≤ 95%             │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  LEARNING OPTIMAL THRESHOLDS                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Use Bayesian optimization to find optimal thresholds:          │    │
│  │                                                                  │    │
│  │  1. Define objective function:                                 │    │
│  │     maximize = (conversion_rate × value) - (error_cost × errors)│    │
│  │                                                                  │    │
│  │  2. Run A/B tests with different thresholds:                   │    │
│  │     • Variant A: 60% threshold                                  │    │
│  │     • Variant B: 70% threshold (control)                        │    │
│  │     • Variant C: 80% threshold                                  │    │
│  │                                                                  │    │
│  │  3. Measure outcomes for 2-4 weeks:                            │    │
│  │     • Conversion rate                                           │    │
│  │     • Error rate                                               │    │
│  │     • Agent override rate                                       │    │
│  │                                                                  │    │
│  │  4. Update thresholds based on results                          │    │
│  │                                                                  │    │
│  │  5. Repeat quarterly                                           │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  THRESHOLD SCHEDULES BY TIME OF DAY                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  TIME OF DAY      │ THRESHOLD │ RATIONALE                      │    │    │
│  │  ─────────────────┼───────────┼───────────────────────────────  │    │
│  │  9AM - 12PM       │    70%    │ Business hours, agents active  │    │    │
│  │  12PM - 2PM       │    65%    │ Post-lunch, faster response OK │    │    │
│  │  2PM - 6PM        │    70%    │ Core business hours           │    │    │
│  │  6PM - 10PM       │    75%    │ After-hours, more conservative  │    │    │
│  │  10PM - 9AM       │    85%    │ Night, minimal supervision     │    │    │
│  │                                                                  │    │
│  │  Weekends: +5% threshold across all times                       │    │
│  │  Holidays: +10% threshold across all times                      │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Feature Engineering

### Feature Dictionary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FEATURE ENGINEERING GUIDE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  TEMPORAL FEATURES                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FEATURE                    │ TYPE    │ DESCRIPTION            │    │
│  │  ───────────────────────────┼─────────┼───────────────────────  │    │
│  │  response_time_hours         │ numeric │ Hours to first response │    │
│  │  days_since_first_contact    │ numeric │ Days since inquiry     │    │
│  │  days_in_current_state       │ numeric │ Days in current stage  │    │
│  │  days_to_travel             │ numeric │ Days until trip date   │    │
│  │  hour_of_day                │ numeric │ Hour of last activity  │    │
│  │  day_of_week                │ numeric │ Day of week (0-6)      │    │
│  │  is_weekend                 │ binary  │ Weekend indicator       │    │
│  │  is_business_hours          │ binary  │ 9AM-6PM indicator      │    │
│  │  communication_frequency     │ numeric │ Messages per day       │    │
│  │  last_contact_gap_hours     │ numeric │ Hours since last msg   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ENGAGEMENT FEATURES                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FEATURE                    │ TYPE    │ DESCRIPTION            │    │
│  │  ───────────────────────────┼─────────┼───────────────────────  │    │
│  │  email_opens_count          │ numeric │ Total email opens       │    │
│  │  email_clicks_count         │ numeric │ Total email clicks      │    │
│  │  whatsapp_response_rate     │ numeric │ Responses/sent         │    │
│  │  question_asked_count       │ numeric │ Questions asked        │    │
│  │  specific_questions_count   │ numeric │ Specific vs generic     │    │
│  │  documents_opened_count     │ numeric │ Quotes/itineraries viewed│    │
│  │  website_visits_count       │ numeric │ Website interactions    │    │
│  │  call_count                │ numeric │ Call attempts           │    │
│  │  agent_response_count       │ numeric │ Agent messages sent    │    │
│  │  customer_initiated_count   │ numeric │ Customer first touch    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  CONTENT FEATURES                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FEATURE                    │ TYPE    │ DESCRIPTION            │    │
│  │  ───────────────────────────┼─────────┼───────────────────────  │    │
│  │  budget_specified           │ binary  │ Budget mentioned        │    │
│  │  budget_specificity_score   │ numeric │ 0-1 budget detail       │    │
│  │  dates_confirmed            │ binary  │ Exact dates given        │    │
│  │  date_range_days            │ numeric │ Width of date range     │    │
│  │  travelers_confirmed        │ binary  │ Exact count given       │    │
│  │  traveler_count             │ numeric │ Number of travelers     │    │
│  │  destination_confirmed      │ binary  │ Destination specified   │    │
│  │  destination_type           │ categorical │ Beach/Hill/City/etc │    │
│  │  travel_class_confirmed     │ binary  │ Class specified         │    │
│  │  trip_type_confirmed        │ binary  │ Leisure/Corporate/etc   │    │
│  │  special_requests_count     │ numeric │ Special requests       │    │
│  │  preferences_count          │ numeric │ Preferences given       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  HISTORICAL FEATURES                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FEATURE                    │ TYPE    │ DESCRIPTION            │    │
│  │  ───────────────────────────┼─────────┼───────────────────────  │    │
│  │  customer_trips_count        │ numeric │ Past trips             │    │
│  │  customer_conversions_count │ numeric │ Past bookings          │    │
│  │  customer_conversion_rate   │ numeric │ Historical conversion   │    │
│  │  customer_avg_value         │ numeric │ Average booking value  │    │
│  │  customer_ltv               │ numeric │ Lifetime value         │    │
│  │  last_trip_days_ago         │ numeric │ Days since last trip   │    │
│  │  preferred_destinations     │ list    │ Past destinations       │    │
│  │  budget_overrun_history     │ numeric │ Past overruns          │    │
│  │  cancellation_rate          │ numeric │ Past cancellations     │    │
│  │  referral_count             │ numeric │ Referrals made          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  CONTEXT FEATURES                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FEATURE                    │ TYPE    │ DESCRIPTION            │    │
│  │  ───────────────────────────┼─────────┼───────────────────────  │    │
│  │  season                    │ categorical │ Peak/Off/Peak       │    │
│  │  is_holiday_period          │ binary  │ Holiday travel          │    │
│  │  destination_demand         │ numeric │ Demand index           │    │
│  │  visa_required              │ binary  │ Visa needed             │    │
│  │  advance_booking_days       │ numeric │ Days ahead booking      │    │
│  │  is_group_booking           │ binary  │ >10 travelers           │    │
│  │  is_international          │ binary  │ International trip       │    │
│  │  source_channel            │ categorical │ WhatsApp/Web/Email │    │
│  │  assigned_agent_id          │ categorical │ Current agent        │    │
│  │  agent_tenure_days         │ numeric │ Agent experience        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  DERIVED FEATURES (Interaction terms)                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  • urgency × completeness (urgent but incomplete = critical)     │    │
│  │  • engagement × days_in_stage (stagnation detection)             │    │
│  │  • budget_risk × trip_value (high value + high risk = flag)     │    │
│  │  • response_time × conversion_prob (speed quality interaction)   │    │
│  │  • agent_tenure × confidence (new agents need higher confidence)│    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Feature Importance Analysis

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FEATURE IMPORTANCE RANKING                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SHAP VALUES FOR CONFIDENCE MODEL                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  RANK │ FEATURE                   │ IMPORTANCE │ DIRECTION     │    │
│  │  ─────┼───────────────────────────┼────────────┼─────────────  │    │
│  │   1  │ engagement_score          │   0.32     │      (+)      │    │
│  │   2  │ response_time_hours       │   0.18     │      (-)      │    │
│  │   3  │ days_since_first_contact  │   0.12     │      (-)      │    │
│  │   4  │ budget_alignment_score    │   0.10     │      (+)      │    │
│  │   5  │ customer_history_conv_rate│   0.08     │      (+)      │    │
│  │   6  │ communication_frequency   │   0.07     │      (+)      │    │
│  │   7  │ stage_days_ratio          │   0.06     │      (-)      │    │
│  │   8  │ seasonal_factor           │   0.04     │      (+)      │    │
│  │   9  │ documents_opened_count    │   0.02     │      (+)      │    │
│  │  10  │ traveler_count            │   0.01     │      (±)      │    │
│  │                                                                  │    │
│  │  (+) = Higher value increases confidence                        │    │
│  │  (-) = Higher value decreases confidence                        │    │
│  │  (±) = Direction depends on context                             │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  FEATURE SELECTION STRATEGY                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  1. Start with all 50+ features                                 │    │
│  │  2. Remove low-importance features (<0.005)                    │    │
│  │  3. Check for multicollinearity (VIF > 5)                      │    │
│  │  4. Remove redundant features                                   │    │
│  │  5. Validate model performance with reduced set                  │    │
│  │  6. Keep features that improve interpretability                 │    │
│  │                                                                  │    │
│  │  Final model typically uses 25-30 features                       │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Model Training Pipeline

### Training Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       MODEL TRAINING PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DATA COLLECTION                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Sources:                                                │  │    │
│  │  │  • Trip packets (all fields)                              │  │    │
│  │  │  • Communication history (WhatsApp, Email)                │  │    │
│  │  │  • Agent actions (approvals, overrides)                   │  │    │
│  │  │  • Outcomes (converted, lost, stalled)                     │  │    │
│  │  │  • Timestamps for all events                               │  │    │
│  │  │                                                          │  │    │
│  │  │  Volume target: Minimum 10,000 completed trips             │  │    │
│  │  │  Refresh: Incremental training monthly                     │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  DATA PREPROCESSING                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Steps:                                                  │  │    │
│  │  │  1. Handle missing values (impute or flag)               │  │    │
│  │  │  2. Encode categoricals (target encoding for high card)  │  │    │
│  │  │  3. Scale numerics (robust scaler for outliers)          │  │    │
│  │  │  4. Create temporal features (time since calculations)    │  │    │
│  │  │  5. Generate interaction terms                            │  │    │
│  │  │  6. Remove temporal leakage (no future data)              │  │    │
│  │  │                                                          │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  TRAIN/VALIDATE/TEST SPLIT                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  • Train: 70% (for model fitting)                         │  │    │
│  │  │  • Validate: 15% (for hyperparameter tuning)               │  │    │
│  │  │  • Test: 15% (for final evaluation)                       │  │    │
│  │  │                                                          │  │    │
│  │  │  Temporal split: Use time-based split, not random          │  │    │
│  │  │  • Train: Oldest data                                      │  │    │
│  │  │  • Test: Newest data (simulates production)               │  │    │
│  │  │                                                          │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  MODEL TRAINING                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Algorithm: LightGBM (fast, accurate, handles missing)   │  │    │
│  │  │                                                          │  │    │
│  │  │  Hyperparameter tuning (Bayesian optimization):          │  │    │
│  │  │  • Learning rate: 0.01 - 0.1                            │  │    │
│  │  │  • Num leaves: 31 - 127                                 │  │    │
│  │  │  • Max depth: 5 - 10                                     │  │    │
│  │  │  • Min data in leaf: 10 - 100                            │  │    │
│  │  │  • Bagging fraction: 0.7 - 1.0                          │  │    │
│  │  │  • Feature fraction: 0.7 - 1.0                           │  │    │
│  │  │                                                          │  │    │
│  │  │  Cross-validation: 5-fold time-series CV                 │  │    │
│  │  │                                                          │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  MODEL EVALUATION                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Metrics:                                                │  │    │
│  │  │  • ROC-AUC: Target ≥0.75                                 │  │    │
│  │  │  • Precision: Target ≥0.70 at optimal threshold          │  │    │
│  │  │  • Recall: Target ≥0.65                                   │  │    │
│  │  │  • Log loss: Monitor for calibration                      │  │    │
│  │  │  • Brier score: Probability accuracy                      │  │    │
│  │  │                                                          │  │    │
│  │  │  Calibration check: Reliability diagram error < 5%       │  │    │
│  │  │                                                          │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  DEPLOYMENT                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Steps:                                                  │  │    │
│  │  │  1. Export model to ONNX format                          │  │    │
│  │  │  2. Deploy to inference service                           │  │    │
│  │  │  3. Enable monitoring (drift detection)                   │  │    │
│  │  │  4. Set up shadow mode (compare with old model)           │  │    │
│  │  │  5. Gradual rollout (10% → 50% → 100%)                   │  │    │
│  │  │  6. Monitor performance daily                             │  │    │
│  │  │                                                          │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Algorithm Reference

### Pseudo-Code Summary

```python
# Confidence Scoring Algorithm
def calculate_confidence(trip_packet, model, rules_engine):
    # Extract features
    features = extract_features(trip_packet)
    
    # Rule-based confidence
    rule_conf = rules_engine.evaluate(features)
    rule_conf += calculate_engagement_boost(trip_packet.engagement)
    rule_conf += calculate_completeness_boost(trip_packet.data_completeness)
    rule_conf += calculate_timing_boost(trip_packet.timing)
    rule_conf -= calculate_uncertainty_penalty(trip_packet.ambiguity_flags)
    rule_conf = clamp(rule_conf, 0, 100)
    
    # ML-based confidence
    ml_conf = model.predict_proba(features) * 100
    
    # Historical confidence
    similar_trips = find_similar_trips(trip_packet, k=10)
    if len(similar_trips) >= 5:
        historical_conf = weighted_avg(
            similar_trips.success_rate,
            weights=decay_factor(similar_trips.days_ago)
        ) * 100
    else:
        historical_conf = 50  # Neutral
    
    # Ensemble
    final_conf = (
        0.30 * rule_conf +
        0.50 * ml_conf +
        0.20 * historical_conf
    )
    
    return clamp(final_conf, 0, 100)


# Completeness Scoring Algorithm
def calculate_completeness(trip_packet):
    field_weights = {
        # Critical fields
        'destination': 1.0,
        'travel_dates': 1.0,
        'traveler_count': 1.0,
        'contact_info': 1.0,
        # Important fields
        'budget': 0.7,
        'travel_class': 0.7,
        'trip_type': 0.7,
        # Enhancing fields
        'preferences': 0.4,
        'special_requests': 0.4,
        # Context fields
        'source': 0.2,
    }
    
    total_score = 0
    total_weight = 0
    
    for field, weight in field_weights.items():
        score = get_field_score(trip_packet, field)
        total_score += weight * score
        total_weight += weight
    
    return (total_score / total_weight) * 100


# Urgency Scoring Algorithm
def calculate_urgency(trip_packet):
    # Time urgency
    days_to_travel = (trip_packet.travel_date - today).days
    time_urgency = get_time_urgency(days_to_travel)
    
    # SLA urgency
    sla_hours = get_stage_sla(trip_packet.current_state)
    hours_since_action = (now - trip_packet.last_action_time).hours
    sla_ratio = hours_since_action / sla_hours
    sla_urgency = get_sla_urgency(sla_ratio)
    
    # Stage urgency
    stage_urgency = STAGE_URGENCY[trip_packet.current_state]
    days_multiplier = get_stage_days_multiplier(
        trip_packet.days_in_state,
        trip_packet.current_state
    )
    stage_urgency *= days_multiplier
    
    return max(time_urgency, sla_urgency, stage_urgency)


# Risk Scoring Algorithm
def calculate_risk(trip_packet):
    # Budget risk
    budget_deviation = (
        trip_packet.requested_budget /
        trip_packet.market_norm_budget - 1
    )
    budget_risk = get_budget_risk_from_deviation(budget_deviation)
    budget_risk += get_customer_history_adjustment(trip_packet.customer)
    budget_risk += get_destination_adjustment(trip_packet.destination)
    
    # Compliance risk
    compliance_risk = 0
    if trip_packet.is_corporate and not trip_packet.has_pan:
        compliance_risk += 30
    if trip_packet.is_international and trip_packet.value > 500000:
        compliance_risk += 25
    if trip_packet.requires_visa:
        compliance_risk += 20
    if trip_packet.pax_count > 10:
        compliance_risk += 20
    
    # Operational risk
    operational_risk = get_complexity_risk(trip_packet.itinerary)
    operational_risk += get_timing_risk(trip_packet)
    operational_risk += get_supplier_risk(trip_packet.suppliers)
    
    return max(budget_risk, compliance_risk, operational_risk)
```

---

## Summary

The Decision Engine algorithms use a **multi-dimensional ensemble approach** combining rule-based logic, machine learning, and historical patterns. Four independent scores (Confidence, Completeness, Urgency, Risk) feed into an orchestration layer that produces actionable recommendations with explainable reasoning.

**Key Design Principles:**
1. **Ensemble over single model** — Combines strengths of multiple approaches
2. **Explainable by default** — Every score can be broken down
3. **Calibrated probabilities** — Confidence matches real-world frequency
4. **Adaptive thresholds** — Adjust based on context and workload
5. **Feature engineering depth** — 50+ features capture domain nuance
6. **Continuous learning** — Monthly retraining with feedback loop

**Next Document:** DECISION_06_HUMAN_IN_LOOP_DEEP_DIVE.md — Override mechanisms and learning from human feedback
