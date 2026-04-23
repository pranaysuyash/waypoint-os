# Timeline: AI/ML Deep Dive

> AI enhancement, intelligent features, and machine learning patterns for Timeline

---

## Part 1: AI Philosophy for Timeline

### The Role of AI

Timeline without AI is useful — a chronological log. Timeline with AI is **powerful** — an intelligent assistant that surfaces insights, patterns, and meaning.

**AI enhances Timeline in three ways:**

1. **Summarization:** Condense thousands of events into digestible insights
2. **Pattern Recognition:** Find trends across trips that humans miss
3. **Prediction:** Anticipate needs and flag risks before they become problems

**Principles:**

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Human-in-the-loop** | AI suggests, human decides | All AI actions require confirmation |
| **Explainable** | Always show reasoning | "Why this recommendation?" visible |
| **Gradual** | Start simple, improve over time | V1: rules → V2: ML → V3: deep learning |
| **Privacy-first** | Train on anonymized data | No customer PII in training sets |
| **Fallback-safe** | Graceful degradation | System works if AI is down |

---

## Part 2: AI Feature Taxonomy

### 2.1 Event-Level AI

| Feature | Description | Phase |
|---------|-------------|-------|
| **Smart Summaries** | AI-generated event summaries | P1 |
| **Sentiment Analysis** | Detect customer emotion | P1 |
| **Urgency Detection** | Flag time-sensitive events | P1 |
| **Entity Extraction** | Extract key info from unstructured text | P1 |
| **Duplicate Detection** | Find similar/redundant events | P2 |
| **Anomaly Detection** | Flag unusual events | P2 |

### 2.2 Trip-Level AI

| Feature | Description | Phase |
|---------|-------------|-------|
| **Trip Summary** | "What happened on this trip" | P1 |
| **Milestone Extraction** | Key moments in trip journey | P1 |
| **Story Arc** | Narrative structure of trip | P2 |
| **Risk Score** | Probability of issues | P2 |
| **Health Score** | Overall trip "wellness" | P3 |
| **Next Best Action** | What should agent do now | P3 |

### 2.3 Cross-Trip AI

| Feature | Description | Phase |
|---------|-------------|-------|
| **Pattern Detection** | "What do Thailand trips have in common" | P2 |
| **Similar Trips** | "This trip is like these 3" | P2 |
| **Benchmarking** | "How does this compare to typical" | P3 |
| **Predictive Modeling** | "This trip will likely need X" | P3 |
| **Optimization** | "What could have been better" | P4 |

---

## Part 3: Event-Level AI Features

### 3.1 Smart Summaries

**Problem:** Some events have long content (emails, transcripts, AI analysis). Agents need quick understanding.

**AI Solution:** Generate concise, context-aware summaries.

```typescript
interface AISummary {
  event_id: string;
  summary: string;           // 1-2 sentence summary
  key_points: string[];      // Bullet points of key info
  action_items?: string[];   // Any actions identified
  confidence: number;        // How confident is AI
  generated_at: string;
}

interface TripEvent {
  // ... existing fields
  aiSummary?: AISummary;
}
```

**Implementation:**

```python
class EventSummarizer:
    """Generate AI summaries for events"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def summarize_event(self, event: TripEvent) -> AISummary:
        """Generate summary for a single event"""

        # Skip if already summarized
        if event.ai_summary:
            return event.ai_summary

        # Build prompt based on event type
        prompt = self._build_summary_prompt(event)

        # Call LLM
        response = await self.llm.complete(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3  # Low temp for factual summary
        )

        # Parse response
        summary = self._parse_summary_response(response, event)

        return summary

    def _build_summary_prompt(self, event: TripEvent) -> str:
        """Build prompt based on event type"""

        base_prompt = f"""You are a travel agency assistant. Summarize this event concisely.

Event Type: {event.event_type}
Timestamp: {event.timestamp}
Actor: {event.actor.name} ({event.actor.type})

Content:
"""

        if event.event_type == 'whatsapp_message_received':
            return base_prompt + f"""
Customer Message: {event.content.get('message')}

Provide:
1. One-sentence summary
2. Key points (what customer wants/asks)
3. Any action items for agent
"""

        elif event.event_type == 'analysis_scenarios':
            return base_prompt + f"""
AI evaluated {len(event.content.get('scenarios', []))} scenarios.

Selected: {event.content.get('rationale')}

Provide:
1. What was decided
2. Why this choice
3. Any risks/concerns
"""

        # ... other event types

        return base_prompt + str(event.content)
```

