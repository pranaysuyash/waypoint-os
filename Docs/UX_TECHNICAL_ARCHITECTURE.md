# UX Technical Architecture: From Notebooks to UI

**Date**: 2026-04-13
**Purpose**: Define how NB01-NB03 connect to a future web/mobile UI
**Related**: `UX_AND_USER_EXPERIENCE.md`, `specs/canonical_packet.schema.json`

---

## Current State: Notebooks Only

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRESENT (2026-04-13)                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  notebooks/01_intake_and_normalization.ipynb  →  CanonicalPacket                │
│           ↓                                                                     │
│  notebooks/02_gap_and_decision.ipynb          →  DecisionResult                 │
│           ↓                                                                     │
│  notebooks/03_session_strategy.ipynb         →  PromptBundle                   │
│                                                                                  │
│  All logic in Jupyter notebooks. No web UI. No API. No persistence.             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Current Limitations

1. **No web interface** - Agents must run notebooks manually
2. **No persistence** - Can't save packets between sessions
3. **No real-time updates** - Must re-run cells to see changes
4. **No multi-user support** - One agent per notebook instance
5. **No WhatsApp integration** - Copy-paste messages manually

---

## Target State: Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  TARGET (Future)                                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐            │
│  │   Web UI        │     │   Mobile View   │     │  WhatsApp Bot   │            │
│  │  (React/Next)   │     │  (Responsive)   │     │  (Integration)  │            │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘            │
│           │                      │                       │                     │
│           └──────────────────────┴───────────────────────┘                     │
│                              │                                                  │
│                              ↓                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        API LAYER (FastAPI)                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │  Intake API │  │ Decision   │  │  Strategy   │  │  Customer  │      │   │
│  │  │             │  │  API       │  │   API      │  │    API     │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                  │
│                              ↓                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    SERVICE LAYER (Python)                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │   NB01      │  │   NB02      │  │   NB03      │  │  Customer  │      │   │
│  │  │  Service    │  │  Service    │  │  Service    │  │  Service   │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                  │
│                              ↓                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA LAYER                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ PostgreSQL  │  │    Redis    │  │   Vector    │  │   S3/      │      │   │
│  │  │ (Packets)   │  │  (Cache)    │  │   DB (Embed) │  │  Files     │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Migration Path: Notebook → Service → API → UI

### Phase 1: Extract to Services (Immediate)

**Goal**: Make notebook logic callable as Python functions

```python
# src/services/nb01_service.py
from typing import Dict, Any
from pydantic import BaseModel

class IntakeRequest(BaseModel):
    raw_input: str
    source_channel: str  # "whatsapp", "email", "form"
    customer_id: str | None = None

class IntakeResponse(BaseModel):
    packet_id: str
    packet: CanonicalPacket
    processing_time_ms: float
    confidence: float

def extract_and_normalize(request: IntakeRequest) -> IntakeResponse:
    """
    Extracted from notebooks/01_intake_and_normalization.ipynb

    This function contains ALL the logic from NB01, callable as:
    result = extract_and_normalize(IntakeRequest(raw_input="..."))
    """
    # [NB01 logic here - fact extraction, ambiguity detection, etc.]
    return response

# src/services/nb02_service.py
class DecisionRequest(BaseModel):
    packet: CanonicalPacket
    current_stage: str
    operating_mode: str
    mvb_config: Dict | None = None

class DecisionResponse(BaseModel):
    result: DecisionResult
    next_actions: List[str]
    recommended_questions: List[str]

def make_decision(request: DecisionRequest) -> DecisionResponse:
    """
    Extracted from notebooks/02_gap_and_decision.ipynb

    Contains ALL decision logic from NB02
    """
    # [NB02 logic here - blocker checks, feasibility, contradictions]
    return response

# src/services/nb03_service.py
class StrategyRequest(BaseModel):
    packet: CanonicalPacket
    decision_result: DecisionResult
    output_mode: str  # "traveler_safe", "internal_draft", "both"

class StrategyResponse(BaseModel):
    prompts: PromptBundle
    message_templates: List[str]
    confidence: float

def build_strategy(request: StrategyRequest) -> StrategyResponse:
    """
    Extracted from notebooks/03_session_strategy.ipynb

    Contains ALL prompt generation logic from NB03
    """
    # [NB03 logic here - prompt builders, tone, traveler-safe transformations]
    return response
```

