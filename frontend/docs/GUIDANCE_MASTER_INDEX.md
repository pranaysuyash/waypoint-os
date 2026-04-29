# User Guidance & Helper System — Master Index

> Comprehensive research on contextual help, guided tours, AI-powered assistance, and help content management for agents and customers.

---

## Series Overview

This series explores how Waypoint OS guides users through the platform — from contextual tooltips and smart hints to interactive guided tours and an AI-powered help assistant. Every user, regardless of experience level, should always know what to do next and how to do it.

**Target Audience:** Frontend engineers, UX designers, content strategists, product managers

**Key Constraint:** Indian travel agents have varying technical literacy — guidance must be simple enough for day-one agents while being dismissible for power users

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [GUIDANCE_01_CONTEXTUAL_HELP.md](GUIDANCE_01_CONTEXTUAL_HELP.md) | Tooltip engine, help panel, empty states, error guidance, smart hints |
| 2 | [GUIDANCE_02_GUIDED_TOURS.md](GUIDANCE_02_GUIDED_TOURS.md) | Tour framework, interactive walkthroughs, feature discovery, tour builder, analytics |
| 3 | [GUIDANCE_03_AI_ASSISTANT.md](GUIDANCE_03_AI_ASSISTANT.md) | AI help chat, proactive suggestions, knowledge retrieval, answer quality, continuous learning |
| 4 | [GUIDANCE_04_ACCESSIBILITY_HELP.md](GUIDANCE_04_ACCESSIBILITY_HELP.md) | Content authoring, multilingual support, WCAG compliance, content lifecycle, effectiveness metrics |

---

## Key Themes

### 1. Right Help, Right Place, Right Time
Help should appear where the user needs it, when they need it, and in the right amount. A tooltip for a quick reminder, a help panel for deeper questions, an AI assistant for complex queries. Never blocking, always dismissible.

### 2. Adaptive Guidance
Novice agents see detailed tooltips and proactive hints. Expert agents see minimal help with keyboard shortcut reminders only. The system adapts based on experience level, usage patterns, and explicit preferences.

### 3. AI-Powered But Grounded
The AI assistant can answer natural language questions and suggest next actions, but it's always grounded in verified documentation. Confidence levels are shown, and escalation to human support is always available.

### 4. Content as a Living System
Help articles, tutorials, and guides are not write-once documents. They have a lifecycle — authored, reviewed, published, monitored, and refreshed. Staleness detection and effectiveness analytics keep content relevant.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Workspace Customization (WORKSPACE_*) | Workspace onboarding tours and progressive disclosure |
| Agent Training (AGENT_TRAINING_*) | Training modules and certification system |
| Onboarding & First-Run (ONBOARDING_*) | First-time user guidance and setup wizards |
| AI Copilot (AI_COPILOT_*) | AI-powered feature assistance and auto-fill |
| Accessibility (A11Y_*) | Screen reader and keyboard help navigation |
| Knowledge Base (KNOWLEDGE_BASE_*) | Internal wiki and destination guides |
| Help Desk (HELP_DESK_*) | Customer support escalation from in-app help |
| Mobile Experience (MOBILE_*) | Mobile-friendly help and tour delivery |
| Offline Mode (OFFLINE_*) | Cached help content for offline access |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Tour Framework | react-joyride / custom | Guided tour rendering |
| Tooltip Engine | Floating UI / Tippy.js | Tooltip positioning and rendering |
| Help Panel | Custom slide-over | Contextual help panel |
| AI Assistant | Claude API / custom RAG | Natural language help |
| Content CMS | Headless CMS (Strapi/Contentful) | Help article management |
| Search | Typesense / Meilisearch | Help content full-text search |
| Analytics | PostHog / custom | Content effectiveness tracking |
| Localization | i18next / Lokalise | Multilingual content delivery |
| Media | Cloudinary | Screenshots and video hosting |

---

**Created:** 2026-04-28
