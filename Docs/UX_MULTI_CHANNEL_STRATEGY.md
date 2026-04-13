# Multi-Channel Communication Strategy

**Date**: 2026-04-13
**Purpose**: Document all communication channels, not just WhatsApp
**Related**: `UX_MESSAGE_TEMPLATES_AND_FLOWS.md`, `UX_DASHBOARDS_BY_PERSONA.md`

---

## The Multi-Channel Reality

Travel agencies don't just use WhatsApp. Real communication spans multiple channels:

| Channel | Best For | Frequency | Agency Sends | Customer Sends |
|---------|----------|-----------|--------------|----------------|
| **WhatsApp** | Quick questions, updates | Daily | Yes | Yes |
| **Email** | Proposals, PDFs, detailed itineraries | Per trip | Yes | Yes |
| **SMS** | Urgent alerts, confirmations | Critical moments | Yes | No |
| **Web Portal / Link** | Trip status, docs, payments | Ongoing | Yes | Yes |
| **Phone** | Complex discussions, emergencies | As needed | Yes | Yes |
| **Telegram** | Alternative to WhatsApp (some markets) | Varies | Yes | Yes |

**Key insight**: Customers should be able to interact via **any channel they prefer** and see the **same information**.

---

## Channel Use Cases by Stage

### Discovery Stage
```
Customer inquiry via: WhatsApp / Email / Web Form / Phone
         ↓
Agency response via: SAME CHANNEL (customer preference)
         ↓
Follow-ups via: WhatsApp OR Email (based on customer choice)
```

### Proposal Stage
```
Agency sends: Email with proposal PDF
           + WhatsApp message: "Check your email for options!"
           + Secure link to view proposal online
```

### Document Collection
```
Agency sends: WhatsApp message with link
         ↓
Customer clicks: Secure link to upload portal
         ↓
Customer uploads: Passport, visa documents
         ↓
Agency sees: Updated status in dashboard
```

### Booking Stage
```
Agency sends: Payment link (email + WhatsApp)
         ↓
Customer pays: Via link (card, UPI, bank transfer)
         ↓
Agency sends: SMS confirmation + Email receipt + WhatsApp acknowledgment
```

### Pre-Trip
```
Agency sends: Email with all documents
         + WhatsApp: "3 days to go! Documents in email 📧"
         + SMS: Flight reminder (day before)
```

### During Trip
```
Customer uses: Web portal / WhatsApp for support
Agency sends: Updates via preferred channel
Emergency: Phone call (immediate human response)
```

---

## The Secure Link / Portal Strategy

This is the piece I missed earlier. **A secure link is actually better than WhatsApp for many things.**

