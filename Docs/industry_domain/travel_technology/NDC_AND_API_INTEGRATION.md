# NDC and API Integration for Travel Agencies

## Overview
This document explains how modern agency technology integrates with airline and supplier systems via APIs, including the New Distribution Capability (NDC) standard.

## What NDC is
- NDC is an IATA standard for airline distribution that moves airline content away from legacy EDIFACT/GDS messaging.
- It enables more expressive offers, dynamic bundling, and richer ancillary merchandising.
- For agencies, NDC creates the potential for differentiated pricing, true fare transparency, and better product control.

## Core integration patterns
### GDS-based booking
- Traditional distribution using Sabre, Amadeus, Travelport, or other host systems.
- Good for broad inventory coverage and familiar workflow support.
- Often still the baseline for corporate and wholesale bookings.

### NDC-direct/API-based booking
- Direct connection to airline APIs or NDC aggregators.
- Useful for premium, corporate, and value-added product offerings.
- Requires mapping between airline-specific payloads and the agency's mid-office system.

### Hybrid distribution
- Use GDS for confirmed PNR creation and NDC for supplementary offers, ancillaries, or special fares.
- Many agencies operate a hybrid stack during the transition period.

## Integration considerations
- Data model mapping: align passenger data, fare rules, ancillaries, and ticketing instructions.
- Pricing consistency: ensure the total price shown to the traveler matches the supplier invoice.
- Inventory reliability: validate that direct API availability and GDS availability are synchronized.
- Exception handling: design workflows for booking failures, reprice triggers, and policy validation.

## Operational capabilities enabled
- Dynamic bundling of baggage, seats, lounge access, and flexible fare options.
- Personalized offers and traveler preference-based upsell.
- Better recovery from ticketing or itinerary change exceptions.

## Why this matters
As airline distribution evolves, agencies that manage NDC/API integration effectively can offer better price certainty, higher-margin ancillaries, and a more seamless experience for corporate and luxury travelers.
