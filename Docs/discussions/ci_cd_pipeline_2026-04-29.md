# CI/CD Pipeline — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, automate deployment+  
**Approach:** Independent analysis — minimum viable CI/CD, not enterprise  

---

## 1. The Core Truth: You're Solo, But Need Automation+

### Your Reality (Solo Dev))

| Task | Manual | Automated (GitHub Actions) |
|------|--------|--------------------------|
| **Run tests** | ❌ Forget → break prod | ✅ On every push |
| **Deploy backend** | ❌ 30 mins each time | ✅ 5 mins (Railway) |
| **Deploy frontend** | ❌ 30 mins each time | ✅ 5 mins (Vercel) |
| **Backup before deploy** | ❌ Forget → risky | ✅ Auto-backup |

**My insight:**   
As solo dev, **CI/CD = insurance policy**.   
`git push` → 5 mins later → live. Zero manual work.

---

## 2. My CI/CD Model (Lean, GitHub Actions))

### What You Actually Need (2 Workflows))

```yaml
# .github/workflows/test.yml
name: Run Tests+

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3+
      
      # 1. Setup Python
      - name: Setup Python
        uses: actions/setup-python@v4+
        with:
          python-version: '3.11'+
      
      # 2. Install deps
      - name: Install deps
        run: |
          cd spine_api
          pip install uv
          uv pip install -r requirements.txt
          uv pip install pytest pytest-cov+
      
      # 3. Run tests (FAIL if any break)
      - name: Run pytest
        run: |
          cd spine_api
          pytest tests/ -v --cov=src --cov-fail-under=40+
      
      # 4. Upload coverage (optional)
      - name: Upload coverage
        if: always()
        uses: codecov/codecov-action@v4+
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3+
      
      # 1. Setup Node
      - name: Setup Node
        uses: actions/setup-node@v4+
        with:
          node-version: '20'+
      
      # 2. Install deps
      - name: Install deps
        run: |
          cd frontend
          npm ci+
      
      # 3. Run tests
      - name: Run tests
        run: |
          cd frontend
          npm test+
```

**My insight:**   
`--cov-fail-under=40` = enforce 40% coverage.   
FAIL CI if tests break → you can't merge broken code. 

---

### Deployment Workflow (Auto-Deploy))

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production+

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3+
      
      # 1. Run tests FIRST (never deploy broken)
      - name: Run tests
        run: |
          cd spine_api
          pip install uv
          uv pip install -r requirements.txt
          uv pip install pytest
          pytest tests/ -v+
      
      # 2. Backup DB (before deploy!)
      - name: Backup DB
        env:
          PGPASSWORD: ${{ secrets.DB_PASSWORD }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          TIMESTAMP=$(date +%Y%m%d_%H%M%S)
          pg_dump $DATABASE_URL | gzip > /tmp/backup_$TIMESTAMP.sql.gz
          aws s3 cp /tmp/backup_$TIMESTAMP.sql.gz s3://my-agency-backups/db/
          echo "Backup done: backup_$TIMESTAMP.sql.gz"
      
      # 3. Deploy to Railway
      - name: Deploy Backend
        uses: railway-deploy@v2+
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: travel-agency-backend+

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3+
      
      # 1. Run tests FIRST
      - name: Run tests
        run: |
          cd frontend
          npm ci
          npm test+
      
      # 2. Deploy to Vercel
      - name: Deploy Frontend
        uses: vercel-deploy@v3+
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend+
```

**My insight:**   
Backup BEFORE deploy = **insurance policy**.   
If deploy breaks → restore from backup (1 hour). 

---

## 3. Secrets Management (GitHub))

### What to Store in GitHub Secrets+

| Secret | Where to Get | Why |
|--------|--------------|-----|
| **RAILWAY_TOKEN** | Railway Dashboard → Settings → Tokens | Deploy backend |
| **VERCEL_TOKEN** | Vercel Dashboard → Settings → Tokens | Deploy frontend |
| **VERCEL_ORG_ID** | Vercel Dashboard → Settings | Project belongs here |
| **VERCEL_PROJECT_ID** | Vercel Dashboard → Project Settings | Which project? |
| **DB_PASSWORD** | Your `.env` file | Backup command needs it |
| **AWS_ACCESS_KEY_ID** | AWS Console → IAM → Security Credentials | S3 backup |
| **AWS_SECRET_ACCESS_KEY** | AWS Console → IAM → Security Credentials | S3 backup |

**My insight:**   
GitHub Secrets = **encrypted at rest**.   
`secrets.RAILWAY_TOKEN` ≠ `.env` file (different places). 

---

### How to Add Secrets+

```bash
# 1. Go to: https://github.com/you/travel-agency-agent/settings/secrets/actions

# 2. Add each secret:
- Name: RAILWAY_TOKEN
  Value: [paste from Railway dashboard]

- Name: VERCEL_TOKEN
  Value: [paste from Vercel dashboard]

# 3. Verify in workflow:
- ${{ secrets.RAILWAY_TOKEN }}  # Auto-replaced
```

**My insight:**   
Secrets NEVER appear in logs.   
`${{ secrets.X }}` = replaced at runtime. 

---

## 4. Branch Protection (Optional, Later))

### Why You Might Want It+

| Without Protection | With Protection |
|-------------------|-------------------|
| ❌ force-push to main | ✅ Only PRs with passing tests |
| ❌ Forget to run tests | ✅ Tests REQUIRED to merge |
| ❌ Broken code reaches prod | ✅ Only working code reaches prod |

### Setup (5 Minutes, Later))

```bash
# 1. Go to: https://github.com/you/travel-agency-agent/settings/branches

# 2. Add rule:
- Branch: main
- Require status checks: ✅ backend-tests, ✅ frontend-tests
- Require branches up to date: ✅ YES

# 3. Now:
- `git push origin main` → auto-runs tests
- If tests fail → can't merge
```

**My insight:**   
Branch protection = **force multiplier**.   
You can't accidentally break production. 

---

## 5. Current State vs CI/CD Model+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| CI (tests) | None | GitHub Actions (pytest + npm test) |
| CD (deploy) | Manual | GitHub Actions (Railway + Vercel) |
| Backup before deploy | None | Auto-backup to S3 |
| Secrets mgmt | None | GitHub Secrets (encrypted) |
| Branch protection | None | Later (require passing tests) |

---

## 6. Decisions Needed (Solo Dev Reality)+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| CI/CD now? | Yes / Later | **NOW** — 15 mins setup, saves hours |
| Backup before deploy? | Yes / No | **YES** — 5 mins in workflow |
| Branch protection? | Now / Later | **Later** — you're solo, trust yourself |
| Coverage requirement? | 40% / 60% / None | **40%** — money + compliance only |
| Auto-deploy? | Yes / Manual trigger | **YES** — git push = live |

---

## 7. Next Discussion: Code Quality Tools+

Now that we know **HOW code moves**, we need to discuss: **HOW to keep it clean?**

Key questions for next discussion:
1. **Black** — Python code formatter? (auto-runs?)
2. **isort** — sort Python imports?
3. **mypy** — static type checking for Python?
4. **ESLint** — Next.js code quality?
5. **Prettier** — format frontend code?
6. **Solo dev reality** — what's the MINIMUM to stay clean?

---

**Next file:** `Docs/discussions/code_quality_tools_2026-04-29.md`