**Display in UI:**

```
┌─────────────────────────────────────────────────────────────┐
│  🕐 YESTERDAY — 2:35 PM                            [▲]    │
│  🤖 AI ANALYSIS: Scenarios Evaluated                       │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  📝 AI Summary:                                                   │
│  Evaluated 3 scenarios for Thailand honeymoon. Selected          │
│  Phuket+Krabi (₹1.8L-2.2L) for best balance of beaches,         │
│  weather, and budget fit.                                        │
│                                                                     │
│  Key Points:                                                       │
│  • Scenario A offers romantic beaches within budget              │
│  • June is optimal weather for Andaman coast                     │
│  • Direct flights available from major cities                    │
│                                                                     │
│  [View Full Details]                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.2 Sentiment Analysis

**Problem:** Customer emotion is critical context. Frustrated customers need different handling than happy ones.

**AI Solution:** Analyze customer messages for sentiment.

```typescript
interface SentimentAnalysis {
  event_id: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
  emotions: {
    joy?: number;        // 0-1
    anger?: number;
    fear?: number;
    sadness?: number;
    surprise?: number;
  };
  triggers?: string[];   // What caused this sentiment
  analyzed_at: string;
}

interface TripEvent {
  aiSentiment?: SentimentAnalysis;
}
```

**Implementation:**

```python
class SentimentAnalyzer:
    """Analyze sentiment of customer communications"""

    def __init__(self):
        # Load pre-trained model
        self.model = load_model('sentiment-model-v1')
        self.emotion_classifier = load_model('emotion-model-v1')

    async def analyze_event(self, event: TripEvent) -> SentimentAnalysis:
        """Analyze sentiment of an event"""

        # Only analyze customer events
        if event.actor.type != 'customer':
            return None

        # Get text content
        text = self._extract_text(event)
        if not text:
            return None

        # Predict sentiment
        sentiment_result = self.model.predict(text)

        # Predict emotions
        emotion_result = self.emotion_classifier.predict(text)

        return SentimentAnalysis(
            event_id=event.id,
            sentiment=sentiment_result.label,
            confidence=sentiment_result.confidence,
            emotions=emotion_result.emotions,
            triggers=self._identify_triggers(text, sentiment_result)
        )

    def _extract_text(self, event: TripEvent) -> str:
        """Extract text from event content"""
        if event.event_type in ['whatsapp_message_received', 'whatsapp_message_sent']:
            return event.content.get('message', '')
        elif event.event_type == 'email_received':
            return event.content.get('body', '')
        # ... other event types
        return ''
```

**Visual Indicators in Timeline:**

```
┌─────────────────────────────────────────────────────────────┐
│  💬 YESTERDAY — 3:20 PM                                     │
│  Customer: "This is ridiculous! I've been waiting for       │
│            3 days and still no quote!"                       │
│                                                                     │
│  😠 Negative (87% confident)                                 │
│  Emotions: Anger (0.82), Frustration (0.76)               │
│  Trigger: Delay in quote delivery                          │
│                                                                     │
│  ⚠️ Suggested Action: Call customer immediately              │
│  to apologize and provide update.                            │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.3 Urgency Detection

**Problem:** Some messages need immediate attention. Agents need to know what's urgent.

**AI Solution:** Classify urgency of events.

```typescript
interface UrgencyAnalysis {
  event_id: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  reason: string;           // Why is this urgent?
  time_sensitivity?: {      // If time-sensitive
    deadline?: string;      // When does it need attention?
    reason: string;         // Why this deadline?
  };
  analyzed_at: string;
}

interface TripEvent {
  aiUrgency?: UrgencyAnalysis;
}
```

**Implementation (Rule-based + ML):**

