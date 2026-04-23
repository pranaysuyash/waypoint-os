# S1-S3: Trip Emergency

**Persona**: Individual Traveler
**Scenario**: A customer calls with an emergency during travel and expects the agency to respond immediately and resolve it.

---

## Situation

A customer is currently on a trip and contacts the agency with an urgent problem.
This is a high-stress situation where the agency must respond quickly and correctly.

### Customer message
> "We are in Phuket and the hotel has no hot water. The kids are freezing and the manager says it will take 8 hours. Can you fix this now?"

### Customer state
- Frustrated and stressed
- Traveling with kids
- Already paid for the trip
- Expects the agency to intervene immediately

## What the system should do

1. **Escalate immediately**
   - Recognize "emergency" and "now"
   - Route the request to the emergency handling workflow

2. **Fetch current booking details**
   - Confirm hotel, dates, room type, and contact information
   - Check if the issue is covered by supplier agreement or service warranty

3. **Offer resolution options**
   - Move to a different room or hotel
   - Demand compensation or refund credit
   - Request immediate maintenance escalation

4. **Communicate clearly**
   - Send a calm customer-facing response:
     > "I’m on it. I’m contacting the hotel manager now and will update you within 15 minutes."
   - Keep the customer informed until resolved

## Required system behaviors

- Emergency detection from customer message
- Access to live booking and supplier details
- Prioritization of urgent issues
- Clear status updates for the customer
- Ability to recommend immediate remediation

## Why this matters

Emergencies are the highest-value touchpoints for a travel agency.
How the agency performs here determines customer trust and loyalty.

## Success criteria

- The system flags the case as emergency immediately.
- The agent has the necessary booking context instantly.
- The agent can choose an appropriate resolution path.
- The customer receives a fast, reassuring response.
- The issue is tracked to closure without confusion.
