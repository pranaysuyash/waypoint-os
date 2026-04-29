# Session Management — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, NextAuth.js+  
**Approach:** Independent analysis — minimum viable session, not enterprise  

---

## 1. The Core Truth: Sessions Expire, People Forget+

### Your Reality (Solo Dev))

| Scenario | Without Session Mgmt | With Session Mgmt |
|----------|-----------------------|-------------------|
| **JWT expires (1h)** | ❌ YOU get logged out | ✅ Auto-refresh |
| **Tab closed 8h** | ❌ Need to login again | ✅ Persisted session |
| **Different browser** | ❌ New login needed | ✅ Session cookie |
| **Logout** | ❌ JWT still valid | ✅ Server-side revoke |

**My insight:**   
NextAuth.js = **built-in session**. Zero work for you.   
JWT expiry = **security** (not convenience).

---

## 2. My Session Model (Lean, NextAuth.js))+

### What You Actually Need (Simple))+

```typescript+
// [...nextauth].ts (already exists, verify config)
import NextAuth from "next-auth";
import JwtStrategy from "next-auth/jwt";

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",  // JWT in cookie (no DB session table)
    maxAge: 30 * 24 * 60 * 60,  // 30 days (YOU stay logged in)
  },
  jwt: {
    secret: process.env.NEXTAUTH_SECRET!,
    maxAge: 30 * 24 * 60 * 60,  // 30 days
  },
  providers: [
    CredentialsProvider({
      name: "YOU (solo dev)",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // 1. Check against YOUR creds (env var or DB)
        if (
          credentials.username === process.env.ADMIN_USERNAME &&
          await compare(password, process.env.ADMIN_HASHED_PASSWORD!)
        ) {
          return {
            id: "you",
            name: "Ravi (Agency Owner)",
            email: "hello@your-agency.com",
            role: "OWNER"
          };
        }
        return null;
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    }
  }
};

export default NextAuth(authOptions);
```

**My insight:**   
`strategy: "jwt"` = NO session table needed.   
`maxAge: 30 days` = YOU stay logged in (solo dev = convenience).

---

### Login Page (Simple, 1 Minute)+

```typescript+
// app/login/page.tsx+
import { signIn } from "next-auth/react";
import { useState } from "react";

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget as HTMLFormElement);
    
    const res = await signIn("credentials", {
      username: formData.get("username"),
      password: formData.get("password"),
      redirect: false
    });
    
    if (res?.error) {
      setError("Invalid username or password");
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-6 border rounded">
      <h1>Login to Travel Agency OS</h1>
      <form onSubmit={handleSubmit}>
        <input name="username" placeholder="Username" className="w-full mb-2 p-2 border" />
        <input name="password" type="password" placeholder="Password" className="w-full mb-2 p-2 border" />
        <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">
          Login →
        </button>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </form>
    </div>
  );
}
```

**My insight:**   
`redirect: false` = show error on SAME page.   
Tell YOU the error ("Invalid username...").

---

## 3. JWT Structure (What's Inside))+

### What You Get (NextAuth.js Default))+

```typescript+
// When user logs in, JWT contains:
{
  "sub": "you",  // user ID
  "name": "Ravi (Agency Owner)",
  "email": "hello@your-agency.com",
  "role": "OWNER",
  "iat": 1714387200,  // Issued at (timestamp)
  "exp": 1716989200   // Expires (30 days later)
}

// Frontend: useSession()
const { data: session } = useSession();
console.log(session?.user?.name);  // "Ravi..."
console.log(session?.user?.role);  // "OWNER"
```

**My insight:**   
`exp: 1716989200` = auto-expires in 30 days.   
`useSession()` = React hook, always up-to-date.

---

### Backend: Verify JWT (FastAPI))+

```python+
# spine_api/core/auth.py+
from fastapi import Depends, HTTPException+
from fastapi.security import HTTPBearer+
from jose import jwt+
from jose.exceptions import JWTError+

bearer_scheme = HTTPBearer()

async def get_current_user(token: str = Depends(bearer_scheme)):
    """Verify JWT from NextAuth.js."""
    try:
        # NextAuth uses NEXTAUTH_SECRET+
        payload = jwt.decode(
            token,
            "your-32-char-secret",  # process.env.NEXTAUTH_SECRET+
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Usage in endpoints:
@app.get("/api/enquiries")
async def get_enquiries(user: dict = Depends(get_current_user)):
    # user['sub'] = "you"
    # user['role'] = "OWNER"
    return db.get_enquiries()
```

**My insight:**   
NextAuth secret = **same for FastAPI**.   
`Depends(get_current_user)` = auto-verifies on every call. 

---

## 4. Session Expiry Handling (Frontend))+

### What User Sees (Graceful))+

