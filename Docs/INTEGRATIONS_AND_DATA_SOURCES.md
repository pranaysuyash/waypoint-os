# Integrations and Data Sources

**Date**: 2026-04-14
**Purpose**: What APIs and services do you actually need?

---

## The Integration Trap

> "Every integration is a dependency, a maintenance burden, and potential point of failure."

**Principle**: Integrate only what's essential. Everything else is a "later."

---

## Core Truth: You Don't Need Most Integrations

**Agencies already know how to:**
- Search flights (GDS, OTA, airline sites)
- Search hotels (same)
- Check visa requirements (Google, embassy sites)
- Get weather info (weather apps)
- Check holidays (Google)

**Your job**: Help them with planning, not booking.

---

## What You DO Need (MVP)

### 1. LLM API (Non-negotiable)

| Provider | Why consider |
|----------|--------------|
| **OpenAI** | Best models, reliable |
| **Anthropic** | Claude is excellent for complex reasoning |
| **Open source** (Llama, Mistral) | Cost control, but requires hosting |

**Recommendation**: Start with OpenAI or Anthropic. Build abstraction layer to switch later.

```python
class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str: ...
    def stream_complete(self, prompt: str) -> Iterator[str]: ...
```

---

### 2. Basic Reference APIs (Nice to Have)

| API | Purpose | Priority |
|-----|---------|----------|
| **Holiday API** | Check if date is holiday in source/destination | P1 |
| **Time zone API** | Convert times for flights/transfers | P1 |
| **Weather API** | Seasonality packing hints | P2 |
| **Currency API** | Budget conversion if international | P2 |

**Cost**: All have free tiers sufficient for MVP.

---

## What You DON'T Need (Yet)

### Booking APIs (Amadeus, Sabre, GDS)

| Why not to integrate | Counter-argument |
|----------------------|------------------|
| Complex certification | ― |
| Rate limits | ― |
| Cost per call | ― |
| Agencies already have access | They know how to book |
| You'd be rebuilding existing tools | Focus on planning gap |

**Decision**: Don't integrate booking APIs for MVP.

Let agents handle booking. They're experts at it. You're solving the planning problem.

---

### Agency CRM Integration

| Why not | When to consider |
|---------|------------------|
| Most small agencies don't use CRM | When 10+ customers request it |
| Every CRM is different | Focus on standalone value first |
| Integration is complex | Build export/import instead |

**Alternative**: Simple CSV export/import, not real-time sync.

---

### WhatsApp Business API

| Why not | MVP alternative |
|---------|-----------------|
| Requires business verification | Manual copy-paste |
| Ongoing costs | Free for everyone |
| Complex setup | Works immediately |

**Decision**: Manual WhatsApp workflow for MVP (already covered in UX docs).

---

## Integration Philosophy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  INTEGRATION DECISION TREE                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Should I integrate X?                                                            │
│                                                                                  │
│  1. Does it solve a problem users ACTUALLY have?                                 │
│     No → Don't integrate                                                          │
│     Yes → Continue                                                                │
│                                                                                  │
│  2. Can users solve it themselves easily?                                         │
│     Yes → Don't integrate (let them do it)                                       │
│     No → Continue                                                                 │
│                                                                                  │
│  3. Is there a free/cheap API?                                                   │
│     No → Defer until revenue justifies cost                                      │
│     Yes → Consider                                                                │
│                                                                                  │
│  4. Will this integration break if the service changes?                          │
│     Yes → Build abstraction layer, have fallback                                 │
│     No → Proceed                                                                  │
│                                                                                  │
│  5. Can I build a simple version myself?                                         │
│     Yes → Do that instead of integrating                                         │
│     No → Integrate                                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Specific APIs to Consider

### For Feasibility Checks

| API | Use case | Free tier | Recommendation |
|-----|----------|-----------|----------------|
| **Calendarific** | Holidays by country | 10,000 requests/month | Use for MVP |
| **GeoNames** | Timezones, locations | Free (with credit) | Use for MVP |
| **OpenMeteo** | Weather data | Free, no key required | Use if needed |
| **Open Exchange Rates** | Currency conversion | 1,000 requests/month | Use if needed |

---

## Build vs. Integrate

### Example: Holiday Information

**Option A**: Integrate Calendarific API
- Pro: Accurate, always up-to-date
- Con: API dependency, rate limits

**Option B**: Build your own holiday database
- Pro: No dependency, fast
- Con: Maintenance burden, outdated eventually

**Option C**: Let LLM tell you (with caveats)
- Pro: No integration needed
- Con: May be wrong

**Recommendation**: Option A for MVP (simple API), fallback to Option B if needed.

---

## Data You Should Collect (Not Integrate)

Instead of integrating external data, collect it from usage:

| Data | How | Why |
|------|-----|-----|
| **Popular destinations** | Track trip destinations | Learn patterns |
| **Seasonal pricing** | Ask agents for budgets | Build knowledge base |
| **Common constraints** | Track constraints from trips | Improve extraction |
| **Feasibility patterns** | Track what works/doesn't | Better gate decisions |

**This becomes your proprietary data advantage.**

---

## Future Integrations (When You Have Demand)

### When Users Ask for These:

| Integration | Trigger to build |
|-------------|------------------|
| **HubSpot/Salesforce sync** | 10+ paying customers request it |
| **GDS integration** | Large agency partner requires it |
| **WhatsApp Business API** | You have 50+ users and want automation |
| **Google Calendar sync** | Multiple agencies request it |
| **Email integration** | "Send directly to traveler" feature demand |

**Principle**: Let users tell you what they need. Don't guess.

---

## Integration Architecture (If You Do It)

```python
# Abstraction layer for easy switching

class ExternalService(ABC):
    @abstractmethod
    async def fetch(self, params): ...

class HolidayService(ExternalService):
    def __init__(self, provider: str):
        if provider == "calendarific":
            self.client = CalendarificClient()
        elif provider == "database":
            self.client = HolidayDatabase()
        else:
            self.client = MockHolidayClient()

    async def fetch(self, country: str, date: date):
        return await self.client.get_holidays(country, date)

# Usage: easy to swap providers
holidays = HolidayService("calendarific")
# Later: holidays = HolidayService("database")
```

---

## Data Quality Over More Data

| Approach | Better for |
|----------|------------|
| **Few reliable sources** | Accuracy, trustworthiness |
| **Many scraped sources** | Coverage, but lower quality |

**Your brand depends on reliability.** One bad hallucination from a scraped source hurts more than missing info.

---

## Summary

**MVP integrations**:
1. LLM API (OpenAI or Anthropic)
2. Holiday API (Calendarific or similar)
3. Timezone API (GeoNames or similar)

**Don't integrate**:
- Booking APIs (GDS, Amadeus) — let agents handle
- CRM systems — build standalone value first
- WhatsApp API — manual workflow is fine

**Philosophy**: Every integration is debt. Only take on debt when it enables clear value.

**Later**: Let customer demand drive integration roadmap.

---

## Quick Decision Matrix

| Integration | Need for MVP? | Why/Why not |
|-------------|---------------|-------------|
| OpenAI API | ✅ Yes | Core functionality |
| Holiday API | ✅ Yes | Feasibility checks |
| GDS/Amadeus | ❌ No | Agents handle booking |
| HubSpot | ❌ No | Few agencies use it |
| WhatsApp API | ❌ No | Manual is fine for MVP |
| Calendar API | ❌ No | Nice to have, not core |
| Weather API | ⏸️ Maybe | Seasonality hints, P2 |
| Currency API | ⏸️ Maybe | International trips, P2 |