```python
class UrgencyDetector:
    """Detect urgency of events"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.rules = self._load_urgency_rules()

    async def detect_urgency(self, event: TripEvent) -> UrgencyAnalysis:
        """Detect urgency of an event"""

        # First, check rules (fast, deterministic)
        rule_result = self._check_rules(event)
        if rule_result:
            return rule_result

        # Then, use ML for nuanced cases
        return await self._ml_detect(event)

    def _check_rules(self, event: TripEvent) -> UrgencyAnalysis:
        """Check urgency rules"""

        text = self._extract_text(event).lower()

        # Critical urgency keywords
        critical_keywords = [
            'emergency', 'urgent', 'asap', 'immediately',
            'cancel booking', 'wrong date', 'payment failed',
            'complaint', 'dispute', 'refund', 'legal action'
        ]

        # High urgency keywords
        high_keywords = [
            'need response', 'waiting for', 'follow up',
            'deadline', 'by tomorrow', 'today only'
        ]

        # Check for time-sensitive phrases
        if any(kw in text for kw in critical_keywords):
            return UrgencyAnalysis(
                event_id=event.id,
                urgency='critical',
                confidence=0.95,
                reason=f"Contains critical keyword: {self._matched_keyword(text, critical_keywords)}"
            )

        if any(kw in text for kw in high_keywords):
            return UrgencyAnalysis(
                event_id=event.id,
                urgency='high',
                confidence=0.90,
                reason=f"Contains urgent keyword: {self._matched_keyword(text, high_keywords)}"
            )

        # Check for deadline mentioned
        deadline = self._extract_deadline(text)
        if deadline:
            hours_until = (deadline - datetime.now()).total_seconds() / 3600

            if hours_until < 4:
                return UrgencyAnalysis(
                    event_id=event.id,
                    urgency='critical',
                    confidence=0.85,
                    reason="Deadline within 4 hours",
                    time_sensitivity={'deadline': deadline.isoformat()}
                )
            elif hours_until < 24:
                return UrgencyAnalysis(
                    event_id=event.id,
                    urgency='high',
                    confidence=0.85,
                    reason="Deadline within 24 hours",
                    time_sensitivity={'deadline': deadline.isoformat()}
                )

        return None

    async def _ml_detect(self, event: TripEvent) -> UrgencyAnalysis:
        """Use ML to detect urgency"""

        prompt = f"""Analyze the urgency of this customer message.

Message: {self._extract_text(event)}

Respond with JSON:
{{
  "urgency": "low|medium|high|critical",
  "reason": "explanation",
  "confidence": 0.0-1.0
}}
"""

        response = await self.llm.complete(prompt)

        return UrgencyAnalysis(
            event_id=event.id,
            **json.loads(response)
        )
```

**UI Display:**

```
Timeline Panel with Urgency Filter:

┌─────────────────────────────────────────────────────────────┐
│  Timeline                                          [🔴 Urgent] │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔴 CRITICAL — 5 min ago                                   │
│  Customer: "I need to cancel immediately!"                    │
│  → Action required: Call customer NOW                        │
│                                                                     │
│  🟠 HIGH — 1 hour ago                                       │
│  Customer: "Still waiting for the quote"                      │
│  → Action required: Respond within 2 hours                   │
│                                                                     │
│  🟡 MEDIUM — 3 hours ago                                    │
│  AI: Decision changed to Needs Attention                      │
│  → Review recommended                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.4 Entity Extraction

**Problem:** Unstructured text contains valuable data (dates, places, budgets) that should be structured.

**AI Solution:** Extract entities from messages.

```typescript
interface EntityExtraction {
  event_id: string;
  entities: {
    dates?: DateEntity[];
    destinations?: DestinationEntity[];
    budget?: BudgetEntity[];
    people?: PeopleEntity[];
    contacts?: ContactEntity[];
  };
  confidence: number;
  extracted_at: string;
}

interface DateEntity {
  text: string;
  value: string;          // ISO date
  type: 'departure' | 'return' | 'flexible' | 'deadline';
  confidence: number;
}

interface DestinationEntity {
  text: string;
  value: string;          // Normalized name
  type: 'country' | 'city' | 'region' | 'airport';
  confidence: number;
}

interface BudgetEntity {
  text: string;
  value: number;          // In INR
  currency: string;
  type: 'total' | 'per_person' | 'per_day';
  confidence: number;
}
```

**Implementation:**

```python
class EntityExtractor:
    """Extract entities from event text"""

    def __init__(self):
        self.ner_model = load_model('ner-model-v1')
        self.date_parser = DateParser()
        self.currency_parser = CurrencyParser()

    async def extract_entities(self, event: TripEvent) -> EntityExtraction:
        """Extract entities from event"""

        text = self._extract_text(event)
        if not text:
            return None

        # NER for entities
        ner_results = self.ner_model.extract(text)

        # Post-process by entity type
        entities = {
            'dates': self._process_dates(ner_results),
            'destinations': self._process_destinations(ner_results),
            'budget': self._process_budget(ner_results),
            'people': self._process_people(ner_results),
            'contacts': self._process_contacts(ner_results)
        }

        return EntityExtraction(
            event_id=event.id,
            entities=entities,
            confidence=self._calculate_confidence(entities)
        )