### Phase 2: Add API Layer (FastAPI)

```python
# src/api/main.py
from fastapi import FastAPI, HTTPException
from src.services.nb01_service import extract_and_normalize
from src.services.nb02_service import make_decision
from src.services.nb03_service import build_strategy

app = FastAPI(title="Agency OS API", version="0.1.0")

# Health check
@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.1.0"}

# Endpoints
@app.post("/api/v1/intake", response_model=IntakeResponse)
def intake(request: IntakeRequest):
    """
    NB01: Extract and normalize raw input into CanonicalPacket
    """
    try:
        return extract_and_normalize(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/decision", response_model=DecisionResponse)
def decision(request: DecisionRequest):
    """
    NB02: Given a packet, determine what to do next
    """
    try:
        return make_decision(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/strategy", response_model=StrategyResponse)
def strategy(request: StrategyRequest):
    """
    NB03: Generate prompts and message templates
    """
    try:
        return build_strategy(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Combined endpoint (most common)
@app.post("/api/v1/process", response_model=ProcessResponse)
class ProcessResponse(BaseModel):
    packet: CanonicalPacket
    decision: DecisionResult
    strategy: StrategyResponse

def process_inquiry(request: ProcessRequest):
    """
    Run full pipeline: NB01 → NB02 → NB03
    """
    # NB01
    intake_result = extract_and_normalize(request.intake)
    # NB02
    decision_result = make_decision(DecisionRequest(packet=intake_result.packet))
    # NB03
    strategy_result = build_strategy(StrategyRequest(
        packet=intake_result.packet,
        decision_result=decision_result
    ))
    return ProcessResponse(
        packet=intake_result.packet,
        decision=decision_result,
        strategy=strategy_result
    )
```

### Phase 3: Add Persistence Layer

```python
# src/services/customer_service.py
from sqlalchemy.orm import Session
from src.db.models import Customer, Packet, ConversationTurn

class CustomerService:
    def get_or_create_customer(self, phone: str, db: Session) -> Customer:
        """Lookup by phone (WhatsApp ID), create if new"""
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        if not customer:
            customer = Customer(phone=phone, name="Unknown")
            db.add(customer)
            db.commit()
        return customer

    def save_packet(self, packet: CanonicalPacket, customer_id: str, db: Session):
        """Save packet with version history"""
        db_packet = Packet(
            packet_id=packet.packet_id,
            customer_id=customer_id,
            schema_version=packet.schema_version,
            stage=packet.stage,
            operating_mode=packet.operating_mode,
            facts_json=packet.facts.model_dump_json(),
            # ... other fields
        )
        db.add(db_packet)
        db.commit()
        return db_packet

    def get_customer_history(self, customer_id: str, db: Session) -> List[Packet]:
        """Get all past packets for repeat customer recognition"""
        return db.query(Packet).filter(
            Packet.customer_id == customer_id
        ).order_by(Packet.created_at.desc()).all()

# src/db/models.py
from sqlalchemy import Column, String, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True)
    phone = Column(String, unique=True, nullable=False)
    name = Column(String)
    email = Column(String)
    preferences = Column(JSON)  # Store learned preferences
    created_at = Column(DateTime)
    last_contact = Column(DateTime)

class Packet(Base):
    __tablename__ = "packets"

    id = Column(Integer, primary_key=True)
    packet_id = Column(String, unique=True, nullable=False)
    customer_id = Column(String, nullable=False)
    schema_version = Column(String)
    stage = Column(String)
    operating_mode = Column(String)
    facts = Column(JSON)
    derived_signals = Column(JSON)
    ambiguities = Column(JSON)
    contradictions = Column(JSON)
    decision_state = Column(String | None)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id = Column(Integer, primary_key=True)
    packet_id = Column(String, nullable=False)
    role = Column(String)  # "customer" or "agent"
    content = Column(String)
    channel = Column(String)  # "whatsapp", "email", etc.
    timestamp = Column(DateTime)
```

