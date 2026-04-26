# Creator Travel Research Exploratory Routes

This document captures sets of high-velocity research experiments and feature ideas for creator travel.
It is intentionally exploratory: these are not fully scoped products yet, but they are worthwhile routes to test and document.

## Why this matters

Creator travel is a multi-dimensional problem. The existing doc corpus covers foundational strategy, compliance, finance, and logistics.
This file focuses on the next layer: exploratory product/experience routes that can become future research projects or prototypes.

## Exploratory routes

### 1. Mobile-first creator operations

Research questions
- Can agency staff, creators, and local partners capture structured work entries from a phone with minimal friction?
- Can a mobile bot turn loose text, voice notes, and simple form entries into validated itinerary data, permit updates, production notes, or expense claims?
- What are the right micro-interactions for creators in the field who need to log content ideas, location notes, or quick approval requests?

Potential experiments
- phone-based creator logbook bot for on-site shoot status
- SMS/chat assistant for permit submission and local partner checklists
- offline entry capture that syncs to the agency back office when connectivity returns

### 2. Conversational approvals and chat-driven operations

Research questions
- Can the AI agent act as a conversation layer for approvals, task handoffs, and risk escalations?
- Can a creator or agency user ask the bot to "update the shoot permit for location X" and receive a guided workflow rather than a form?
- What guardrails are needed to keep conversational inputs compliant and auditable?

Potential experiments
- approval flows for creator budgets, local supplier hires, and event permits
- conversational permit and compliance checklist assistant for in-destination teams
- chat-based review of creator marketing copy, disclosure language, or sponsorship terms

### 3. Local partner enablement and supplier bot support

Research questions
- Can lightweight bots help local guides, vendors, and production crews onboard and report status without desktop systems?
- Can the bot translate supplier onboarding requirements into local-language instructions and checklist items?
- Can local partner updates be surfaced to the agency as structured events rather than free-form WhatsApp messages?

Potential experiments
- supplier onboarding bot for credential collection, paperwork validation, and community standards
- local partner task feed with simple accept/decline and status updates
- partner quality and compliance checks via mobile task prompts

### 4. Creator brief capture and ideation support

Research questions
- Can creators use a bot to capture content concepts, destination hooks, and marketing angles while they are on location?
- Can the AI automatically tag those ideas with travel product intent, compliance flags, and partner fit?
- How would this feed into itinerary design, booking proposals, and sponsor partnerships?

Potential experiments
- creator idea capture bot with prompt templates for destination stories, audience hooks, and sponsor alignment
- auto-generated creator brief summaries for agency approvals and supplier packaging
- sentiment and risk tagging of creator concept notes before they move into production

### 5. Field data, risk, and compliance sync

Research questions
- Can field crews and creators report health, safety, and permit status through a simple mobile experience?
- Can the bot automatically surface local advisory updates, visa/permit changes, weather/atmosphere/pollution/crime alerts, and flight status updates to the agency?
- What is the minimal structure needed to make field and external operational updates usable in booking, itinerary adaptation, and compliance workflows?

Potential experiments
- risk alert bot for local events, permit conditions, and health/safety issues
- content compliance reporter for sponsor disclosure, local filming restrictions, and cultural safety
- field update pipeline that converts mobile entries into operational tickets

### 6. AI-assisted entry validation and quality control

Research questions
- Can the bot check creator or partner submissions for completeness, compliance, and operational feasibility?
- Can it flag missing fields, likely contract issues, or supplier credential gaps before the item reaches the back office?
- How should the system balance automation with human review for risky creator travel decisions?

Potential experiments
- validation bot for creator briefs, insurance approvals, and permit filings
- auto-suggest corrections for incomplete expense entries, calendar clashes, or unsupported partner requests
- triage assistant that assigns low-risk approvals to AI and high-risk items to humans

### 7. PII and model risk research

Research questions
- Can the travel AI pipeline detect and classify PII before data enters the spine or LLM prompt bundle?
- Can we safely support synthetic/test dogfood data today while enforcing an automatic escalation path to encryption and compliance for real users?
- How do we compare hosted OpenAI/Anthropic models to OpenAI’s new open-source PII-safe model and other open-source/local alternatives for travel privacy and control?
- How do we keep the current specific open-source PII model investigation alongside broader evaluation of equivalent open-weight travel privacy/control models?
- What fine-tuning strategy is safe for travel tasks: synthetic only, de-identified batches, or prompt-layer adaptation?

Potential experiments
- PII detection layer for input capture and extraction pipelines
- privacy-safe prompt conventions for travel agent assistants
- external operational feed integration for weather, air quality, crime, pollution, flight status, and local advisories
- model provider risk comparison matrix: OpenAI hosted / OpenAI open-source PII-safe / open-source local / hybrid
- safe fine-tuning policy for travel tasks without using raw traveler PII

### 8. Booked-trip audit and verification research

Research questions
- Can the agency analyze self-booked itineraries, flight confirmations, tour packages, and visa documents to identify cost waste and compliance risk?
- What data extraction and verification checks are needed for booked flights, add-on tours, packages, and visa permit timelines?
- How should audit mode distinguish “already booked” versus “about to book” while still surfacing agency-led correction opportunities?
- Can the system surface real booking risks from flights, tours, visas, and packages without requiring travelers to log into the platform?

Potential experiments
- Audit mode for self-booked itineraries with flight/tour/package/visa extraction
- Booking risk checker that flags flight/visa/package mismatch, overpaying, or missing required documentation
- Document-driven recommendation engine that proposes better agency-sourced alternatives for already-booked trips
- “Already booked” status taxonomy that feeds analysis, escalation, and lead capture

## How to use this document

- Treat this as a living set of exploratory routes, not a finished feature list.
- Use it to seed research spikes, prototype briefs, and discovery interviews.
- Link new findings back to the existing creator roadmap, taxonomy matrix, and agency settings.