```

**Use Case: Auto-populate trip fields**

```python
async def apply_extracted_entities(event_id: str):
    """Apply extracted entities to trip fields"""

    event = await get_event(event_id)
    extracted = await entity_extractor.extract_entities(event)

    if extracted.entities.dates:
        # Ask agent: "Update trip dates from message?"
        for date in extracted.entities.dates:
            if date.type == 'departure':
                await suggest_field_update(
                    event.workspace_id,
                    'departure_date',
                    date.value,
                    source_event_id=event_id,
                    confidence=date.confidence
                )

    # ... similar for other entity types
```

---

## Part 4: Trip-Level AI Features

### 4.1 Trip Summary

**Problem:** A trip with 100+ events is overwhelming. Agents need a quick overview.

**AI Solution:** Generate intelligent trip summary.

```typescript
interface TripSummary {
  trip_id: string;
  summary: string;           // 2-3 paragraph narrative
  key_moments: KeyMoment[];  // Most important events
  timeline_summary: {
    total_events: number;
    duration: string;        // "3 weeks, 2 days"
    active_periods: string[];
  };
  status_summary: {
    current_state: string;
    progress: number;        // 0-100
    blockers: string[];
    next_steps: string[];
  };
  customer_profile: {
    communication_style: string;
    sentiment_trend: 'improving' | 'stable' | 'declining';
    engagement_level: 'high' | 'medium' | 'low';
  };
  generated_at: string;
}
```

**Implementation:**

```python
class TripSummarizer:
    """Generate AI summary of entire trip"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def summarize_trip(self, trip_id: str) -> TripSummary:
        """Generate comprehensive trip summary"""

        # Get all events for trip
        events = await get_trip_events(trip_id)

        # Generate narrative summary
        narrative = await self._generate_narrative(events)

        # Extract key moments
        key_moments = await self._extract_key_moments(events)

        # Calculate status summary
        status_summary = await self._calculate_status(events)

        # Analyze customer profile
        customer_profile = await self._analyze_customer(events)

        return TripSummary(
            trip_id=trip_id,
            summary=narrative,
            key_moments=key_moments,
            timeline_summary=self._summarize_timeline(events),
            status_summary=status_summary,
            customer_profile=customer_profile,
            generated_at=datetime.now().isoformat()
        )

    async def _generate_narrative(self, events: List[TripEvent]) -> str:
        """Generate narrative summary of trip"""

        # Build context for LLM
        context = self._build_summary_context(events)

        prompt = f"""Generate a 2-3 paragraph narrative summary of this trip.

Trip Context:
{context}

Focus on:
1. What customer originally wanted
2. How the trip evolved
3. Current status and what's pending