### Phase 4: Frontend Integration

```typescript
// Frontend talks to API

interface ProcessInquiryRequest {
  raw_input: string;
  source_channel: "whatsapp" | "email" | "form";
  customer_id?: string;
}

interface ProcessInquiryResponse {
  packet: CanonicalPacket;
  decision: DecisionResult;
  strategy: {
    prompts: PromptBundle;
    message_templates: string[];
  };
}

// React component
async function handleCustomerMessage(message: string) {
  const response = await fetch('/api/v1/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      raw_input: message,
      source_channel: 'whatsapp',
      customer_id: currentCustomer?.id
    })
  });

  const data: ProcessInquiryResponse = await response.json();

  // Update UI
  setPacket(data.packet);
  setDecision(data.decision);
  setSuggestedMessages(data.strategy.message_templates);
}
```

---

## API Contract Definitions

### NB01 Intake API

```python
# POST /api/v1/intake
# Request: Raw customer message
{
  "raw_input": "Hi, planning Europe trip for 5 people, June, 4-5L budget",
  "source_channel": "whatsapp",
  "customer_id": "cust_123"  # Optional, for repeat customers
}

# Response: Structured packet
{
  "packet_id": "pkt_abc123",
  "packet": {
    "schema_version": "0.2",
    "stage": "discovery",
    "operating_mode": "normal_intake",
    "facts": {
      "party_size": {"value": 5, "confidence": 0.9, ...},
      "destination_candidates": {"value": ["Europe"], ...},
      "date_window": {"value": "June", ...},
      "budget_min": {"value": 400000, ...}
    },
    "derived_signals": {},
    "ambiguities": [
      {
        "field_name": "destination_candidates",
        "ambiguity_type": "destination_open",
        "raw_value": "Europe",
        "severity": "blocking"
      }
    ],
    "contradictions": [],
    "hypotheses": [],
    "unknowns": []
  },
  "processing_time_ms": 145,
  "confidence": 0.78
}
```

### NB02 Decision API

```python
# POST /api/v1/decision
# Request: Packet + context
{
  "packet": { ... },  # CanonicalPacket from NB01
  "current_stage": "discovery",
  "operating_mode": "normal_intake",
  "mvb_config": {}  # Optional config override
}

# Response: Decision + next actions
{
  "result": {
    "packet_id": "pkt_abc123",
    "current_stage": "discovery",
    "operating_mode": "normal_intake",
    "decision_state": "ASK_FOLLOWUP",
    "hard_blockers": ["destination_candidates", "party_size"],
    "soft_blockers": ["trip_purpose"],
    "ambiguities": [...],
    "contradictions": [],
    "follow_up_questions": [
      {
        "question": "Is the 5th person a grandparent?",
        "field": "party_composition",
        "priority": "high"
      }
    ],
    "rationale": {
      "primary_reason": "Blocking ambiguities prevent proposal generation",
      " blockers": ["destination too broad", "party size unclear"]
    },
    "confidence_score": 0.65,
    "risk_flags": [
      {"type": "budget_feasibility", "severity": "advisory", "message": "..."}
    ]
  },
  "next_actions": [
    "Send clarification questions",
    "Wait for customer response",
    "Re-run decision when blockers cleared"
  ],
  "recommended_questions": [
    "Is the 5th person a grandparent?",
    "When you say 'Europe' - which country?",
    "Is 4-5L per person or total?"
  ]
}
```

