# Onboarding — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, maybe someday hire help  
**Approach:** Independent analysis — onboarding for 1 person = overkill?  

---

## 1. The Core Truth: You're Solo, But MAYBE Not Forever**

### Your Reality (Solo Dev Today)

| Question | Answer for You Today | Future (If You Hire) |
|----------|----------------------|--------------------------|
| **How many agents?** | 1 (you) | 2-5 within 1 year |
| **Need onboarding?** | NO | YES — they need to learn |
| **Documentation?** | YOU know it | They DON'T know it |
| **SOPs?** | In your head | Written down |

**My insight:**  
Write onboarding docs **now** (while it's fresh in your head).  
6 months from now → you'll forget WHY you built X feature.

---

## 2. My Lean Onboarding Model (Just Docs)**

### What You Actually Need (Simple)**

```markdown
# ONBOARDING_GUIDE.md (in repo root)

## 1. First Login
- URL: http://localhost:3000
- Login with: [your credentials]
- Bookmark: Enquiries page

## 2. Daily Workflow (The 3 Things)
1. Check WhatsApp → new messages
2. Open enquiry → read AI summary
3. Reply within 4 hours (SLA)

## 3. Key Pages (Cheat Sheet)
- `/enquiries` → list all enquiries
- `/enquiries/[id]` → enquiry details
- `/bookings` → active bookings
- `/customers` → customer list

## 4. AI Assistance (How to Use)
- Click "Draft Reply" → AI generates first version
- Edit tone: Casual (leisure) / Formal (corporate)
- Send via WhatsApp → auto-logged in comms

## 5. Vendor Coordination
- Search vendor: "Bali hotel"
- Click "Request Quote" → auto-sends email/WhatsApp
- Mark reply: "Quote received" → updates enquiry

## 6. Payment Tracking (Status Only)
- Customer says "Paid ₹50k via UPI"
- Click "Mark as Paid" → logs payment_received
- Upload receipt screenshot → stores proof

## 7. Emergency Procedures
- VIP customer calls: Search name → open enquiry
- Vendor silent 24h: Click "Send Reminder"
- EMI overdue: Check notifications → call customer

## 8. Reports (Weekly)
- Visit `/analytics/revenue` → check this month's earnings
- Visit `/analytics/vendors` → who's performing?
- Export Excel → send to accountant
```

**My insight:**   
3-page `ONBOARDING_GUIDE.md` = enough for first hire.  
Keep it in **repo root** — always updated with code.

---

## 3. Tooltip System (In-App Hints)**

### What's Actually Useful (Minimal)**

```typescript
// components/Tooltip.tsx
// Show ONLY on first login

const tooltips = [
  {
    target: "[data-tour='enquiry-list']",
    title: "Your Enquiries",
    content: "All customer enquiries appear here. Click any to open details.",
    placement: "bottom"
  },
  {
    target: "[data-tour='draft-button']",
    title: "AI Draft",
    content: "Click to generate AI-assisted reply. Edit tone before sending.",
    placement: "top"
  },
  {
    target: "[data-tour='whatsapp-send']",
    title: "Send via WhatsApp",
    content: "Sends message + logs in communication history.",
    placement: "left"
  }
];

// Show only if: localStorage.getItem('tour_completed') !== 'true'
```

**My insight:**   
Tooltips = **annoying** if shown every time.  
Show ONLY on **first login** → `localStorage` flag.

---

## 4. Video Tutorials (Maybe Later)**

### When You MIGHT Need Videos**

| Situation | Need Video? | Alternative |
|-----------|--------------|-------------|
| **Hire first agent** | ✅ YES | 10-minute Loom recording |
| **Complex workflow** | 🟡 MAYBE | Screenshot + arrows |
| **Draft with AI** | ❌ NO | Tooltip is enough |
| **WhatsApp API** | ❌ NO | Written SOP in repo |

**My insight:**   
10-minute **Loom video** > 20-page manual.  
Record your screen: "This is how I reply to Ravi's Bali enquiry."

---

## 5. SOPs (Standard Operating Procedures)**

### What to Document (Critical Workflows)**

```markdown
# SOPs/ (folder in repo)

## SOP-001: New Enquiry Handling
1. Receive WhatsApp → system auto-creates enquiry
2. AI analyzes → status = TRIAGED
3. You review AI draft → edit tone
4. Send reply via WhatsApp
5. Mark as "DRAFT_SENT"

## SOP-002: Booking Confirmation
1. Customer agrees → mark enquiry as "CONFIRMED"
2. Create booking → enters `booking_reference`
3. Vendor confirms → upload voucher PDF
4. Send confirmation WhatsApp to customer

## SOP-003: Complaint Handling
1. Receive complaint → `enquiry_subtype = "complaint"`
2. Severity = HIGH → auto-alerts you
3. Contact vendor → negotiate solution
4. Send apology + solution → `comm_type = APOLOGY`
5. Mark resolved → check customer satisfaction

## SOP-004: Payment Tracking
1. Customer says "Paid" → ask for screenshot
2. Upload receipt → `receipt_url`
3. Verify amount → `paid_amount == agreed_amount`
4. Mark as "COMPLETED"

## SOP-005: EMI Follow-up
1. Check notifications daily → "EMI overdue?"
2. Call customer → "Why missed payment?"
3. Log call notes → `emi_tracking.notes`
4. Escalate if >2 overdue → `escalated_to_agent_id`
```

**My insight:**   
SOPs = your **insurance policy**.  
If you're hit by bus tomorrow → new agent can CONTINUE your business.

---

## 6. First Login Experience (New Agent)**

### What They Should See**

```typescript
// app/page.tsx (landing page for new agent)
export default function FirstLoginPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  
  const steps = [
    {
      title: "Welcome to Travel Agency OS!",
      content: "You're the new agent. Here's how to work.",
      action: null
    },
    {
      title: "Your Daily Workflow",
      content: "1. Check WhatsApp → 2. Open enquiry → 3. Reply within 4h",
      action: () => router.push('/enquiries')
    },
    {
      title: "Try AI Draft",
      content: "Open any enquiry → click 'Draft Reply' → AI helps!",
      action: () => router.push('/enquiries/demo')
    },
    {
      title: "You're Ready!",
      content: "Bookmark /enquiries. Start working!",
      action: () => {
        localStorage.setItem('tour_completed', 'true');
        router.push('/enquiries');
      }
    }
  ];
  
  return (
    <div className="max-w-lg mx-auto mt-20">
      <h1>{steps[step].title}</h1>
      <p>{steps[step].content}</p>
      {steps[step].action && (
        <Button onClick={steps[step].action}>
          Next →
        </Button>
      )}
      <Progress value={step + 1} max={steps.length} />
    </div>
  );
}
```

**My insight:**   
Tour = **3 minutes max**. Don't bore them with 20 slides.  
Let them START WORKING → learn by doing.

---

## 7. Current State vs Onboarding Model**

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Onboarding guide | None | `ONBOARDING_GUIDE.md` in repo |
| Tooltip system | None | 3 tooltips on first login |
| Video tutorials | None | Loom recording (if hire) |
| SOPs | None | `SOPs/` folder with 5 procedures |
| First login tour | None | 4-step wizard (3 minutes) |

---

## 8. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Write onboarding now? | Yes / No | **YES** — while it's fresh |
| Tooltip system? | Full / Minimal / None | **Minimal** — 3 tooltips |
| Video tutorials? | Yes / Later | **Later** — record when you hire |
| SOPs? | 5 / 20 / None | **5** — critical workflows only |
| First login tour? | Yes / No | **YES** — 3 minutes, then work |

---

## 9. Next Discussion: Performance & Scaling**

Now that we know **HOW to teach new agents**, we need to discuss: **What happens when system slows down?**

Key questions for next discussion:
1. **1000 enquiries** — will PostgreSQL handle it? (yes, easily)
2. **10000 enquiries** — need indexes? (yes, you need them)
3. **WhatsApp API rate limits** — 1000 msgs/day limit?
4. **File storage** — S3 costs for 10000 receipt PDFs?
5. **Solo dev reality** — will you EVER have 1000 enquiries? (maybe 100?)
6. **When to optimize** — pre-mature optimization vs. real need?

---

**Next file:** `Docs/discussions/performance_scaling_2026-04-29.md`
