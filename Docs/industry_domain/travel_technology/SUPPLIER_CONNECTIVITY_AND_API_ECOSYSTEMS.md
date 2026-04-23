# Supplier Connectivity and API Ecosystems

## Overview
This document explains how travel agencies connect to suppliers, content sources, and technology partners through APIs and integration platforms.

## Connectivity models
### Direct supplier APIs
- Airlines, hotels, and ground operators expose APIs for booking, pricing, and availability.
- Direct integration offers better control but requires more development and maintenance.

### Aggregator / marketplace APIs
- Platforms like Bed Banks, NDC aggregators, and API marketplaces consolidate supplier content.
- These can reduce integration overhead and simplify sourcing across multiple suppliers.

### Connectivity middleware
- Integration middleware transforms supplier data into normalized payloads for the agency's systems.
- It also handles retries, error normalization, and vendor-specific quirks.

## API ecosystem considerations
- **Authentication**: API keys, OAuth, and token refresh flows
- **Rate limits**: plan for throttling, caching, and graceful degradation
- **Data model mismatch**: map supplier schemas to the agency's product and pricing models
- **Error handling**: normalize supplier errors and extract actionable reasons for agents

## Operational best practices
- Build a supplier connectivity catalog documenting endpoints, request/response fields, and supported features
- Version APIs explicitly and support fallback strategies when suppliers change contracts
- Track supplier API health and latency to avoid operational disruptions
- Use API-based event triggers to keep availability, pricing, and booking status synchronized

## Why this matters
Strong supplier connectivity is the foundation for modern travel agency operations. It enables faster quoting, more reliable fulfillment, and the ability to scale product coverage without manual intervention.