### NB03 Strategy API

```python
# POST /api/v1/strategy
# Request: Packet + Decision
{
  "packet": { ... },
  "decision_result": { ... },
  "output_mode": "both"  # "traveler_safe", "internal_draft", or "both"
}

# Response: Prompts + message templates
{
  "prompts": {
    "traveler_safe": [
      {
        "role": "agent_message",
        "content": "Hi! Quick questions to find the best options...",
        "is_internal": false,
        "channel": "whatsapp"
      }
    ],
    "internal_draft": [
      {
        "role": "system_note",
        "content": "Budget is tight. Consider Andaman if Switzerland is too expensive.",
        "is_internal": true
      }
    ]
  },
  "message_templates": [
    "Hi! Quick questions to find the best options: 1) Is the 5th person a grandparent?..."
  ],
  "confidence": 0.78
}
```

### Combined Process API

```python
# POST /api/v1/process
# Request: Raw message (most common endpoint)
{
  "message": "Hi, planning Europe trip for 5 people, June, 4-5L budget",
  "customer_phone": "+91-98765-43210",
  "source_channel": "whatsapp"
}

# Response: Full pipeline output
{
  "customer": {
    "id": "cust_123",
    "name": "Mrs. Sharma",
    "is_repeat": true,
    "past_trips": [
      {"destination": "Singapore", "date": "2024-03", "budget": 250000}
    ]
  },
  "packet": { ... },
  "decision": {
    "decision_state": "ASK_FOLLOWUP",
    "hard_blockers": ["destination_candidates"],
    "follow_up_questions": [...]
  },
  "suggested_actions": {
    "send_message": "Hi Mrs. Sharma! Great to hear from you. Quick question...",
    "next_state": "waiting_for_response"
  },
  "ui_hints": {
    "show": ["blocker_panel", "repeat_customer_banner"],
    "highlight": ["budget_feasibility_warning"]
  }
}
```

---

## State Management Strategy

### Client-Side State (React/Frontend)

```typescript
interface AppState {
  // Current customer
  currentCustomer: Customer | null;

  // Current packet (from NB01)
  currentPacket: CanonicalPacket | null;

  // Current decision (from NB02)
  currentDecision: DecisionResult | null;

  // UI state
  ui: {
    activeView: "list" | "detail" | "proposal";
    sidebarOpen: boolean;
    filters: FilterState;
  };

  // Messages
  messages: Message[];
}

// Redux slice
const packetSlice = createSlice({
  name: 'packet',
  initialState: {
    current: null,
    history: [],
  },
  reducers: {
    setPacket: (state, action) => {
      state.current = action.payload;
    },
    updatePacketField: (state, action) => {
      if (state.current) {
        state.current.facts[action.payload.field] = action.payload.value;
      }
    },
  },
});
```

### Server-Side State (Database)

| Table | Purpose | Retention |
|-------|---------|-----------|
| `customers` | Customer profiles, preferences, history | Forever |
| `packets` | All packets, versioned | Forever (for analytics) |
| `conversation_turns` | Individual messages | 90 days |
| `documents` | Uploaded passports, visas | Until trip completion + 30 days |
| `quotes` | Generated proposals | 1 year |
| `bookings` | Confirmed bookings | Forever (legal requirement) |

---

## WhatsApp Integration

### Two Approaches

#### Option A: WhatsApp Business API (Official)

