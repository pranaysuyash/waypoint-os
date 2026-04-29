# Environment Management — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, need dev/staging/prod+  
**Approach:** Independent analysis — minimum viable env setup  

---

## 1. The Core Truth: You Need 3 Environments+

### Your Reality (Solo Dev))

| Environment | Purpose | Cost |
|-------------|---------|------|
| **Dev (localhost)** | Test new features | ₹0 (your laptop) |
| **Staging (Railway preview)** | Test before prod | FREE (Vercel preview) |
| **Production (Live)** | Customers use it | ₹500/month |

**My insight:**   
As solo dev, **dev + prod** might be enough.   
Staging = **nice-to-have**, not mandatory.

---

## 2. My Environment Model (Lean, Practical))

### What Env Vars You Actually Need+

```bash
# .env.example (template for ALL environments)
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==
# Environment: DEV | STAGING | PROD
# == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# Core
NODE_ENV=development  # development | staging | production
NEXT_PUBLIC_APP_URL=http://localhost:3000  # Auto-set in prod
API_BASE_URL=http://localhost:8000

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost:5432/travel_agency_dev
# Production: postgresql://user:pass@prod-host:5432/travel_agency

# WhatsApp Business API
WHATSAPP_API_KEY=your_meta_api_key
WHATSAPP_PHONE_ID=your_phone_number_id
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret

# Encryption (CRITICAL)
ENCRYPTION_KEY=32_char_random_string  # openssl rand -hex 16
# KEEP THIS SAFE! Lose it = ALL PII unreadable

# AWS S3 (Backups)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=my-agency-backups

# Google Calendar (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Session (NextAuth.js)
NEXTAUTH_SECRET=32_char_random_string  # openssl rand -hex 16
NEXTAUTH_URL=http://localhost:3000

# Vercel (Frontend Prod)
VERCEL_ORG_ID=your_org_id
VERCEL_PROJECT_ID=your_project_id
VERCEL_TOKEN=your_vercel_token

# Railway (Backend Prod)
RAILWAY_TOKEN=your_railway_token
```

**My insight:**   
`ENCRYPTION_KEY` = MOST CRITICAL. Store in **password manager**, not just `.env`.   
`DATABASE_URL` = different for each env (dev/staging/prod).

---

### Environment-Specific Files+

```bash
# .env.development (auto-loaded by Next.js)
NODE_ENV=development
DATABASE_URL=postgresql://user:pass@localhost:5432/travel_agency_dev
NEXT_PUBLIC_APP_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
ENCRYPTION_KEY=dev_only_key_not_for_prod

# .env.staging (Railway)
NODE_ENV=staging
DATABASE_URL=postgresql://user:pass@staging-host:5432/travel_agency_staging
NEXT_PUBLIC_APP_URL=https://staging.yourname-travels.com
API_BASE_URL=https://api-staging.yourname-travels.com

# .env.production (Railway - set via dashboard)
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@prod-host:5432/travel_agency
NEXT_PUBLIC_APP_URL=https://yourname-travels.com
API_BASE_URL=https://api.yourname-travels.com
ENCRYPTION_KEY=REAL_32_char_production_key
```

**My insight:**   
Next.js auto-loads `.env.local`, `.env.development`, etc.   
Railway/Vercel = set env vars in **dashboard**, not files.

---

## 3. Environment Promotion (How Code Moves)+

### Simple Flow (Solo Dev))+

```
localhost (dev)
  ↓ (git push)
GitHub (main branch)
  ↓ (auto-deploy)
Vercel/Railway (staging preview)
  ↓ (manual promote)
Vercel/Railway (production)
```

### GitHub Actions (Auto-Deploy))+

```yaml
# .github/workflows/deploy.yml
name: Deploy to Staging

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # 1. Run tests (MUST pass)
      - name: Run tests
        run: |
          cd spine_api && python -m pytest tests/
          cd frontend && npm test
      
      # 2. Deploy to Railway (backend)
      - name: Deploy Backend
        uses: railway-deploy@v2
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: travel-agency-backend
      
      # 3. Deploy to Vercel (frontend)
      - name: Deploy Frontend
        uses: vercel-deploy@v3
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
```

