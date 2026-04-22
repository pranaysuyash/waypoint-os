# Workspace Code Format Analysis

**Goal:** Choose a code format that balances uniqueness, memorability, and security

---

## Options Analysis

### Option A: 3-Part Hyphenated (e.g., `ABC-XYZ-786`)

```
Format: [WORD]-[WORD]-[NUMBER]
Example: SKY-FOX-786, TRIP-ONE-123
```

**Pros:**
- Easy to read over phone/on WhatsApp
- Memorability: Words stick better than random chars
- Clear segments: "sky fox seven eight six"
- Feels professional, not like a promo code

**Cons:**
- Word list required for generation
- Longer than pure random
- Possible unintended word combinations
- 3 words + number = harder to remember

**Uniqueness:** With 1000 words × 1000 words × 999 numbers = ~1B combinations

**Collisions:** Very low with proper random

---

### Option B: Prefix + Random (e.g., `agency-abc123`)

```
Format: [PREFIX]-[RANDOM]
Example: agency-xkq9m2, ws-pr7znl
```

**Pros:**
- Clearly indicates purpose (agency-*, ws-*)
- Shorter than word-based
- Easy to generate (no word list)
- Zero ambiguity in characters

**Cons:**
- Random chars are hard to remember
- Hard to communicate verbally ("was that m or n?")
- Feels technical, not user-friendly
- "agency-" prefix is redundant context

**Uniqueness:** With 36 chars (a-z0-9) × 6 length = ~2B combinations

**Collisions:** Very low with proper random

---

### Option C: UUID-Style (e.g., `abc123xyz`)

```
Format: [ALPHANUMERIC]
Example: 3k7mx9p2, q1z8x7k4
```

**Pros:**
- Shortest option
- No prefix overhead
- Standard format, recognizable

**Cons:**
- Hardest to communicate verbally
- Zero semantic meaning
- Feels like a temp password
- "Was that 1 or l? 0 or O?"

**Uniqueness:** With 36 chars × 8 length = ~2.8 trillion combinations

**Collisions:** Extremely low

---

### Option D: Phonetic + Digits (e.g., `TRI-789-PLY`)

```
Format: [SYLLABLE]-[DIGITS]-[SYLLABLE]
Example: TRI-789-PLY, VOY-234-GER
```

**Pros:**
- Phonetic syllables are pronounceable
- Digits in middle for break
- Travel-related syllables (TRI, VOY, TUR)
- Easy to say: "trip seven eight nine play"

**Cons:**
- Syllable list required
- Still somewhat abstract
- Limited syllable combinations

**Uniqueness:** With 100 syllables × 9999 digits × 100 syllables = ~1B combinations

**Collisions:** Very low

---

## Recommendation: Phonetic + Digits (Option D)

**Why:**
1. **Speakability:** "tri-seven-eight-nine-ply" is easy to communicate
2. **Branding:** Syllables can be travel-themed (TRI, VOY, TUR, DES, TIN)
3. **Balance:** Not too long, not too abstract
4. **Professional:** Feels like a workspace code, not a promo code

**Format:**
```
[SYLLABLE]-[4 DIGITS]-[SYLLABLE]
Examples:
- TRI-7892-PLY  (Trip)
- VOY-1234-GER  (Voyage)
- TUR-5678-NAT  (Tourist)
```

**Syllable palette (40 syllables):**
```
TRI, VOY, TUR, DES, TIN,      # Travel
JOU, RNY, RNE, EXL, SCP,      # Journey
SKY, SEA, LAN, MUN, CIT,      # Places
FLY, ROA, MAP, WAY, PTH,      # Movement
SIL, GLD, PLT, DIA, GEM,      # Values
WRL, GLO, ERR, ZNE, NOD,      # Space
```

---

## Code Types: Internal vs External

### Internal Agent Code
```
Format: [SYLLABLE]-[4 DIGITS]-[SYLLABLE]
Example: TRI-7892-PLY
Purpose: Full-time team members
Access: All trips, full workspace features
```

### External Agent Code
```
Format: EXT-[SYLLABLE]-[4 DIGITS]
Example: EXT-TRI-7892
Purpose: Vendors, contractors, part-time
Access: Limited to assigned trips only
```

**Why different?**
- Clear visual distinction in management
- External codes have "EXT" prefix for quick ID
- Easier to audit who's internal vs external
- Can set different permissions by code type

---

## Code Lifecycle

```
Generated → Shared → Agent Joins → Active → Agent Leaves → Reusable
```

| State | Description |
|-------|-------------|
| **Generated** | Created, not yet shared |
| **Shared** | Given to agent, not yet used |
| **Active** | Agent has joined and using |
| **Inactive** | Agent left/removed, code reusable |
| **Archived** | Code retired, won't be reused |

**Reuse policy:**
- When agent leaves, code marked "inactive"
- Admin can reactivate for new agent
- Or generate new code (fresh start)
- Code history tracked (who used, when)

---

## Uniqueness Guarantees

### Database Schema
```sql
CREATE TABLE workspace_codes (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  code VARCHAR(20) UNIQUE NOT NULL,
  code_type VARCHAR(10) NOT NULL,  -- 'internal' | 'external'
  status VARCHAR(20) NOT NULL,      -- 'generated' | 'shared' | 'active' | 'inactive'
  created_by UUID NOT NULL,         -- user who created
  created_at TIMESTAMP DEFAULT NOW(),
  used_by UUID,                     -- agent who used this code
  used_at TIMESTAMP,
  expires_at TIMESTAMP,             -- NULL = never expires

  UNIQUE(workspace_id, code)
);
```

### Collision Handling
```python
def generate_code(code_type: 'internal' | 'external') -> str:
    max_attempts = 5
    for _ in range(max_attempts):
        if code_type == 'internal':
            code = f"{random_syllable()}-{random_digits(4)}-{random_syllable()}"
        else:
            code = f"EXT-{random_syllable()}-{random_digits(4)}"

        if not code_exists(code):
            return code

    # Fallback: add timestamp suffix
    return f"{code}-{int(time.time()) % 1000}"
```

---

## Security Considerations

### What the code grants
| Code Type | Access Scope |
|-----------|--------------|
| Internal | Full workspace: all trips, team features, settings |
| External | Assigned trips only, no team management, no settings |

### Rate limiting
```python
# Prevent code guessing
MAX_SIGNUP_ATTEMPTS = 5 per IP per hour
MAX_CODE_ATTEMPTS = 10 per code per hour
```

### Audit logging
```python
# Track all code activity
{
  "event": "code_used",
  "code": "TRI-7892-PLY",
  "workspace_id": "abc-123",
  "new_agent_id": "user-456",
  "ip_address": "1.2.3.4",
  "timestamp": "2026-04-22T10:30:00Z"
}
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Format** | Phonetic + Digits: `SYLLABLE-4DIGITS-SYLLABLE` |
| **Internal example** | `TRI-7892-PLY` |
| **External example** | `EXT-TRI-7892` |
| **Expiration** | Never expires |
| **Reusability** | Reusable when agent leaves |
| **Uniqueness** | DB constraint + collision handling |
| **Syllables** | 40 travel-themed options |

---

**Status:** Code format decision made, ready for implementation brief
