# UX Discovery Session - 2026-04-22

## Original Request

> "select next ux item to explore, existing or something we can add, use relevant or new skills"

Context: Travel agency agent workspace with existing features:
- Inbox with sorting/filtering
- Workspace panels (Intake, Packet, Decision, Strategy, Safety, Output, Feedback)
- Editable trip details with SmartCombobox
- Audit trail for changes
- Multi-currency budget support

Goal: Identify next high-impact UX feature to build

---

## Brand Context Discovered

### Original Inspiration
**Palantir for travel agencies**

This explains the current design direction:
- Dark theme (data-dense, serious, analytical)
- Information-rich displays
- Focus on data integrity and control
- Professional, not consumer-facing

### Business Goals (What Matters)
1. **Fast responses** → More customers served
2. **Efficiency** → Lower cost per booking
3. **Correctness** → Fewer mistakes, higher margins
4. **Growth** → Scale the agency

**Outcome**: Agencies want to grow big through better operations.

### Emotional Tone (Clarified)
**NOT just "user-friendly" — but REASSURING**

The system should make agents feel:
- Confident in their decisions
- Protected from mistakes
- Supported during panic moments (11 PM WhatsApp)
- In control of their workload

> "I see that as a negative" — The user rejected framing this as "user-wise" and emphasized **reassurance** as the key emotional goal.

### Visual References
- User: Open to exploration/research
- Current: Palantir-inspired dark aesthetic
- To explore: What patterns fit fast, efficient, reassuring travel agency software?

### Anti-Patterns Approach
- User: Wants discussion/exploration, not a fixed list
- Goal: Research and document what to avoid
- Approach: Explore what works in travel/CRM context

---

## Design Direction Synthesis

### Personality Words
Based on context:
1. **Precise** - Accurate data, no ambiguity
2. **Efficient** - Fast workflows, minimal friction
3. **Reassuring** - Agent feels supported and confident

### Aesthetic Approach
- **Palantir-inspired but for travel**: Dark, data-rich, serious but adapted
- **Not consumer travel**: No vacation photos, beach backgrounds
- **Not generic SaaS**: Avoid boring card grids, blue buttons
- **Not playful**: No excessive emojis or gamification

### Key Principles
1. **Speed without sacrifice**: Fast responses with accuracy
2. **Confidence through clarity**: Agent knows what's happening
3. **Protection from disaster**: Hard blockers, validation, guidance
4. **Calm during crisis**: Support for panic scenarios (11 PM WhatsApp)

---

## Next UX Feature Candidates

Based on persona scenarios and business goals:

### High Impact Options

| Feature | Persona Served | Business Impact | Reassurance Factor |
|---------|---------------|-----------------|-------------------|
| **Command Palette** | P1 (Solo Agent) | Speed (10x faster) | "I can find anything" |
| **Operational Dashboard** | P2 (Owner) | Visibility | "I know what's happening" |
| **Quality Indicators** | P2, P3 | Accuracy | "This quote is solid" |
| **Customer Profile Sidebar** | P1, P3 | Memory | "I remember this customer" |
| **Crisis Mode** | P1, S1-S2 | Trust | "I'm handling emergencies" |

### Priority Analysis

**1. Command Palette (Cmd+K)**
- Why: P1-S1 "11 PM WhatsApp panic" needs speed
- Pattern: Palantir, Linear, Slack - proven for power users
- Reassurance: Instant access to any action/trip
- Implementation: Global search + quick actions

**2. Quality/Confidence Indicators**
- Why: P2-S1 "Quote disaster", P3-S3 "Is this right?"
- Pattern: Visual confidence scoring (like Palantir's data quality)
- Reassurance: "This quote is 92% complete" - agent feels secure
- Implementation: Progress bars, completeness scores, validation badges

**3. Customer Profile/History Panel**
- Why: P1-S2 "Repeat customer forgot", P2-S2 "Agent who left"
- Pattern: CRM sidebars (HubSpot, Salesforce)
- Reassurance: "I know this customer's history"
- Implementation: Slide-out panel with trip history, preferences, notes

---

## Anti-Patterns to Explore & Avoid

### Research Needed

**Generic "AI Slop" Indicators**
- What makes interfaces look AI-generated?
- How to avoid "card grid + blue button + icon" pattern?

**Travel Industry Clichés**
- Stock vacation photos (beaches, palm trees)
- Consumer booking site patterns (search forms, carousels)
- Overly playful vacation vibes

**Enterprise Clutter**
- Dashboard overwhelm (too many metrics)
- Dense tables without hierarchy
- Notification spam

**False Confidence**
- Over-promising accuracy
- Hiding uncertainty
- Pretending AI is perfect

---

## Design Principles Draft

1. **Clarity Over Cleverness** - Agent must understand instantly
2. **Calm Over Exciting** - Reduce anxiety, don't add stimulation
3. **Precision Over Generality** - Specific information, not vague summaries
4. **Protection Over Freedom** - Hard barriers vs soft suggestions
5. **Speed Over Comprehensiveness** - Right info, right now, drill down later

---

## Open Questions

1. **Command Palette scope** - What actions? What search targets?
2. **Quality indicators** - What metrics? How to score?
3. **Customer data** - What to show in profile panel?
4. **Mobile support** - Do agents work on phones?
5. **Collaboration** - Multiple agents on same trip?

---

## Progress Tracker

| Step | Status | Document |
|------|--------|----------|
| Explore anti-patterns | ✅ Complete | `ANTI_PATTERNS_RESEARCH.md` |
| Feature deep-dive | ✅ Complete | `DESIGN_BRIEF_Command_Palette.md` |
| Visual exploration | ⏳ Pending | Design mockups needed |
| Validate with personas | ⏳ Pending | User review needed |

---

## Next Steps (Updated)

1. **Visual exploration** - Create design mockups for Command Palette
2. **Validate with personas** - Test design brief against P1-S1 "panic" scenario
3. **Implementation** - Build Command Palette MVP (Phase 1)

---

## Documentation Note

This is a living document. Update as we learn more.

---

## Related Documents

- `ANTI_PATTERNS_RESEARCH.md` - What to avoid in travel agency UX
- `DESIGN_BRIEF_Command_Palette.md` - Detailed Command Palette design
- `FEATURE_DOCUMENTATION.md` - Already-implemented features
- `IMPLEMENTATION_SUMMARY.md` - Quick reference for existing features
