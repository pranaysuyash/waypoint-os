# Risk Analysis

**Date**: 2026-04-14
**Purpose**: What could go wrong and how to sleep at night

---

## Solo Builder Risk Management

> "You can't eliminate risk, but you can think about it in advance."

---

## Category 1: Technology Risks

### Risk: OpenAI/Anthropic API Goes Down

**Likelihood**: Low (they have good uptime)
**Impact**: High (your app doesn't work)

**Mitigation**:
```python
# 1. Retry with exponential backoff
# 2. Fallback to alternative provider (have API keys ready)
# 3. Cache common queries
# 4. Graceful degradation: "We're experiencing issues, try again later"
```

**Action before launch**: Have alternative API keys ready, test fallback

---

### Risk: LLM Hallucinates Bad Advice

**Likelihood**: Medium
**Impact**: High (if traveler acts on it)

**Mitigation**:
- Source envelope on every suggestion
- Never let LLM output go directly to traveler
- Human agent always reviews
- Clear disclaimer: "AI-generated, verify before booking"

**Already in design**: Traveler-safe boundary, source envelope

---

### Risk: OpenAI Raises Prices Dramatically

**Likelihood**: Low-Medium
**Impact**: Medium (margin compression, might need to raise prices)

**Mitigation**:
```python
# Build abstraction layer
class LLMProvider:
    def complete(self, prompt):
        # Can switch providers without changing app code
        pass
```

**Action before launch**: Implement provider abstraction, test with multiple providers

---

### Risk: Database Corruption or Data Loss

**Likelihood**: Very Low (Postgres is reliable)
**Impact**: Catastrophic

**Mitigation**:
- Daily automated backups (Render provides)
- Weekly export to external storage (R2/S3)
- Test restore process

**Action before launch**: Set up backups, test restore once

---

## Category 2: Business Risks

### Risk: No One Pays

**Likelihood**: Medium (common for startups)
**Impact**: Existential

**Early warning signs**:
- Design partners won't commit to weekly usage
- Lots of interest but no one wants to pay after free trial
- "This is great, I'll use it later" (procrastination = no)

**Mitigation**:
- Start charging early (even 50% off)
- Talk to users weekly
- If no one pays after 20 design partners → pivot or persevere?

---

### Risk: Customer Acquisition Cost > Lifetime Value

**Likelihood**: High initially
**Impact**: You burn money

**Example math**:
```
CAC = ₹500 (Facebook ads)
LTV = ₹1,000 × 6 months = ₹6,000
LTV/CAC = 12x → Good!

But if:
CAC = ₹2,000 (content takes time)
LTV = ₹1,000 × 2 months (churn) = ₹2,000
LTV/CAC = 1x → Bad
```

**Mitigation**:
- Focus on organic channels first (Facebook groups, word of mouth)
- Improve retention before scaling acquisition
- Monitor unit economics weekly

---

### Risk: Big Player Launches Similar Feature

**Likelihood**: Medium (Google, OpenAI could add "travel agent mode")
**Impact**: Medium-High

**Your defense**:
- You have agency-specific workflow
- You have relationships with early customers
- You move faster than big companies
- You're not generic — you're specialized

**Reality**: If Google launches this, it validates the market. Focus on what they won't do: deep agency workflow.

---

## Category 3: Legal/Compliance Risks

### Risk: Agency Sues Over Bad Advice

**Likelihood**: Very Low (agencies understand they review output)
**Impact**: Medium (legal costs, reputation)

**Mitigation**:
- Clear terms: "We provide suggestions, agency makes final decisions"
- Source envelope on everything
- Agency reviews before sending to traveler
- Professional liability insurance (later, when revenue justifies)

**Action**: Strong disclaimer in TOS, clear UI about human review

---

### Risk: Data Privacy Violation

**Likelihood**: Low-Medium
**Impact**: Medium (fines, reputation)

**Mitigation**:
- Minimize data collection (only what you need)
- Encrypt data at rest and in transit
- Clear data ownership: agency owns their data
- Data deletion on request
- GDPR-compliant if you have EU customers

**Action before launch**: Basic privacy policy, data deletion endpoint

---

### Risk: Traveler Data Leaked

**Likelihood**: Low
**Impact**: High (reputation, legal)

**Mitigation**:
- Don't store sensitive data (passport numbers, payment info)
- Agencies control what they input
- HTTPS everywhere
- Regular security reviews

**Already in design**: Traveler sees filtered output only

---

## Category 4: Operational Risks

### Risk: You Get Sick or Burned Out

**Likelihood**: Medium
**Impact**: High (you're the business)

**Mitigation**:
- Document critical systems
- Have a "pause button" (can you stop features and keep running?)
- Set boundaries (see Support doc)
- Build for reliability > features

**Action**: Keep READMEs updated, don't skip sleep

---

### Risk: You Run Out of Money

**Likelihood**: Depends on your runway
**Impact**: Existential

**Mitigation**:
- Know your runway (months of savings)
- Have revenue targets
- Cut costs if needed
- Consider consulting/freelancing to extend runway

**Action**: Build financial model (separate doc)

---

## Risk: Can't Scale Technically

**Likelihood**: Low (modern scales well)
**Impact**: Medium (slow growth, bad UX)

**Mitigation**:
- Build on scalable stack (Postgres, hosted services)
- Monitor performance metrics
- Have scaling plan (when to add caching, workers, etc.)

**Already covered**: Technical Infrastructure doc

---

## Category 5: Product Risks

### Risk: Product Doesn't Solve Real Problem

**Likelihood**: Medium (most startups fail here)
**Impact**: High

**Early warning signs**:
- Low activation rate (< 20%)
- Low weekly active (< 30%)
- High churn (> 20%/month)
- Users say "cool but I don't use it"

**Mitigation**:
- Talk to users weekly
- Ship features they request
- Be willing to pivot based on feedback
- Focus on one problem and nail it

---

### Risk: Feature Creep

**Likelihood**: High (common trap)
**Impact**: Medium (slower progress, bloat)

**Mitigation**:
- Have a "no" list
- Every feature must solve a real user problem
- Measure feature usage, remove unused ones

**Questions to ask before building**:
- Did a user request this?
- Will this increase retention?
- Is this aligned with core value prop?

---

## Risk Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RISK PRIORITIZATION                                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  High Impact, High Likelihood → Handle NOW                                       │
│  ────────────────────────────────────────                                        │
│  • Product doesn't solve real problem                                            │
│  • No one pays (eventually)                                                     │
│  • You burn out                                                                  │
│                                                                                  │
│  High Impact, Low Likelihood → Plan for, monitor                                │
│  ────────────────────────────────────────────                                    │
│  • Data breach                                                                  │
│  • LLM hallucination causes incident                                            │
│  • Big player launches competitor                                               │
│                                                                                  │
│  Low Impact, Any Likelihood → Accept or ignore                                  │
│  ────────────────────────────────────────                                        │
│  • Minor bugs                                                                   │
│  • Feature requests from non-users                                              │
│  • Minor price changes from vendors                                             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Pre-Launch Checklist (Risk Edition)

| Risk | Mitigation | Done? |
|------|------------|-------|
| API goes down | Fallback provider, error handling | |
| Bad advice | Source envelope, human review | ✓ (in design) |
| Data loss | Daily backups, test restore | |
| No one pays | Start charging early, talk to users | |
| Legal issue | TOS, privacy policy, disclaimers | |
| You burn out | Set boundaries, document systems | |
| Can't scale | Scalable stack, monitoring | |

---

## Summary

**Highest priority risks**:
1. Product doesn't solve real problem → Talk to users, iterate
2. You burn out → Set boundaries, pace yourself
3. No one pays → Charge early, learn why

**Have a plan for**:
- API downtime (fallbacks)
- Data backup (automated + tested)
- Legal basics (TOS, privacy policy)

**Don't worry about**:
- Big competitors (you're faster, more focused)
- Every edge case (handle common ones first)

**Sleep at night knowing**: You've thought about the big risks, and you have mitigations in place.