```typescript+
// components/SessionWatcher.tsx+
import { signOut, getSession } from "next-auth/react";
import { useEffect, useState } from "react";

export function SessionWatcher() {
  const { data: session } = useSession();
  const [showExpiryWarning, setShowExpiryWarning] = useState(false);

  useEffect(() => {
    if (!session) return;

    // Check expiry every 60s+
    const interval = setInterval(async () => {
      const session = await getSession();
      if (!session) {
        // JWT expired+
        signOut();  // Force re-login+
        window.location.href = "/login?expired=1";
      }
    }, 60_000);

    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {showExpiryWarning && (
        <div className="fixed bottom-4 right-4 bg-yellow-100 p-4 rounded shadow">
          <p>⚠️ Session expiring soon!</p>
          <button onClick={() => signOut()}>Re-login →</button>
        </div>
      )}
    </>
  );
}

// Layout (wrap app):
<SessionWatcher />
{children}
```

**My insight:**   
`signOut()` = clears JWT cookie.   
`/login?expired=1` = show "Session expired" message. 

---

### Backend: Expiry Check (FastAPI))+

```python+
# spine_api/core/auth.py+
from datetime import datetime, timezone+

async def check_session_expiry(token: dict):
    """Check if JWT is about to expire."""
    exp = token.get("exp")
    if not exp:
        return True  # No expiry = invalid+

    now = datetime.now(timezone.utc).timestamp()
    seconds_left = exp - now+

    if seconds_left < 300:  # 5 minutes+
        # Tell frontend: "refresh soon!"
        return False  # Expiring soon+
    return True

# Usage in endpoints:
@app.get("/api/enquiries")
async def get_enquiries(user: dict = Depends(get_current_user)):
    if not check_session_expiry(user):
        # Add header: X-Session-Expiring: true+
        pass  # Frontend can show warning+
    return db.get_enquiries()
```

**My insight:**   
`seconds_left < 300` = warn frontend.   
NextAuth.js auto-refreshes (built-in). 

---

## 5. Refresh Token Strategy (NextAuth.js Handles It))+

### How It Works (Zero Work for You))+

| Concept | Without Refresh | With Refresh (NextAuth))+
|---------|-------------------|-----------------------------|
| **JWT expires (1h)** | ❌ YOU get logged out | ✅ Auto-refreshed |
| **Tab closed 8h** | ❌ Need to login again | ✅ Persisted session |
| **Implementation** | Write refresh logic | ✅ Built-in (0 mins) |

**My insight:**   
NextAuth.js = **auto-refresh**. You do NOTHING.   
Session cookie = persists across tabs. 

---

## 6. Logout (Clear Session))+

### Frontend: signOut()+

```typescript+
// components/LogoutButton.tsx+
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();

  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push("/login?logged_out=1");
  };

  return (
    <button onClick={handleLogout} className="text-red-500">
      Logout →
    </button>
  );
}
```

### Backend: Revoke (Optional, Later))+

```python+
# spine_api/core/auth.py+
# JWT is stateless (no server-side session store)+
# Logout = frontend deletes cookie+
# Optionally: add token to blacklist (Redis) if you want server-side revoke+

# Later (if needed):
# redis_client.sadd("blacklisted_tokens", token['jti'])
# Then check in get_current_user()+
```

**My insight:**   
JWT = **stateless**. Logout = delete cookie.   
Server-side revoke = **Redis** (later, not needed now). 

---

## 7. Current State vs Session Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Session strategy | None (NextAuth setup?) | JWT (no DB session table) |
| JWT expiry | None | 30 days (solo dev convenience) |
| Refresh token | None | NextAuth built-in (auto) |
| Frontend watcher | None | `SessionWatcher` (warn if expiring) |
| Backend verify | None | `Depends(get_current_user)` on all endpoints |
| Logout | None | `signOut()` (clears cookie) |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Session strategy? | JWT / DB Sessions | **JWT** — zero DB table |
| Expiry time? | 1h / 24h / 30 days | **30 days** — solo dev convenience |
| Session watcher? | Yes / No | **YES** — warn if expiring |
| Server-side revoke? | Now / Later | **Later** — JWT is enough |
| Refresh token? | Manual / Auto | **Auto** — NextAuth built-in |

---

## 9. Next Discussion: Rate Limiting+

Now that we know **HOW sessions work**, we need to discuss: **How to protect APIs?**

Key questions for next discussion:
1. **Rate limit on backend** — 100 req/min? (protect from abuse)
2. **Rate limit on WhatsApp API** — 1000 msgs/day (Meta limit)
3. **Per-user vs per-IP** — limit YOU vs customer?
4. **Burst handling** — allow 20 req/sec for 5s?
5. **Solo dev reality** — will anyone attack you? (maybe not, but safe)

---

**Next file:** `Docs/discussions/rate_limiting_2026-04-29.md`
