# Waypoint OS (`travel_agency_agent`) — Strategic Feature Roadmap & Architectural Specifications

**Document Date**: 2026-08-07  
**Author**: Waypoint Agentic AI Team  
**Status**: APPROVED & CAPTURED  
**Idea Pad Tracked Items**: IDEA-120, IDEA-121, IDEA-122, IDEA-123  

---

## Overview

This document formalizes the strategic features and platform architecture enhancements for Waypoint OS (`travel_agency_agent`). These initiatives extend the core engine (Multi-Channel Inbound Parsing, Stage 1/2 Teaser Unmasking, Yield Arbitrage, and Corporate Policy Audit) into a high-end autonomous agency operating system.

---

## 1. Autonomous Price-Lock Sentinel (`IDEA-120`)

### Concept & Value
A background worker that continuously monitors GDS and NDC supplier APIs during the 72-hour price lock window (`price_lock_expires_at`). If a lower rate or superior inventory becomes available, the Sentinel auto-holds the lower rate before traveler deposit confirmation.

### Architectural Blueprint
* **Module**: `src/services/price_lock_sentinel.py` & `spine_api/routers/price_lock.py`
* **Data Flow**:
  1. Cron task scans active trips in `STAGE_1_TEASER` where `now() < price_lock_expires_at`.
  2. Queries GDS/NDC connector facade (`Amadeus`, `Sabre`, `HotelBeds`) for matching flight/hotel keys.
  3. If rate drops by >5%:
     - Re-locks lower price quote.
     - Logs `price_lock_arbitrage_saved` event to `AuditStore`.
     - Updates trip record `strategy.recommended_option` with new margin.

---

## 2. Dynamic Visual Teaser & Interactive Itinerary Builder (`IDEA-121`)

### Concept & Value
Upgrades public traveler proposal links (`/proposals/{proposalId}`) into visual, interactive web itineraries featuring interactive maps, day-by-day climate forecasts, and real-time hotel/activity galleries.

### Architectural Blueprint
* **Frontend Component**: `frontend/src/app/proposals/[proposalId]/visual`
* **Data Flow**:
  1. Integrates Mapbox GL JS for dynamic route rendering.
  2. Surfaces interactive day-by-day accordion cards with high-res supplier images.
  3. Provides instant 1-click "Lock Deposit ($25)" modal with Stripe Payment Element.

---

## 3. Group Trip Multi-Payer Split Deposit Portal (`IDEA-122`)

### Concept & Value
Shared link portal for multi-passenger bookings (bachelor/bachelorette trips, corporate retreats, family reunions) allowing attendees to vote on itinerary options and pay individual deposit shares.

### Architectural Blueprint
* **Module**: `spine_api/routers/group_booking.py`
* **Data Flow**:
  1. Generates unique passenger invite tokens (`/group/{groupId}/join`).
  2. Calculates per-passenger deposit share (`total_deposit / passenger_count`).
  3. Tracks individual payment statuses (`unpaid`, `holding`, `paid`) before advancing trip stage to `STAGE_2_DEPOSIT_PAID`.

---

## 4. Voice & WhatsApp Native AI Inbound Handler (`IDEA-123`)

### Concept & Value
Direct Voice AI call handler (via Twilio Media Streams + ElevenLabs / Gemini Multimodal Live) for phone-first luxury clientele. Automatically transcribes inbound calls, scrubs PII, and converts conversation into `CanonicalPacket` v0.3 facts.

### Architectural Blueprint
* **Module**: `spine_api/routers/voice_inbound.py`
* **Data Flow**:
  1. Webhook receives audio stream from Twilio.
  2. Processes speech-to-text and extracts structured trip facts (`destination`, `budget`, `dates`, `passengers`).
  3. Ingests packet via `pipeline.extract(...)` and saves trip to `TripStore`.

---

## Summary Matrix

| Idea ID | Feature Name | Primary Layer | Owner | Target Milestone |
| :--- | :--- | :--- | :--- | :--- |
| **IDEA-120** | Autonomous Price-Lock Sentinel | `spine_api/services` | antigravity | Q3 2026 |
| **IDEA-121** | Dynamic Visual Teaser Builder | `frontend/src/app` | antigravity | Q3 2026 |
| **IDEA-122** | Group Split Deposit Portal | `spine_api/routers` | antigravity | Q3 2026 |
| **IDEA-123** | Voice AI Inbound Handler | `src/intake` | antigravity | Q4 2026 |