Write in a professional, concise style suitable for agent handoff.
"""

        response = await self.llm.complete(
            prompt=prompt,
            max_tokens=500,
            temperature=0.4
        )

        return response.strip()

    def _build_summary_context(self, events: List[TripEvent]) -> str:
        """Build context from events"""

        # Get key events only (don't overwhelm LLM)
        key_events = self._filter_key_events(events)

        context_parts = []
        for event in key_events[:20]:  # Limit to 20 key events
            context_parts.append(
                f"- {event.timestamp}: {event.event_type} - {event.summary or event.title}"
            )

        return "\n".join(context_parts)
```

**UI Display:**

```
┌─────────────────────────────────────────────────────────────┐
│  Trip Summary                                        [▲]    │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  Thailand Honeymoon Trip                                          │
│                                                                     │
│  This trip began on Apr 20 with an inquiry for a Thailand         │
│  honeymoon for 2 people in June with a ₹2L budget. The           │
│  customer later added Phi Phi Islands to their requirements,      │
│  which required re-evaluation of scenarios. After AI             │
│  evaluation, Phuket+Krabi was selected as the best option.        │
│                                                                     │
│  Currently, the trip is Ready to Book with all questions         │
│  answered. Budget has been confirmed at ₹2.2L. Customer           │
│  has been sent the quote and is awaiting their decision.          │
│                                                                     │
│  Key Moments:                                                      │
│  • Apr 20: Original inquiry received                              │
│  • Apr 21: AI selected Phuket+Krabi scenario                      │
│  • Apr 22: Customer added Phi Phi request                         │
│  • Apr 23: Quote sent to customer                                 │
│                                                                     │
│  Status: Ready to Book (87% confidence)                           │
│  Next steps: Await customer confirmation, then proceed            │
│  to booking                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.2 Milestone Extraction

**Problem:** Long trips have many events. Agents need to see the major milestones.

**AI Solution:** Identify and highlight key milestones.

```typescript
interface Milestone {
  id: string;
  name: string;
  description: string;
  event_id: string;          // The event that created this milestone
  timestamp: string;
  category: 'inquiry' | 'decision' | 'action' | 'communication' | 'milestone';
  importance: number;        // 0-1, higher = more important
  icon: string;
}

interface TripMilestones {
  trip_id: string;
  milestones: Milestone[];
  generated_at: string;
}
```

**Implementation:**

```python
class MilestoneExtractor:
    """Extract key milestones from trip events"""

    async def extract_milestones(self, trip_id: str) -> List[Milestone]:
        """Extract milestones from trip events"""

        events = await get_trip_events(trip_id)

        # Define milestone patterns
        milestone_patterns = {
            'inquiry_received': {
                'event_types': ['inquiry_received'],
                'importance': 1.0,
                'icon': '📧',
                'name': 'Trip Started'
            },
            'first_quote_sent': {
                'event_types': ['quote_sent'],
                'importance': 0.9,
                'icon': '💰',
                'name': 'First Quote',
                'selector': lambda events: events[0]  # First quote
            },
            'decision_ready': {
                'event_types': ['decision_changed'],
                'filter': lambda e: e.content.toState == 'READY_TO_BOOK',
                'importance': 0.95,
                'icon': '✅',
                'name': 'Ready to Book'
            },
            'customer_modification': {
                'event_types': ['field_updated'],
                'filter': lambda e: e.actor.type == 'customer',
                'importance': 0.7,
                'icon': '✏️',
                'name': 'Customer Updated'
            },
            'budget_change': {
                'event_types': ['field_updated'],
                'filter': lambda e: e.content.field == 'budget',
                'importance': 0.8,
                'icon': '💵',
                'name': 'Budget Changed'
            }
        }

        # Extract milestones
        milestones = []
        for pattern_name, pattern in milestone_patterns.items():
            matching_events = self._find_matching_events(events, pattern)
            for event in matching_events:
                milestones.append(Milestone(
                    id=f"ms_{event.id}",
                    name=pattern['name'],
                    description=self._generate_description(event),
                    event_id=event.id,
                    timestamp=event.timestamp,
                    importance=pattern['importance'],
                    icon=pattern['icon']
                ))

        # Sort by importance, then time
        milestones.sort(key=lambda m: (-m.importance, m.timestamp))

        return milestones
```

---

### 4.3 Risk Score

**Problem:** Some trips are riskier than others (budget issues, difficult customers, tight deadlines). Agents need to know.

**AI Solution:** Calculate trip risk score.

```typescript
interface RiskScore {
  trip_id: string;
  overall_score: number;      // 0-100, higher = riskier
  risk_factors: RiskFactor[];
  trend: 'improving' | 'stable' | 'worsening';
  recommendations: string[];
  calculated_at: string;
}

interface RiskFactor {
  category: 'budget' | 'timeline' | 'customer' | 'complexity' | 'supplier';
  score: number;              // 0-100
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  events: string[];           // Event IDs contributing to this risk
}
```

**Implementation:**

```python
class RiskScorer:
    """Calculate risk score for trips"""

    def __init__(self):
        self.risk_rules = self._load_risk_rules()

    async def calculate_risk(self, trip_id: str) -> RiskScore:
        """Calculate comprehensive risk score"""

        events = await get_trip_events(trip_id)
        trip = await get_trip(trip_id)

        # Calculate individual risk factors
        budget_risk = await self._calculate_budget_risk(events, trip)
        timeline_risk = await self._calculate_timeline_risk(events, trip)
        customer_risk = await self._calculate_customer_risk(events)
        complexity_risk = await self._calculate_complexity_risk(events, trip)

        # Combine into overall score
        overall_score = self._combine_scores([
            budget_risk,
            timeline_risk,
            customer_risk,
            complexity_risk
        ])

        # Generate trend
        trend = await self._calculate_trend(events)

        # Generate recommendations
        recommendations = self._generate_recommendations([
            budget_risk,
            timeline_risk,
            customer_risk,
            complexity_risk
        ])

        return RiskScore(
            trip_id=trip_id,
            overall_score=overall_score,
            risk_factors=[budget_risk, timeline_risk, customer_risk, complexity_risk],
            trend=trend,
            recommendations=recommendations,
            calculated_at=datetime.now().isoformat()
        )

    async def _calculate_budget_risk(self, events, trip) -> RiskFactor:
        """Calculate budget-related risk"""

        risk_score = 0
        contributing_events = []

        # Check if budget exceeds customer stated
        if trip.budget > trip.customer_stated_budget:
            overage = (trip.budget - trip.customer_stated_budget) / trip.customer_stated_budget
            risk_score += min(overage * 100, 50)

        # Check for budget changes (instability)
        budget_changes = [e for e in events if e.content.get('field') == 'budget']
        if len(budget_changes) > 2:
            risk_score += len(budget_changes) * 10
            contributing_events.extend([e.id for e in budget_changes])

        # Check if budget is tight
        if trip.budget and trip.estimated_cost:
            margin = (trip.budget - trip.estimated_cost) / trip.budget
            if margin < 0.1:  # Less than 10% margin
                risk_score += 30

        return RiskFactor(
            category='budget',
            score=min(risk_score, 100),
            description=self._describe_budget_risk(risk_score),
            severity=self._score_to_severity(risk_score),
            events=contributing_events
        )
```

**UI Display:**

```
┌─────────────────────────────────────────────────────────────┐
│  Trip Risk Score                                           │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  Overall Risk: 🔴 HIGH (72/100)                          │
│                                                                     │
│  Risk Factors:                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ 💰 Budget: 🟠 Medium (45/100)                       │      │
│  │ Budget changed 3 times. Currently 8% over customer    │      │
│  │ stated budget.                                         │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ ⏰ Timeline: 🔴 High (65/100)                        │      │
│  │ Travel dates in 2 weeks but flights not booked.       │      │
│  │ High risk of price increase.                           │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │ 👤 Customer: 🟡 Low (25/100)                         │      │
│  │ Customer sentiment is positive and cooperative.        │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  Recommendations:                                                  │
│  • Confirm budget with customer immediately                       │
│  • Book flights within 48 hours to lock prices                     │
│  • Consider offering payment plan for budget overage               │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 5: Cross-Trip AI Features

### 5.1 Pattern Detection

**Problem:** "What do all our Thailand honeymoons have in common?"

**AI Solution:** Find patterns across similar trips.

```typescript
interface TripPattern {
  pattern_id: string;
  name: string;
  description: string;
  matching_trips: string[];     // Trip IDs
  confidence: number;           // How strong is this pattern?
  common_attributes: {
    destinations?: string[];
    budget_range?: { min: number; max: number };
    duration_range?: { min: number; max: number };
    decision_points?: string[];
    common_issues?: string[];
  };
  success_rate?: number;        // How often does this pattern work?
  extracted_at: string;
}
```

**Implementation:**

```python
class PatternDetector:
    """Detect patterns across trips"""

    async def find_patterns(
        self,
        filters: TripFilters
    ) -> List[TripPattern]:
        """Find patterns matching filters"""

        # Get matching trips
        matching_trips = await self._find_similar_trips(filters)

        if len(matching_trips) < 3:  # Need minimum sample size
            return []

        patterns = []

        # Destination pattern
        dest_pattern = await self._detect_destination_pattern(matching_trips)
        if dest_pattern:
            patterns.append(dest_pattern)

        # Budget pattern
        budget_pattern = await self._detect_budget_pattern(matching_trips)
        if budget_pattern:
            patterns.append(budget_pattern)

        # Decision pattern
        decision_pattern = await self._detect_decision_pattern(matching_trips)
        if decision_pattern:
            patterns.append(decision_pattern)

        # Issue pattern
        issue_pattern = await self._detect_issue_pattern(matching_trips)
        if issue_pattern:
            patterns.append(issue_pattern)

        return patterns

    async def _detect_destination_pattern(
        self,
        trips: List[Trip]
    ) -> Optional[TripPattern]:
        """Detect destination selection patterns"""

        # Extract destinations from all trips
        destinations = []
        for trip in trips:
            events = await get_trip_events(trip.id)
            dest_events = [e for e in events if e.event_type == 'field_updated'
                          and e.content.get('field') == 'destination']
            destinations.extend([e.content.get('newValue') for e in dest_events])

        # Find most common
        from collections import Counter
        counter = Counter(destinations)

        if counter:
            most_common = counter.most_common(3)

            return TripPattern(
                pattern_id=f"dest_{uuid.uuid4().hex[:8]}",
                name=f"Common Destinations for {trips[0].destination}",
                description=f"Agents most frequently select: {', '.join([d for d, _ in most_common])}",
                matching_trips=[t.id for t in trips],
                confidence=sum([c for _, c in most_common]) / len(destinations),
                common_attributes={
                    'destinations': [d for d, _ in most_common]
                },
                extracted_at=datetime.now().isoformat()
            )

        return None
```

**UI Display:**

```
┌─────────────────────────────────────────────────────────────┐
│  Pattern Analysis                                    [▲]    │
├─────────────────────────────────────────────────────────────┤
│                                                                     │
│  For: Thailand Honeymoon trips (15 matched)                     │
│                                                                     │
│  📍 Destination Pattern:                                         │
│  87% of trips choose Phuket+Krabi                                │
│  13% choose Bangkok+Pattaya                                       │
│                                                                     │
│  💰 Budget Pattern:                                               │
│  Typical range: ₹1.8L - ₹2.5L                                    │
│  Average: ₹2.1L                                                   │
│  Your trip: ₹2.2L (within typical range) ✓                       │
│                                                                     │
│  ⏱️ Duration Pattern:                                             │
│  Typical: 5-7 days                                                │
│  Your trip: 6 days (typical) ✓                                   │
│                                                                     │
│  ⚠️ Common Issues:                                                │
│  • 40% have visa expiry concerns                                 │
│  • 27% have budget overage questions                             │
│  • 20% request Phi Phi addition                                   │
│                                                                     │
│  💡 Recommendations:                                              │
│  • Proactively check visa expiry dates                            │
│  • Have Phi Phi pricing ready                                     │
│  • Prepare budget justification before customer asks             │
│                                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.2 Similar Trips

**Problem:** "Has anyone handled a trip like this before?"

**AI Solution:** Find and rank similar trips.

```typescript
interface SimilarTrip {
  trip_id: string;
  similarity_score: number;    // 0-1
  similarity_reasons: string[];
  trip_summary: {
    destination: string;
    duration: string;
    budget: number;
    outcome: string;
  };
  timeline_preview: {
    event_count: number;
    duration: string;
    key_events: string[];
  };
  agent_notes?: string;
}

interface SimilarTripsResult {
  current_trip_id: string;
  similar_trips: SimilarTrip[];
  generated_at: string;
}
```

**Implementation:**

```python
class SimilarityFinder:
    """Find trips similar to current trip"""

    async def find_similar(
        self,
        trip_id: str,
        limit: int = 5
    ) -> List[SimilarTrip]:
        """Find similar trips"""

        current_trip = await get_trip(trip_id)
        current_events = await get_trip_events(trip_id)

        # Get all other trips
        all_trips = await get_all_trips(exclude=[trip_id])

        # Calculate similarity for each
        similarities = []
        for trip in all_trips:
            score = await self._calculate_similarity(
                current_trip,
                current_events,
                trip
            )

            if score > 0.3:  # Minimum threshold
                similarities.append((trip, score))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Convert to result
        results = []
        for trip, score in similarities[:limit]:
            results.append(await self._build_similar_trip(
                trip,
                score,
                current_trip
            ))

        return results

    async def _calculate_similarity(
        self,
        trip1: Trip,
        events1: List[TripEvent],
        trip2: Trip
    ) -> float:
        """Calculate similarity score between two trips"""

        score = 0.0

        # Destination similarity (high weight)
        if trip1.destination == trip2.destination:
            score += 0.3

        # Budget proximity (medium weight)
        if trip1.budget and trip2.budget:
            budget_diff = abs(trip1.budget - trip2.budget) / max(trip1.budget, trip2.budget)
            score += 0.2 * (1 - budget_diff)

        # Duration similarity (medium weight)
        if trip1.duration and trip2.duration:
            duration_diff = abs(trip1.duration - trip2.duration) / max(trip1.duration, trip2.duration)
            score += 0.15 * (1 - duration_diff)

        # Trip type similarity (medium weight)
        if trip1.trip_type == trip2.trip_type:
            score += 0.2

        # Event pattern similarity (low weight)
        events2 = await get_trip_events(trip2.id)
        pattern_similarity = await self._compare_event_patterns(events1, events2)
        score += 0.15 * pattern_similarity

        return min(score, 1.0)
```

---

### 5.3 Next Best Action

**Problem:** "What should I do now for this trip?"

**AI Solution:** Suggest next action based on trip state and patterns.

```typescript
interface NextActionSuggestion {
  action_id: string;
  action: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  reasoning: string;
  estimated_time: string;
  similar_cases?: string[];     // Trip IDs where this worked
  templates?: {                 // Ready-to-use templates
    message?: string;
    email_subject?: string;
    email_body?: string;
  };
}

interface NextActionsResult {
  trip_id: string;
  current_state: string;
  suggested_actions: NextActionSuggestion[];
  generated_at: string;
}
```

**Implementation:**

```python
class NextActionRecommender:
    """Recommend next actions for trips"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def recommend_actions(
        self,
        trip_id: str
    ) -> List[NextActionSuggestion]:
        """Recommend next actions"""

        trip = await get_trip(trip_id)
        events = await get_trip_events(trip_id)

        # Build context
        context = self._build_action_context(trip, events)

        # Get similar successful trips
        similar_trips = await self._get_similar_successful_trips(trip)

        # Build prompt
        prompt = f"""You are a travel agency expert. Based on the trip state and similar successful trips, recommend the next 3 actions.

Current Trip State:
{context}

Similar Successful Trips:
{self._format_similar_trips(similar_trips)}

For each action, provide:
1. Action (what to do)
2. Priority (low/medium/high/critical)
3. Reasoning (why this action)
4. Estimated time to complete
5. Any templates needed

Respond as JSON list.
"""

        response = await self.llm.complete(prompt)

        actions = json.loads(response)

        # Add metadata
        for action in actions:
            action['action_id'] = f"na_{uuid.uuid4().hex[:8]}"
            action['similar_cases'] = [t.id for t in similar_trips[:3]]

        return actions
