# Feature Flags & Toggles — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, test features safely  
**Approach:** Independent analysis — minimum viable flags, not enterprise  

---

## 1. The Core Truth: You Need a Kill Switch+

### Your Reality (Solo Dev))

| Feature Launch | Without Flags | With Flags |
|-----------------|---------------|-------------------|
| **New AI model** | ❌ Deploy + hope | ✅ OFF by default, test |
| **WhatsApp API down** | ❌ Code change + deploy | ✅ Toggle OFF in 5s |
| **New draft UI** | ❌ All customers see it | ✅ VIP only first |
| **Bug in production** | ❌ Revert + deploy | ✅ Toggle OFF in 5s |

**My insight:**   
As solo dev, **flags = insurance policy**.   
Toggle in 5s > revert + deploy (30 mins).

---

## 2. My Feature Flag Model (Lean, Practical))+

### What You Actually Need (Simple))+

```json+
{
  "feature_flags": {
    "ai_draft_v2": {
      "enabled": false,  // OFF by default+
      "enabled_for": ["VIP", "INTERNAL"],  // Only these see it+
      "rollout_percentage": 0,  // 0% see it+
      "kill_switch": false,  // Emergency OFF+
      "description": "New AI model with GPT-4o"
    },
    "whatsapp_priority": {
      "enabled": true,  // ON+
      "kill_switch": false,
      "description": "WhatsApp is primary channel"
    },
    "new_booking_ui": {
      "enabled": false,
      "enabled_for": ["INTERNAL"],  // YOU test first+
      "rollout_percentage": 0,
      "description": "New booking form UI"
    },
    "bulk_email": {
      "enabled": false,  // OFF (not ready)+
      "kill_switch": true,  // Force OFF+
      "description": "Bulk email to customers (unused)"
    }
  }
}
```

**My insight:**   
`kill_switch: true` = force OFF (emergency).   
`enabled_for: ["VIP"]` = test on YOUR best customers.

---

### Storage (Simple JSON File))+

```json+
// config/feature_flags.json (in repo, commit it!)
{
  "ai_draft_v2": { "enabled": false, "enabled_for": ["INTERNAL"] },
  "new_booking_ui": { "enabled": false, "enabled_for": ["INTERNAL"] }
}

# .gitignore: ❌ DON'T gitignore this!
# Commit flags file (version controlled)
```

**My insight:**   
Commit `feature_flags.json` = version controlled.   
See WHEN you turned feature ON (git blame).

---

## 3. Backend: Check Flag (FastAPI))+

### How to Check (5 Lines))+

```python+
# spine_api/utils/feature_flags.py+
import json+
from pathlib import Path+

FLAGS_FILE = Path(__file__).parent.parent / "config" / "feature_flags.json"

def is_enabled(feature_name: str, user_role: str = "INTERNAL") -> bool:
    """Check if feature is enabled for this user."""
    try:
        with open(FLAGS_FILE) as f:
            flags = json.load(f)
        
        flag = flags.get(feature_name, {})
        
        # Kill switch = force OFF+
        if flag.get("kill_switch", False):
            return False
        
        # Check if enabled+
        if not flag.get("enabled", False):
            return False
        
        # Check user role+
        enabled_for = flag.get("enabled_for", [])
        if "ALL" in enabled_for or user_role in enabled_for:
            return True
        
        # Check rollout % (later)+
        return False
        
    except:
        return False  # Fail safe: feature OFF+

# Usage in endpoint:
@app.post("/api/enquiries/{id}/draft")
async def generate_draft(enquiry_id: str, user: dict = Depends(get_current_user)):
    if is_enabled("ai_draft_v2", user.get("role", "INTERNAL")):
        draft = generate_with_gpt4o(enquiry_id)
    else:
        draft = generate_with_gpt35(enquiry_id)
    return {"draft": draft}
```

**My insight:**   
`Fail safe: return False` = feature OFF if file missing.   
`user_role` = "INTERNAL" (you) or "VIP" (customer).

---

## 4. Frontend: Check Flag (Next.js))+

### How to Check (5 Lines))+

