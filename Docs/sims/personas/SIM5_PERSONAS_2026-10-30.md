# Sim #5 Personas — Tier-2 Indian Agent & Regional Travel Ecosystem

**Project:** Waypoint OS (travel_agency_agent) — Sim #5 Suite  
**Date:** 2026-10-30  
**Context:** Indian Tier-2 travel agency dynamics, vernacular/Hinglish intake, joint family structures, GST/TCS regulatory workflows, and WhatsApp-first client communications.

---

## Suite Map

| Sim | Lens / Door | Primary Persona | Client Persona | Surfaces Under Test |
|---|---|---|---|---|
| **5-A** | **Tier-2 Outbound Multi-Gen Family Inquiry** | Rajesh Khandelwal (42, Indore Agency Owner) | Sunil Agrawal (Indore, Agrawal Textiles) | `/api/triage/message` (Hinglish sub-second triage, urgency, emotional tone, work intake classification), `/api/v1/messaging/webhook/whatsapp`, `/api/drafts`, `/run` (party: 6 adults, 2 kids, 1 infant; origin: IDR; destination: DXB; budget: ₹4.5 lakh; constraints: wheelchair, Jain pure-veg, GST invoice) |
| **5-B** | **WhatsApp Preference Refinement & Tax Clarification** | Rajesh Khandelwal | Sunil Agrawal | Inbound follow-up note supersession, location preference (Downtown/SZR vs Deira), Indian Tax Compliance (TCS under Sec 206C(1G) threshold evaluation: 5% vs 20%), passport validity horizon |
| **5-C** | **Omnichannel Dispatch & Non-Repudiation Audit** | Rajesh Khandelwal | Sunil Agrawal | `/api/v1/messaging/send` (WhatsApp dispatch, honest provider status `NOT_CONFIGURED` without credentials), `/api/v1/messages` read model, `AuditStore` event sequencing & chain hash integrity |

---

## Persona 1: Rajesh Khandelwal (Operator Seat)

- **ID**: `P-TIER2-INDIA-01`
- **Role**: Founder & Managing Director, Shubh Yatra Holidays, Saket, Indore, Madhya Pradesh.
- **Full Dossier**: [`PERSONA_TIER2_AGENT_RAJESH_KHANDELWAL.md`](file:///Users/pranay/Projects/travel_agency_agent/Docs/personas/PERSONA_TIER2_AGENT_RAJESH_KHANDELWAL.md)
- **Operational Reality**: High-volume, relationship-driven boutique operator in Central India. Needs instant message triage, multi-generational family constraint tracking, strict dietary safeguards (Jain veg), GST/TCS compliance, and rapid WhatsApp follow-ups.

---

## Client Persona: Sunil Agrawal (Customer)

- **Profile**: Managing Director, Agrawal Textiles, Sitlamata Bazar, Indore. Traveling with his extended family (wife, 2 children, parents, brother & sister-in-law, infant nephew).
- **Communication Channel**: WhatsApp Business (unstructured Hinglish text & voice note transcripts).
- **Non-Negotiables**:
  1. Wheelchair assistance for his mother (72 yrs) with knee arthritis.
  2. Pure vegetarian / Jain dining (no onion, no garlic, no root vegetables).
  3. B2B GST tax invoice in the name of Agrawal Textiles (Indore, MP).
  4. All-in budget of ₹4,50,000 INR (4.5 Lakhs).

---

## Verbatim Inquiries (Honest-Input Convention)

### Voice 5-A1 (Inbound WhatsApp Inquiry):
> "Bhaiya namaste. Hum 6 bade hain aur 2 bacche (ek 8 saal aur ek 3 saal) plus ek 7 mahine ka infant. Hume December 22 se 28 tak Dubai ka family trip karna hai Indore se. Mummy ji (age 72) ko chalne me dikkat hai to airport aur sightseeing pe wheelchair assistance compulsory chahiye. Khana pure vegetarian/Jain chahiye hotel aur sightseeing me. Budget around 4.5 lakh total sab milakar. Aur humare textile firm ke naam par GST invoice banwana hai. Jaldi batao options."

### Voice 5-A2 (Follow-up Refinement):
> "Sunil Agrawal here again — bhaiya hotel Bur Dubai ya Deira taraf nahi chahiye, kids ko Burj Khalifa aur Dubai Mall paas chahiye so Downtown ya Sheikh Zayed Road taraf batao. Aur kya TCS 5% lagega ya 20%? Sabke passport valid hain till 2028."

### Voice 5-A3 (Outbound Operator Reply to Client):
> "Namaste Sunil ji! Thank you for contacting Shubh Yatra Holidays. We have registered your Dubai family trip (Dec 22-28, 6 adults, 2 kids, 1 infant from Indore). We have noted 100% pure Jain meals, airport & sightseeing wheelchair assistance for Mataji, and Downtown/SZR hotel preference. Since the package is ₹4,50,000 (under ₹7 Lakhs), TCS is 5% which is fully adjustable against your advance tax. GST invoice with your company GSTIN will be provided. Your customized proposal is being prepared now."
