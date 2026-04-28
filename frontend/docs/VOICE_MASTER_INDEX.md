# Voice & Conversational AI — Master Index

> Exploration of voice platform architecture, speech processing, voice-driven booking, and AI-powered call assistance.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Platform Architecture](VOICE_01_ARCHITECTURE.md) | Telephony integration, IVR design, call routing, voice analytics |
| 02 | [Speech Processing & NLU](VOICE_02_SPEECH.md) | Speech-to-text, intent mapping, multi-language, code-switching |
| 03 | [Voice-Driven Booking](VOICE_03_BOOKING.md) | Voice booking flow, slot filling, trip comparison, payment authorization |
| 04 | [Agent Assist & Call Intelligence](VOICE_04_AGENT_ASSIST.md) | Real-time transcription, agent prompts, call analytics, coaching |

---

## Key Themes

- **Voice is the primary channel** — Indian customers prefer calling over filling forms. A robust voice platform isn't optional — it's the main customer interaction channel.
- **AI assists, doesn't replace** — The agent remains the human in the loop. AI provides real-time prompts, knowledge, and transcription. The agent makes the sale and builds the relationship.
- **WhatsApp complements voice** — Voice calls are synchronous and personal; WhatsApp is async and convenient. Every voice interaction should be supplemented with WhatsApp follow-up.
- **Compliance is built-in** — Call recording disclosure, payment security (PCI-DSS), DND compliance, and data localization are non-negotiable. The platform handles compliance automatically.
- **Coaching through data** — Every call is a training opportunity. AI-powered call scoring and coaching insights help agents improve continuously without formal training sessions.

## Integration Points

- **Communication Hub** — Voice calls alongside WhatsApp, email, and SMS
- **Trip Builder** — Voice-driven trip search and booking creation in Workbench
- **Knowledge Base** — Real-time knowledge surfacing during calls
- **Payment Processing** — Secure payment links sent during voice calls
- **Analytics & BI** — Call metrics, conversion rates, and agent performance
- **Agent Training** — Call coaching insights feed into training modules
- **Customer CRM** — Call history and transcripts linked to customer profiles