```python
# src/services/whatsapp_service.py
from fastapi import BackgroundTasks
import requests

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/YOUR_PHONE_ID/messages"

async def send_whatsapp_message(
    to_phone: str,
    message: str,
    message_id: str  # For threading
):
    """Send message via WhatsApp Business API"""

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {
            "body": message,
            "preview_url": False
        },
        "context": {
            "message_id": message_id  # Thread as reply
        }
    };

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    };

    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers);
    return response.json();

# Webhook endpoint for incoming messages
@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(payload: dict):
    """
    Receive incoming WhatsApp message, process through pipeline
    """
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0];
    from_phone = message["from"];
    text = message["text"]["body"];
    message_id = message["id"];

    # Process through NB01-NB02-NB03
    result = await process_inquiry({
        "message": text,
        "customer_phone": from_phone,
        "source_channel": "whatsapp"
    });

    # Send response
    if result.decision.decision_state in ["ASK_FOLLOWUP", "PROCEED_TRAVELER_SAFE"]:
        await send_whatsapp_message(
            to_phone=from_phone,
            message=result.suggested_actions.send_message,
            message_id=message_id
        );

    return {"status": "processed"};
```

#### Option B: Manual Send (Copy-Paste)

```python
# Simpler approach for MVP
# Agent sees message in dashboard, copies to WhatsApp manually

@app.get("/api/v1/messages/{packet_id}/copy-format")
def get_copy_format(packet_id: str):
    """
    Return formatted message ready to copy-paste into WhatsApp
    """
    packet = get_packet(packet_id);
    decision = get_decision(packet_id);

    formatted = format_for_whatsapp({
        "customer_name": packet.facts.get("customer_name")?.value,
        "questions": decision.follow_up_questions,
        "tone": "warm_friendly"
    });

    return {
        "text": formatted,
        "html": render_whatsapp_preview(formatted)
    };
```

---

## Real-Time Updates

### WebSocket for Multi-Agent Sync

```python
# src/api/websocket.py
from fastapi import WebSocket

@app.websocket("/ws/customer/{customer_id}")
async def customer_updates(websocket: WebSocket, customer_id: str):
    """
    Real-time updates when multiple agents work on same customer
    """
    await websocket.accept();

    try:
        while True:
            # Wait for updates
            update = await customer_update_queue.get(customer_id);

            # Send to client
            await websocket.send_json({
                "type": update.type,
                "packet_id": update.packet_id,
                "data": update.data
            });
    except WebSocketDisconnect:
        pass;

# Usage: When Agent A updates a packet
async def on_packet_updated(packet_id: str, agent_id: str):
    await customer_update_queue.put(
        customer_id,
        Update(type="packet_updated", packet_id=packet_id, agent_id=agent_id)
    );
    # Agent B sees: "Mrs. Sharma's profile updated by Priya"
```

---

## Caching Strategy

### What to Cache (Redis)

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Customer profile | 1 hour | Rarely changes during session |
| Packet by ID | Session | Must be fresh, but cache for UI rendering |
| Decision result | 5 minutes | Expensive to recompute, rare to change |
| Message templates | 1 hour | Static templates |
| Budget feasibility | 24 hours | External data, slow to compute |

```python
# src/cache.py
from redis import Redis
import json

redis = Redis(host='localhost', port=6379, decode_responses=True);

def cache_packet(packet: CanonicalPacket, ttl_seconds: int = 3600):
    key = f"packet:{packet.packet_id}";
    redis.setex(key, ttl_seconds, packet.model_dump_json());

def get_cached_packet(packet_id: str) -> CanonicalPacket | None:
    key = f"packet:{packet_id}";
    data = redis.get(key);
    if data:
        return CanonicalPacket.model_validate_json(data);
    return None;

def invalidate_packet(packet_id: str):
    key = f"packet:{packet_id}";
    redis.delete(key);
```

---

## Error Handling

### Error Categories

| Error Type | HTTP Status | User Message | Log Level |
|------------|-------------|--------------|-----------|
| Validation error | 400 | "Please check your input" | INFO |
| Ambiguity detected | 200 | (Normal flow) | DEBUG |
| Budget infeasible | 200 | (Normal flow with flag) | INFO |
| External API failure | 502 | "Having trouble connecting..." | ERROR |
| Database error | 500 | "Something went wrong" | CRITICAL |