```

---

## Part 6: AI Architecture

### 6.1 Model Selection Strategy

| Task | Current | Future | Data Required |
|------|---------|--------|---------------|
| **Summarization** | GPT-4o | Fine-tuned local model | 10K+ summaries |
| **Sentiment** | RoBERTa-sentiment | Fine-tuned on travel domain | 5K+ labeled |
| **Urgency** | Rules + BERT | Custom classifier | 3K+ labeled |
| **NER** | Spacy + custom | Travel-specific NER | 20K+ entities |
| **Similarity** | Embedding-based | Contrastive learning | 50K+ trips |
| **Risk** | Rule-based | Gradient boosting | 10K+ trips |

### 6.2 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Service Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  API Layer (FastAPI)                     │    │
│  │  POST /ai/summarize                                     │    │
│  │  POST /ai/sentiment                                     │    │
│  │  POST /ai/urgency                                       │    │
│  │  POST /ai/similar-trips                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                Request Queue (Redis)                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Worker Processes                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │ Summarization│  │ Sentiment    │  │ Similarity   │  │    │
│  │  │ Worker       │  │ Worker       │  │ Worker       │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Model Layer                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │ GPT-4o API   │  │ Local Models │  │ Embeddings   │  │    │
│  │  │ (Cloud)      │  │ (On-prem)    │  │ (Vector DB)  │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 7: AI Phasing

### Phase 1: Rule-Based (Months 1-3)

**Features:**
- Urgency detection via rules
- Entity extraction via regex/patterns
- Basic summarization templates

**Value:** 40% of AI value, 10% of AI cost

### Phase 2: Hybrid ML (Months 4-9)

**Features:**
- Sentiment analysis
- Smart summarization with LLM
- Similarity search via embeddings
- Pattern detection via clustering

**Value:** 70% of AI value, 40% of AI cost

### Phase 3: Advanced AI (Months 10-18)

**Features:**
- Risk scoring
- Next action recommendations
- Predictive modeling
- Fine-tuned domain models

**Value:** 100% of AI value, 100% of AI cost

---

## Summary

**AI transforms Timeline from a log into an intelligent assistant.**

**Immediate value (Phase 1):**
- Urgency detection prevents missed deadlines
- Entity extraction reduces manual data entry
- Rule-based patterns guide decisions

**Medium-term value (Phase 2):**
- Sentiment analysis improves customer handling
- Summarization accelerates understanding
- Similar trips enable learning

**Long-term value (Phase 3):**
- Risk scoring prevents problems
- Predictive recommendations guide actions
- Fine-tuned models create competitive advantage

**Key principle:** Start simple (rules), evolve to ML, never lose human oversight.

---

**Status:** AI/ML architecture complete. Ready for implementation.

**Next:** Legal/compliance deep dive (TIMELINE_06)
