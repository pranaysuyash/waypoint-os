# Creator Travel Agency Settings and AI Support Controls

This document captures agency-level configuration ideas for creator travel products, including settings that sit on top of a business plan and the controls that govern AI agent support for agency users.

## Why agency settings belong above the plan

A travel plan defines the product strategy and the creator value proposition.
Agency settings define how a specific agency executes that plan.

Each agency should be able to keep its own:

- portfolio and brand positioning
- technology/autonomy tolerance
- support model for human agents and AI agents
- pricing and margin rules
- partner/supplier permissions
- compliance and audit controls

This is especially important in creator travel because one agency may sell creator-led packaged experiences while another is focused on creator-affiliated B2B sourcing, even if both use the same underlying creator product plan.

## Core agency settings categories

### 1. Plan baseline vs agency overrides

The plan is the shared product architecture:

- creator market segmentation
- travel experience types
- distribution channels
- creative and content GTM strategy

Agency settings are the execution layer:

- chosen service tiers and agent support levels
- supplier pools and credentialing thresholds
- permissible AI autonomy band
- client segment eligibility
- local currency, tax, and settlement rules

In other words: the plan says "what" the agency offers; agency settings say "how" it is delivered.

### 2. Agency profile and operational controls

Suggested settings:

- agency identity: brand, region, legal entity, service scope
- service package definitions: premium creator concierge, marketplace-only, co-marketing bundles
- support channels enabled: phone, chat, email, app, creator desk
- agency SLA tiers: standard, expedited, VIP, self-service
- allowed fulfillment paths: agency-owned suppliers, partner marketplaces, third-party sourcing

### 3. AI support model and human support controls

This is the key control the user named.
Every agency should decide whether AI support is:

- disabled
- read-only recommendation mode
- assisted support for human agents
- supervised assistance with approval gates
- autonomous for low-risk tasks
- fully enabled for internal support agents only

Additional agency-level options:

- which user roles can call the AI agent
- whether external agency partners receive AI support
- whether the AI agent can interact with suppliers or only with internal agents
- whether AI support is gated by tier or customer segment
- whether the agency provides an "AI concierge" versus a standard human concierge

### 4. Autonomy and risk boundaries

Agency settings should also include AI decision controls:

- spend thresholds for autonomous recovery or disruption handling
- risk categories that require human escalation
- policy exceptions for creator emergencies and production logistics
- allowed content/marketing advice versus forbidden guidance
- override rules for agency owners and compliance officers

Example controls:

- `AI_CAN_BOOK_AUTONOMOUSLY_UP_TO = $X`
- `AI_CAN_RECOMMEND_CO_PARTNERS_WITHOUT_APPROVAL = true/false`
- `AI_MUST_ESCALATE_IF_DESTINATION_RISK >= HIGH`
- `AI_SUPPORT_FOR_CREATOR_ONBOARDING = enabled | limited | disabled`

### 5. Partner, supplier, and creator governance

For creator travel, agency settings should cover partner workflows too:

- which supplier types are allowed for creator deals
- whether creators can tap approved local guides and production partners
- whether the AI agent can surface partner offers directly
- partner onboarding and credentialing policies
- brand co-marketing permission levels

### 6. Support and training controls

Agency settings should support the actual human users of the system:

- whether the AI assistant is available to Junior Agents, Senior Agents, or only Ops leads
- whether AI-generated advice is visible to agency clients or withheld for internal use
- whether the bot is accessible on mobile, chat, SMS, or voice interfaces for field teams and creators
- whether mobile/phone entry workflows are supported for quick on-location updates, permits, and creator notes
- the training profile of the AI model (e.g., creator travel, compliance, finance)
- whether AI support is part of the service contract or a premium add-on

### 7. Compliance, audit, and explainability controls

Important controls for later research and documentation:

- audit logging of AI decisions and handoffs
- explainability requirements per decision type
- consent controls when the AI agent handles creator content or traveler data
- regulatory filters for local creator marketing, sponsorship disclosure, and labor compliance
- retention and review policies for AI conversation history

## Research ideas for later documentation

These are the kinds of ideas that should be captured and checked later:

- Should each agency have a default AI support mode and a set of switchable support profiles?
- Should agency users be able to exclude the AI agent from certain bookings or creator campaigns?
- What controls should exist for creator-facing content recommendations versus travel compliance recommendations?
- How do agency settings differ for a creator travel agency versus a general travel agency with a creator vertical?
- Should there be a separate "AI support contract" for agencies that purchase AI-assisted workflows?
- What monitoring and recovery controls are needed when AI support is enabled for live creator production logistics?
- Which agency roles should be able to update or override AI settings?
- What safeguards should be applied when an AI agent learns from past bookings and creator outcomes?

## Recommended next step

Capture these settings in a dedicated configuration taxonomy document for creator travel agencies.
This should include:

- agency profile and strategy controls
- AI support levels and role-based access
- autonomy boundaries and risk thresholds
- partner/supplier governance flags
- compliance and audit requirements

That document will help turn these future research ideas into a concrete checklist for product design, implementation, and governance.