**My insight:**   
Tests MUST pass before deploy.   
`secrets.RAILWAY_TOKEN` = set in GitHub repo settings (Settings → Secrets).

---

## 4. Secrets Management (CRITICAL))+

### What NOT to Do+

| Action | Why NOT |
|--------|---------|
| ❌ Commit `.env` to git | API keys → PUBLIC on GitHub |
| ❌ Share `.env` via WhatsApp | End-to-end encrypted, but still risky |
| ❌ Store in code | ANYONE with code = has keys |
| ❌ Use same key for dev/prod | Dev leak = prod compromised |

### What to Do+

| Action | Why |
|--------|-----|
| ✅ `.gitignore` | NEVER commit secrets |
| ✅ GitHub Secrets | For CI/CD (encrypted at rest) |
| ✅ Railway/Vercel Dashboard | For production env vars |
| ✅ Password Manager | Store `ENCRYPTION_KEY` (1Password, etc.) |
| ✅ Different keys per env | Dev leak ≠ prod leak |

**My insight:**   
`ENCRYPTION_KEY` = store in **1Password/Fewer** (not just dashboard).   
If GitHub Secrets + Railway both have it = REDUNDANCY.

---

### How to Generate Secure Keys+

```bash
# ENCRYPTION_KEY (32 chars = 256-bit)
openssl rand -hex 16  # Output: a1b2c3d4e5f67890a1b2c3d4e5f67890

# NEXTAUTH_SECRET (32 chars)
openssl rand -hex 16

# WHATSAPP_API_KEY (from Meta)
# Get from: https://business.facebook.com/settings/
# Path: WhatsApp Business API → API Setup → Show Key

# AWS Keys (from AWS Console)
# Get from: https://console.aws.amazon.com/iam/home#/security_credentials
# Create new access key → Download CSV

# Store all in 1Password:
# Vault: "Travel Agency"
#   - ENCRYPTION_KEY: a1b2c3d4e5f67890a1b2c3d4e5f67890
#   - NEXTAUTH_SECRET: f0e1d2c3b4a567890f0e1d2c3b4a5678
#   - RAILWAY_TOKEN: your_railway_token
```

**My insight:**   
`openssl rand -hex 16` = 1 second to generate.   
Store in **1Password** = accessible from anywhere.

---

## 5. Current State vs Environment Model+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Environmets | Dev only (localhost) | Dev + Prod (staging = nice-to-have) |
| Env vars | `.env` (dev only) | `.env.example` + Railway/Vercel dashboard |
| Secrets mgmt | None | GitHub Secrets + 1Password |
| CI/CD | None | GitHub Actions (auto-deploy) |
| Promotion | Manual | Git push → auto-deploy |

---

## 6. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Staging env? | Yes / No | **NO** — dev + prod only |
| GitHub Actions? | Now / Later | **Now** — auto-deploy after tests |
| Secrets manager? | 1Password / Vault / Dashboard | **1Password** — solo dev, ₹0/month |
| Different DB per env? | Yes / No | **YES** — dev ≠ prod data |
| Auto-deploy? | Yes / Manual | **YES** — git push = live |

---

## 7. Next Discussion: CI/CD Pipeline+

Now that we know **HOW code moves**, we need to discuss: **HOW to automate?**

Key questions for next discussion:
1. **GitHub Actions** — which workflows? (test, deploy, backup?)
2. **Testing in CI** — run pytest + npm test?
3. **Deployment order** — backend first, then frontend?
4. **Rollback** — how to revert if broken?
5. **Solo dev reality** — what's the MINIMUM CI/CD?

---

**Next file:** `Docs/discussions/ci_cd_pipeline_2026-04-29.md`