```typescript+
// lib/featureFlags.ts+
import { getSession } from "next-auth/react";

export function isEnabled(featureName: string): boolean {
  const flags = (window as any).FEATURE_FLAGS || {}
  const session = getSession()
  const userRole = (session?.user as any)?.role || "INTERNAL"
  
  const flag = flags[featureName]
  if (!flag) return false
  
  // Kill switch+
  if (flag.kill_switch) return false
  
  // Check if enabled+
  if (!flag.enabled) return false
  
  // Check user role+
  if (flag.enabled_for?.includes("ALL") || flag.enabled_for?.includes(userRole)) {
    return true
  }
  
  return false+
}

// Usage in component:
import { isEnabled } from "@/lib/featureFlags"

export function DraftButton({ enquiryId }: { enquiryId: string }) {
  if (!isEnabled("ai_draft_v2")) {
    return <button>Old Draft →</button>
  }
  
  return <button>New AI Draft v2 →</button>
}
```

**My insight:**   
`(window as any).FEATURE_FLAGS` = set on page load.   
Check in 5 lines = zero overhead.

---

### Inject Flags (On Page Load))+

```typescript+
// app/layout.tsx+
import { getSession } from "next-auth/react"

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession()
  
  useEffect(() => {
    // Fetch flags on load+
    fetch('/api/feature-flags')
      .then(res => res.json())
      .then(flags => {
        (window as any).FEATURE_FLAGS = flags+
      })
  }, [])
  
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

**My insight:**   
Set on `window` = accessible everywhere.   
Fetch once on load = no per-page overhead.

---

## 5. API: Get Flags (Simple))+

```python+
# spine_api/routes/feature_flags.py+
from fastapi import APIRouter+
import json+
from pathlib import Path+

router = APIRouter()

@router.get("/api/feature-flags")
async def get_flags():
    """Return flags for frontend."""
    flags_file = Path(__file__).parent.parent / "config" / "feature_flags.json"
    try:
        with open(flags_file) as f:
            return json.load(f)
    except:
        return {}  # Fail safe: no flags+
```

**My insight:**   
Frontend fetches ONCE on load.   
If file missing = empty object = all features OFF.

---

## 6. Toggle UI (For You Only))+

### Simple Toggle Page (5 Mins))+

```typescript+
// app/admin/feature-flags/page.tsx+
import { useState } from "react"
import { getSession } from "next-auth/react"

export default function FeatureFlagsAdmin() {
  const { data: session } = useSession()
  const [flags, setFlags] = useState<Record<string, any>>({})
  
  // Only YOU can access+
  if (session?.user?.role !== "OWNER") {
    return <p>Access denied 🔒</p>
  }
  
  const toggleFlag = async (name: string) => {
    const updated = {
      ...flags,
      [name]: { ...flags[name], enabled: !flags[name].enabled }
    }
    setFlags(updated)
    
    // Save to backend+
    await fetch('/api/admin/feature-flags', {
      method: 'POST',
      body: JSON.stringify(flags)
    })
  }
  
  return (
    <div className="max-w-lg mx-auto mt-20">
      <h1>Feature Flags 🎛️</h1>
      {Object.entries(flags).map(([name, config]) => (
        <div key={name} className="flex justify-between p-4 border-b">
          <span>{name}</span>
          <button
            onClick={() => toggleFlag(name)}
            className={config.enabled ? "bg-green-500" : "bg-gray-300"}
          >
            {config.enabled ? "ON ✅" : "OFF ❌"}
          </button>
        </div>
      ))}
    </div>
  )
}
```

**My insight:**   
Only YOU (role: "OWNER") can access.   
Toggle in 1 click = no deploy needed.

---

## 7. Current State vs Feature Flag Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Feature flags | None | `config/feature_flags.json` (committed) |
| Backend check | None | `is_enabled()` (5 lines) |
| Frontend check | None | `isEnabled()` (5 lines) |
| Toggle UI | None | `/admin/feature-flags` (YOU only) |
| Kill switch | None | `kill_switch: true` (force OFF) |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Feature flags now? | Yes / No | **YES** — 5 mins, saves hours |
| Config file? | JSON / env vars | **JSON** — no redeploy |
| Toggle UI? | Yes / No | **YES** — 5 mins, YOU only |
| Kill switch? | Yes / No | **YES** — emergency OFF |
| Rollout %? | Now / Later | **LATER** — start simple |

---

## 9. Next Discussion: **FINAL IMPLEMENTATION ROADMAP**+

Now that we know **HOW to toggle features**, we need to write: **The LIVING Implementation Roadmap tying ALL 37+ discussions together!**

This is the **BIG document** you asked for earlier: "write it, keep it living"

**Next file:** `Docs/discussions/implementation_roadmap_2026-04-29.md` (THE BIG ONE)