```python
# src/api/errors.py
from fastapi import HTTPException

class AgencyOSException(Exception):
    """Base exception for Agency OS"""

class AmbiguityError(AgencyOSException):
    """Not really an error - normal flow"""
    pass

class BudgetInfeasibleError(AgencyOSException):
    """Not an error - normal flow with flag"""
    pass

class ExternalServiceError(AgencyOSException):
    """External API (pricing, suppliers) failed"""
    pass

# Handler
@app.exception_handler(AgencyOSException)
async def agency_exception_handler(request, exc):
    return JSONResponse(
        status_code=200 if isinstance(exc, (AmbiguityError, BudgetInfeasibleError)) else 500,
        content={"error": str(exc), "type": type(exc).__name__}
    )
```

---

## Monitoring & Observability

### Metrics to Track

```python
# src/monitoring.py
from prometheus_client import Counter, Histogram

# Business metrics
inquiries_total = Counter('inquiries_total', 'Total inquiries received')
decisions_by_state = Counter('decisions_by_state', 'Decisions by state', ['decision_state'])
quotes_sent = Counter('quotes_sent', 'Quotes sent to customers')
bookings_completed = Counter('bookings_completed', 'Bookings completed')

# Technical metrics
processing_time = Histogram('processing_time_seconds', 'Time to process inquiry')
nb01_duration = Histogram('nb01_duration_seconds', 'NB01 processing time')
nb02_duration = Histogram('nb02_duration_seconds', 'NB02 processing time')
nb03_duration = Histogram('nb03_duration_seconds', 'NB03 processing time')

# Usage in code
@processing_time.time()
def process_inquiry(request):
    with nb01_duration.time():
        packet = extract_and_normalize(request)
    with nb02_duration.time():
        decision = make_decision(packet)
    # ...
```

---

## Deployment Considerations

### Development

```bash
# Run API locally
uvicorn src.api.main:app --reload --port 8000

# Run with notebooks (for testing)
jupyter notebook notebooks/  # Services still importable
```

### Production

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src/ src/
COPY notebooks/ notebooks/  # For reference, not execution

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRODUCTION INFRASTRUCTURE                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐            │
│  │   CDN (Cloudflare)   │   │   Load Balancer  │   │   API Servers    │            │
│  │   (Static assets)    │   │   (AWS ALB)      │   │   (ECS/Fargate)  │            │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘            │
│                                                              │                  │
│                              ┌────────────────────────────────┴───────────┐       │
│                              │                                      │         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         DATA STORES                                    ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ││
│  │  │   RDS       │  │   ElastiCache│  │    OpenSearch│  │    S3       │  ││
│  │  │ (PostgreSQL)│  │   (Redis)   │  │  (Logging)  │  │   (Files)   │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         EXTERNAL SERVICES                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   WhatsApp  │  │    LLM      │  │   Pricing   │  │   Supplier  │  │   │
│  │  │  Business API│  │  (Claude/   │  │   APIs      │  │   APIs      │  │   │
│  │  │             │  │   OpenAI)   │  │             │  │             │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Next Steps for Implementation

1. **Week 1-2**: Extract NB01, NB02, NB03 to service functions
2. **Week 3**: Build FastAPI wrapper with basic endpoints
3. **Week 4**: Add PostgreSQL persistence for packets
4. **Week 5**: Build basic React dashboard (customer list + detail view)
5. **Week 6**: WhatsApp Business API integration (or copy-paste MVP)
6. **Week 7**: Real-time updates (WebSocket)
7. **Week 8**: Monitoring, logging, error handling

---

## Related Documentation

- `specs/canonical_packet.schema.json` - Core data structure
- `UX_DASHBOARDS_BY_PERSONA.md` - What the UI should look like
- `notebooks/` - Current notebook implementations (source of truth for logic)

---

*This is a living document. As implementation progresses, update with actual decisions made.*