### What the Secure Link Does

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY OS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ [Generate Customer Link]                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  Generated: https://agency-os.com/trip/Sharma-Europe-2024-xK9m2p              │
│                                                                                  │
│  Send via: [WhatsApp] [Email] [SMS] [Copy Link]                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  CUSTOMER RECEIVES                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ WhatsApp from Agency:                                                     ││
│  │ "Hi Mrs. Sharma! I've prepared your Europe options.                       ││
│  │  View everything here: agency-os.com/trip/Sharma-Europe-2024-xK9m2p      ││
│  │  Let me know your thoughts!"                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  OR                                                                             │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ Email from Agency:                                                          ││
│  │ Subject: Your Europe Trip Options 🇨🇭                                       ││
│  │                                                                            ││
│  │ Hi Mrs. Sharma,                                                            ││
│  │                                                                            ││
│  │ Your options are ready! View them online:                                 ││
│  │ [BUTTON: View Your Trip Options]                                          ││
│  │                                                                            ││
│  │ Link: agency-os.com/trip/Sharma-Europe-2024-xK9m2p                        ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  CUSTOMER CLICKS LINK                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ YOUR TRIP TO EUROPE                                              [Agency Logo]││
│  │ ───────────────────────────────────────────────────────────────────────────││
│  │                                                                            ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ TRIP STATUS                                                            │  ││
│  │ │ Planning your options...                                              │  ││
│  │ │ └───────────────────────────────────────────────────────────────────┘  ││
│  │                                                                            ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ YOUR 3 OPTIONS                                                          │  ││
│  │ │                                                                        │  ││
│  │ │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  ││
│  │ │ │   BUDGET    │  │  RECOMMENDED │  │   LUXURY    │                    │  ││
│  │ │ │  ₹5.2L      │  │   ₹6.8L     │  │   ₹9.5L     │                    │  ││
│  │ │ │             │  │      ⭐     │  │             │                    │  ││
│  │ │ │ Interlaken  │  │  Lucerne    │  │  Zermatt    │                    │  ││
│  │ │ │             │  │             │  │             │                    │  ││
│  │ │ │ [View       │  │ [View       │  │ [View       │                    │  ││
│  │ │  Details]    │  │  Details]    │  │  Details]    │                    │  ││
│  │ │ └─────────────┘  └─────────────┘  └─────────────┘                    │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                            ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ NEED CLARIFICATION?                                                     │  ││
│  │ │ Have questions? Reply directly:                                        │  ││
│  │ │                                                                        │  ││
│  │ │ [WhatsApp Us] [Email Us] [Call Us]                                    │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                            ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ DOCUMENTS NEEDED                                                        │  ││
│  │ │ To proceed with booking, please upload:                                │  ││
│  │ │                                                                        │  ││
│  │ │ ☐ Passport copies for all travelers                                    │  ││
│  │ │ ☐ Visa documents (if required)                                         │  ││
│  │ │                                                                        │  ││
│  │ │ [Upload Documents]                                                     │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                            ││
│  │ [I'm Interested in Option 2]  [I have questions]                           ││
│  │                                                                            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  © 2024 Agency OS • Powered by [Your Agency Name]                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Secure Links Are Better Than WhatsApp for Many Things

| Use Case | WhatsApp | Secure Link | Winner |
|----------|-----------|--------------|--------|
| **Send 3 proposals** | Long message, hard to read | Clean UI, compare side-by-side | Link |
| **Upload documents** | Send one by one, quality issues | Bulk upload, auto-resize | Link |
| **Make payment** | External link anyway | Integrated payment flow | Link |
| **Track trip status** | Scroll through chat | Dashboard with progress bars | Link |
| **Share itinerary** | Forward individual messages | Always-current web page | Link |
| **Quick question** | Instant, familiar | Requires login/open link | WhatsApp |
| **Emergency** | Call button anyway | Phone number prominent | Phone |
| **Group coordination** | Forward messages, confusion | Shared portal, everyone sees same | Link |

### The Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  BEST PRACTICE: Combine channels                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. WhatsApp: "Your options are ready!                                         │
│                agency-os.com/trip/Sharma-Europe-2024-xK9m2p                    │
│                Let me know what you think!"                                     │
│                                                                                  │
│  2. Email: Same message + full proposal PDF attached                            │
│                                                                                  │
│  3. Customer clicks link → Views options → Asks questions                       │
│                                                                                  │
│  4. Customer responds via WhatsApp: "Option 2 looks good, but                 │
│                                         is the hotel accessible for elderly?"      │
│                                                                                  │
│  5. Agent responds on WhatsApp: "Yes! Hotel has lifts and                    │
│                                      ground floor rooms. Added to your quote."   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Customer Portal Features

### What the Customer Sees

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MY TRIPS                                                            [Profile] │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  UPCOMING                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🇨🇭 Europe Trip                                     Status: Planning       ││
│  │    Jun 15-25, 2025                              5 people                 ││
│  │                                                                            ││
│  │ [View Options] [Upload Documents] [Chat with Agent]                        ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  PAST TRIPS                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🇸🇬 Singapore Trip                                  Completed Mar 2024    ││
│  │    View Documents | Write Review | Book Again                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Trip Detail Page

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to My Triips                                                             │
│                                                                                  │
│  EUROPE TRIP                                                    [Share] [Print]│
│  ───────────────────────────────────────────────────────────────────────────────│
│  Jun 15-25, 2025 • 5 people • Planning                                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ TRIP STATUS                                                                  ││
│  │ ████████████████░░░░░░░░░░  60% Complete                                   ││
│  │                                                                            ││
│  │ ✓ Options reviewed                                                         ││
│  │ ✓ Destination confirmed: Switzerland                                        ││
│  │ ⏳ Awaiting document uploads                                                ││
│  │ ⏳ Payment pending                                                          ││
│  │ ☐ Booking confirmation                                                      ││
│  │ ☐ Pre-trip documents                                                        ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ SELECTED OPTION                                                              ││
│  │                                                                            ││
│  │ 🥈 RECOMMENDED: Lucerne, Switzerland                                       ││
│  │ • Hotel: Palace Luzern (4-star, lifts accessible)                          ││
│  │ • Activities: Mount Titlis, Lake Cruise, Old Town Tour                    ││
│  │ • Includes: Flights, breakfast, Swiss Travel Pass, insurance              ││
│  │ • Total: ₹6.8L                                                             ││
│  │                                                                            ││
│  │ [View Detailed Itinerary] [Download PDF]                                   ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ DOCUMENTS                                                                   ││
│  │                                                                            ││
│  │ Upload required documents:                                                 ││
│  │                                                                            ││
│  │ ☐✓ Mrs. Sharma - Passport uploaded (Feb 15)                               ││
│  │ ☐  Mr. Sharma - Passport uploaded (Feb 15)                                ││
│  │ ☐  Child 1 - Passport uploaded (Feb 16)                                   ││
│  │ ☐  Child 2 - Pending                                                       ││
│  │ ☐  Grandmother - Pending                                                   ││
│  │                                                                            ││
│  │ [Upload Document] [Reminder All]                                           ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ PAYMENT                                                                     ││
│  │                                                                            ││
│  │ Amount Due: ₹34,000 (50% to confirm booking)                               ││
│  │ Due Date: March 1, 2025                                                    ││
│  │                                                                            ││
│  │ [Pay Now] [View Payment Schedule]                                          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ CHAT WITH AGENT                                                             ││
│  │                                                                            ││
│  │ Have questions? Your agent Priya typically responds in under 2 hours.      ││
│  │                                                                            ││
│  │ [WhatsApp Us] [Email Us] [Call: +91-98765-43210]                          ││
│  │                                                                            ││
│  │ Recent messages:                                                            ││
│  │ You (2 hrs ago): Does the hotel have lifts? My mother has mobility...      ││
│  │ Priya (1 hr ago): Yes! Palace Luzern has elevators and ground floor...     ││
│  │                                                                            ││
│  │ [View Full Chat] [Send Message]                                             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Channel Preference Matrix

### By Customer Type

| Customer Type | Preferred Channel | Backup Channel | Why |
|---------------|-------------------|----------------|-----|
| **Young professional (28-35)** | WhatsApp | Email | Always on phone, quick responses |
| **Family coordinator (35-50)** | WhatsApp + Portal | Phone | Coordinating multiple people, needs visibility |
| **Elderly traveler (60+)** | Phone | Email | Personal touch, not tech-savvy |
| **Corporate traveler** | Email + Portal | SMS | Professional, paper trail |
| **First-time traveler** | Phone + WhatsApp | Portal | Reassurance, hand-holding |

### By Communication Type

| Communication Type | Best Channel | Why |
|-------------------|--------------|-----|
| **Initial inquiry** | Any (customer's choice) | Meet them where they are |
| **Proposals** | Portal + Email | Visual, comparable, saveable |
| **Clarification questions** | WhatsApp | Quick, conversational |
| **Document requests** | Portal link | Organized, bulk upload |
| **Payment links** | Portal + WhatsApp + SMS | Redundancy = conversion |
| **Urgent updates** | WhatsApp + SMS | Immediate attention |
| **Detailed itineraries** | Email + Portal | PDF for offline, portal for live |
| **Trip reminders** | WhatsApp + SMS | Hard to miss |
| **Emergency support** | Phone | Human, immediate |
| **Post-trip feedback** | Email + Portal | Thoughtful, not intrusive |

---

## Technical Implementation: Secure Links

### Link Generation

```python
# src/services/link_service.py

import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel

class TripLink(BaseModel):
    link_id: str
    url: str
    trip_name: str
    expires_at: datetime
    access_count: int = 0
    max_access: int = 100

async def generate_trip_link(
    packet_id: str,
    customer_phone: str,
    trip_name: str,
    valid_for_days: int = 30
) -> TripLink:
    """
    Generate a secure link for customer to view their trip details
    """
    # Generate unique link ID
    link_id = secrets.token_urlsafe(16)

    # Calculate expiration
    expires_at = datetime.now() + timedelta(days=valid_for_days)

    # Store in database
    await db.execute(
        """INSERT INTO trip_links
           (link_id, packet_id, customer_phone, trip_name, expires_at, created_at)
           VALUES ($1, $2, $3, $4, $5, NOW())""",
        link_id, packet_id, customer_phone, trip_name, expires_at
    )

    # Generate URL
    base_url = os.getenv("PUBLIC_URL", "https://agency-os.com")
    url = f"{base_url}/trip/{link_id}"

    return TripLink(
        link_id=link_id,
        url=url,
        trip_name=trip_name,
        expires_at=expires_at
    )

async def validate_trip_link(link_id: str) -> dict | None:
    """
    Validate link and return trip details
    Returns None if link is invalid or expired
    """
    link_data = await db.fetch_one(
        """SELECT * FROM trip_links
           WHERE link_id = $1
           AND expires_at > NOW()
           AND access_count < max_access""",
        link_id
    )

    if not link_data:
        return None

    # Increment access count
    await db.execute(
        """UPDATE trip_links
           SET access_count = access_count + 1,
               last_accessed = NOW()
           WHERE link_id = $1""",
        link_id
    )

    # Get trip details
    trip_data = await db.fetch_one(
        """SELECT p.*, c.name as customer_name
           FROM packets p
           LEFT JOIN customers c ON c.phone = p.customer_phone
           WHERE p.packet_id = $1""",
        link_data["packet_id"]
    )

    return {
        "link": link_data,
        "trip": trip_data
    )
```

### Customer Portal API

```python
# src/api/customer_portal.py

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/portal", tags=["customer"])

@router.get("/trip/{link_id}")
async def get_trip_portal(link_id: str):
    """
    Public endpoint for customer portal
    Validates link and returns trip details
    """
    data = await validate_trip_link(link_id)

    if not data:
        raise HTTPException(status_code=404, detail="Invalid or expired link")

    trip = data["trip"]

    # Get options if available
    options = await get_trip_options(trip["packet_id"])

    # Get document status
    documents = await get_document_status(trip["packet_id"])

    # Get payment status
    payments = await get_payment_status(trip["packet_id"])

    # Get recent messages
    messages = await get_recent_messages(trip["customer_phone"], trip["packet_id"])

    return {
        "trip": {
            "name": trip["trip_name"] or "Your Trip",
            "destination": trip["destination"],
            "dates": trip["dates"],
            "people": trip["party_size"],
            "status": calculate_trip_status(trip)
        },
        "options": options,
        "documents": documents,
        "payments": payments,
        "messages": messages,
        "agent": {
            "name": trip["agent_name"],
            "phone": trip["agent_phone"],
            "response_time": "Usually within 2 hours"
        }
    }

@router.post("/trip/{link_id}/document")
async def upload_document(
    link_id: str,
    document_type: str,
    file: UploadFile
):
    """
    Customer uploads document via portal
    """
    # Validate link
    data = await validate_trip_link(link_id)
    if not data:
        raise HTTPException(status_code=404, detail="Invalid link")

    # Save file
    file_path = await save_document(
        file=file,
        customer_phone=data["trip"]["customer_phone"],
        packet_id=data["trip"]["packet_id"],
        document_type=document_type
    )

    # Update document status
    await update_document_status(
        packet_id=data["trip"]["packet_id"],
        document_type=document_type,
        status="uploaded"
    )

    # Notify agent
    await notify_agent_document_uploaded(
        packet_id=data["trip"]["packet_id"],
        document_type=document_type
    )

    return {"status": "uploaded", "file_path": file_path}

@router.post("/trip/{link_id}/message")
async def send_message_to_agent(link_id: str, message: str):
    """
    Customer sends message via portal
    Routes to agent's WhatsApp/Email
    """
    data = await validate_trip_link(link_id)
    if not data:
        raise HTTPException(status_code=404, detail="Invalid link")

    # Store message
    await store_message(
        customer_phone=data["trip"]["customer_phone"],
        packet_id=data["trip"]["packet_id"],
        content=message,
        role="customer",
        channel="portal"
    )

    # Notify agent
    await notify_agent_new_message(
        agent_id=data["trip"]["agent_id"],
        customer_phone=data["trip"]["customer_phone"],
        message=message
    )

    return {"status": "sent"}

@router.post("/trip/{link_id}/select-option")
async def select_option(link_id: str, option_id: str):
    """
    Customer selects an option from proposal
    """
    data = await validate_trip_link(link_id)
    if not data:
        raise HTTPException(status_code=404, detail="Invalid link")

    # Update selection
    await update_selected_option(
        packet_id=data["trip"]["packet_id"],
        option_id=option_id
    )

    # Notify agent
    await notify_agent_option_selected(
        agent_id=data["trip"]["agent_id"],
        packet_id=data["trip"]["packet_id"],
        option_id=option_id
    )

    # Generate payment link if not exists
    payment_link = await generate_payment_link(
        packet_id=data["trip"]["packet_id"],
        option_id=option_id
    )

    return {
        "status": "selected",
        "payment_link": payment_link,
        "message": "Great choice! Proceed to payment to confirm your booking."
    }
```

### Frontend: Customer Portal

```typescript
// pages/customer-portal/TripPage.tsx

interface TripPortalProps {
  linkId: string;
}

export function TripPortal({ linkId }: TripPortalProps) {
  const { data, loading, error } = useSWR(
    `/api/portal/trip/${linkId}`
  );

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorPage message="Invalid or expired link" />;

  const { trip, options, documents, payments, messages, agent } = data;

  return (
    <div className="customer-portal">
      <Header trip={trip} />

      <div className="portal-grid">
        <div className="main-content">
          <TripStatus trip={trip} />
          <OptionsSection options={options} linkId={linkId} />
          <DocumentsSection documents={documents} linkId={linkId} />
          <PaymentSection payments={payments} linkId={linkId} />
        </div>

        <div className="sidebar">
          <AgentCard agent={agent} />
          <MessagesWidget messages={messages} linkId={linkId} />
        </div>
      </div>
    </div>
  );
}

// Components/OptionsSection.tsx
function OptionsSection({ options, linkId }: Props) {
  const [selected, setSelected] = useState(null);

  const handleSelect = async (optionId: string) => {
    const response = await fetch(`/api/portal/trip/${linkId}/select-option`, {
      method: 'POST',
      body: JSON.stringify({ option_id: optionId })
    });

    const result = await response.json();

    if (result.payment_link) {
      // Show payment modal
      showPaymentModal(result);
    }

    setSelected(optionId);
  };

  return (
    <section className="options-section">
      <h2>Your Options</h2>

      <div className="options-grid">
        {options.map((option) => (
          <OptionCard
            key={option.id}
            option={option}
            selected={selected === option.id}
            onSelect={() => handleSelect(option.id)}
          />
        ))}
      </div>
    </section>
  );
}
```

---

## Channel Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY OS                                                                    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                           ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       ││
│  │  │   WhatsApp  │  │    Email    │  │     SMS     │  │   Portal    │       ││
│  │  │   Service   │  │   Service   │  │   Service   │  │     API     │       ││
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       ││
│  │         │                │                │                │              ││
│  │         └────────────────┴────────────────┴────────────────┘              ││
│  │                            │                                           ││
│  │                            ↓                                           ││
│  │         ┌─────────────────────────────────────┐                         ││
│  │         │      Unified Message Service         │                         ││
│  │         │  (Normalizes all channels to one     │                         ││
│  │         │   conversation thread per customer)  │                         ││
│  │         └─────────────────────────────────────┘                         ││
│  │                            │                                           ││
│  │                            ↓                                           ││
│  │         ┌─────────────────────────────────────┐                         ││
│  │         │         Customer Profile              │                         ││
│  │         │  • Channel preferences               │                         ││
│  │         │  • Conversation history (all channels)│                         ││
│  │         │  • Document status                    │                         ││
│  │         │  • Payment status                     │                         ││
│  │         └─────────────────────────────────────┘                         ││
│  │                                                                           ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Message Routing Logic

```python
# src/services/routing_service.py

class ChannelPreference(BaseModel):
    customer_phone: str
    preferred_channel: str  # "whatsapp", "email", "sms", "portal"
    backup_channel: str
    whatsapp_opt_in: bool = False

async def send_message(
    customer_phone: str,
    message: str,
    message_type: str,  # "proposal", "document_request", "payment", "update", "emergency"
    packet_id: str
):
    """
    Send message via customer's preferred channel
    """

    # Get customer preferences
    prefs = await get_channel_preferences(customer_phone)

    # Route based on message type
    if message_type == "proposal":
        # Proposals always go to portal + email + WhatsApp notification
        await send_proposal_multichannel(
            customer_phone=customer_phone,
            message=message,
            packet_id=packet_id
        )

    elif message_type == "document_request":
        # Send portal link via preferred channel
        link = await generate_document_upload_link(packet_id)
        await send_via_channel(
            channel=prefs.preferred_channel,
            customer_phone=customer_phone,
            message=f"{message}\n\nUpload here: {link}"
        )

    elif message_type == "payment":
        # Send payment link via all channels (redundancy = conversion)
        payment_link = await generate_payment_link(packet_id)
        await send_via_all_channels(
            customer_phone=customer_phone,
            message=f"Payment link: {payment_link}"
        )

    elif message_type == "emergency":
        # Phone call + SMS + WhatsApp
        await send_emergency_alert(
            customer_phone=customer_phone,
            message=message
        )

    else:  # general update
        # Use preferred channel
        await send_via_channel(
            channel=prefs.preferred_channel,
            customer_phone=customer_phone,
            message=message
        )

async def send_proposal_multichannel(
    customer_phone: str,
    message: str,
    packet_id: str
):
    """
    Proposals go everywhere for maximum visibility
    """
    link = await generate_trip_link(packet_id, customer_phone)

    # WhatsApp: notification with link
    if whatsapp_opt_in:
        await send_whatsapp(
            customer_phone,
            f"Your options are ready! View here: {link}"
        )

    # Email: full message + link
    await send_email(
        customer_phone,
        subject="Your Trip Options",
        body=f"{message}\n\nView online: {link}",
        include_pdf=True
    )

    # SMS: brief notification
    await send_sms(
        customer_phone,
        f"Your trip options are ready! Check email or visit: {link}"
    )
```

---

## SMS Integration

### When to Use SMS

| Use Case | Why SMS? |
|----------|----------|
| **Payment confirmations** | Hard to miss, immediate |
| **Flight reminders** | Day-before, critical timing |
| **Portal notifications** | "Your documents are ready" |
| **Urgent updates** | Flight delays, cancellations |
| **OTP verification** | Secure access to portal |

### SMS Implementation

```python
# src/services/sms_service.py

import httpx

SMS_API_KEY = os.getenv("SMS_API_KEY")  # Twilio, MSG91, etc.

async def send_sms(phone: str, message: str):
    """
    Send SMS via provider (Twilio, MSG91, etc.)
    """
    # Clean phone number
    clean_phone = re.sub(r'[^\d+]', '', phone)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sms-provider.com/sms",
            headers={"Authorization": f"Bearer {SMS_API_KEY}"},
            json={
                "to": clean_phone,
                "message": message,
                "sender": "AGENCYO"  # 6-character sender ID
            }
        )

    return response.json()
```

---

## Email Integration

### Email Templates

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Subject: Your Europe Trip Options 🇨🇭                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Hi Mrs. Sharma,                                                                │
│                                                                                  │
│  Great news! Your Europe trip options are ready.                                  │
│                                                                                  │
│  Based on our discussion, I've prepared 3 options for Switzerland in June.       │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🔗 VIEW YOUR OPTIONS ONLINE                                                ││
│  │                                                                            ││
│  │ You can view, compare, and select your option online:                      ││
│  │                                                                            ││
│  │ [BUTTON: View Your Trip Options]                                           ││
│  │                                                                            ││
│  │ Or visit: agency-os.com/trip/Sharma-Europe-2024-xK9m2p                      ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  QUICK SUMMARY:                                                                  │
│  • Option 1 (₹5.2L): Interlaken - Budget-friendly                               │
│  • Option 2 (₹6.8L): Lucerne - RECOMMENDED ⭐                                  │
│  • Option 3 (₹9.5L): Zermatt - Luxury experience                               │
│                                                                                  │
│  All options include: flights, breakfast, Swiss Travel Pass, travel insurance   │
│                                                                                  │
│  Need more details? Click the link above to see full itineraries, hotels, and   │
│  activities.                                                                    │
│                                                                                  │
│  Questions? Reply to this email or message me on WhatsApp.                      │
│                                                                                  │
│  Best regards,                                                                   │
│  Priya                                                                           │
│  +91-98765-43210                                                                 │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────││
│  PDF version attached                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: The Multi-Channel Strategy

### Key Points

1. **Secure links are primary** - Portal is better for proposals, documents, payments
2. **WhatsApp is for conversation** - Quick questions, updates, human connection
3. **Email is for record** - PDFs, detailed itineraries, paper trail
4. **SMS is for urgency** - Things that must be seen immediately
5. **Phone is for complex situations** - Especially for older customers or emergencies

### The Golden Rule

**Don't force customers to use one channel.** Let them:

- Start inquiry via WhatsApp, email, or web form
- View proposals on portal (clean UI)
- Ask questions via WhatsApp (quick)
- Upload documents via portal link (organized)
- Pay via link from any channel
- Get updates via their preferred channel

### Technical Implication

Build the **portal first**, not WhatsApp integration. The portal is where:
- Proposals are viewed
- Documents are uploaded
- Payments happen
- Trip status is tracked

WhatsApp (and other channels) are **notification systems** that drive people to the portal.

---

## Related Documentation

- `UX_MESSAGE_TEMPLATES_AND_FLOWS.md` - Message content for all channels
- `UX_DASHBOARDS_BY_PERSONA.md` - Agent dashboard for managing multi-channel
- `UX_TECHNICAL_ARCHITECTURE.md` - Overall technical implementation

---

*Think "omnichannel" not "WhatsApp-only". The portal is the hub, messaging apps are the spokes.*
