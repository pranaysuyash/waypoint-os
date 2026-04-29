# Dependency Management — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, Python + Node.js  
**Approach:** Independent analysis — minimum viable dep management, not enterprise  

---

## 1. The Core Truth: You Install Once, Forget... Until It Breaks+

### Your Reality (Solo Dev))

| Problem | Impact | Frequency |
|---------|--------|-----------|
| **Security vuln in deps** | Hack risk | MEDIUM (monthly) |
| **Dep conflict** | CI fails | LOW (you control versions) |
| **Dep update breaks code** | Debug 3h+ | LOW (small depset) |
| **License violation** | Legal risk | VERY LOW (MIT/Apache) |

**My insight:**   
As solo dev, **pip-audit monthly** = enough.   
Don't over-engineer monorepo tools.

---

## 2. My Dependency Model (Lean, Practical))

### Python (spine_api, src/)+

| Tool | What It Does | Setup Time |
|------|--------------|-------------|
| **uv** | Fast pip replacement | 5 mins (already using) |
| **pyproject.toml** | Deps + lockfile | Already exists |
| **pip-audit** | Security scan | 0 (built-in) |
| **pip-tools** | Compile deps | ❌ SKIP — uv handles it |

### Setup (Already Done, Verify))+

```bash
# pyproject.toml (already exists)
[project]
name = "spine-api"
version = "0.1.0"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pydantic>=2.0",
    "openai>=1.0",  # AI calls
    "anthropic>=0.39",  # Claude calls
    "pg8000>=1.29",  # PostgreSQL
    "python-dotenv>=1.0",
    "requests>=2.31",
    "python-jose>=3.3",  # JWT
    "passlib>=1.7",  # Password hashing
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "black>=23.0",
    "isort>=5.12",
    "mypy>=1.8"
]

# Lock file (already exists)
uv.lock  # Commit this!
```

**My insight:**   
`uv.lock` = **deterministic builds**. Commit it!   
`pyproject.toml` > `requirements.txt` (modern standard).

---

### Node.js (frontend/)+

| Tool | What It Does | Setup Time |
|------|--------------|-------------|
| **npm** | Package manager | 0 (already using) |
| **package.json** | Deps + lockfile | Already exists |
| **npm audit** | Security scan | 0 (built-in) |
| **npm-check-updates** | Check updates | 2 mins |

### Setup (Already Done, Verify))+

```json
// frontend/package.json (already exists)
{
  "name": "travel-agency-frontend",
  "version": "0.1.0",
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@tanstack/react-query": "^5.0.0",
    "next-auth": "^4.24.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0",
    "@typescript-eslint/parser": "^7.0.0.0",
    "vitest": "^1.0.0"
  },
  "engines": {
    "node": ">=20.0.0"  // Enforce Node 20+
  }
}
```

**My insight:**   
`package-lock.json` = **commit it** (deterministic builds).   
`@tanstack/react-query` > manual `fetch` (better caching). 

---

## 3. Security Scanning (Monthly, 5 Mins))+

### Python (pip-audit))+

```bash
# Monthly cron (or manual)
cd spine_api && pip-audit

# If vulns found:
uv pip install --upgrade package_name  # Fix

# Check specific package:
pip-audit --package fastapi
```

**My insight:**   
`pip-audit` = FREE, built-in.   
Fix CRITICAL vulns only (CVSS >7.0). 

---

### Node.js (npm audit))+

```bash
# Monthly (or manual)
cd frontend && npm audit

# If vulns found:
npm update package_name  # Fix

# Auto-fix (dangerous, may break):
npm audit fix
```

**My insight:**   
`npm audit fix` = **auto-update**, may break code.   
Better: `npm update package_name` (manual, safer). 

---

## 4. Dep Update Strategy (Conservative))+

### What to Update (When))+

| Dep Type | When to Update | Why |
|---------|-----------------|-----|
| **Security fix** | IMMEDIATELY | CVSS >7.0 |
| **Major version** | NEVER (auto) | May break API |
| **Minor version** | Quarterly | New features, low risk |
| **Patch version** | Monthly | Bug fixes, safe |

### Safe Update Process (5 Steps))+

```bash
# 1. Create backup branch
git checkout -b backup-pre-update

# 2. Update (conservative)
cd spine_api
uv pip install --upgrade-package minor fastapi  # Only minor

# 3. Run tests (MUST pass)
pytest tests/ -v

# 4. If tests pass → merge
git checkout main
git merge backup-pre-update

# 5. If tests fail → revert
git checkout main
git branch -D backup-pre-update
```

**My insight:**   
`--upgrade-package minor` = safe (not major).   
Tests MUST pass before merge.

---

## 5. Monorepo Tools (SKIP for Solo Dev))+

### Why You DON'T Need Them+

| Tool | Why Skip It | Alternative |
|------|--------------|-------------|
| **Turborepo** | ❌ Overkill (2 packages) | Separate commands |
| **Nx** | ❌ Enterprise (100+ packages) | Separate commands |
| **Lerna** | ❌ Legacy, dead | Separate commands |

### Simple Alternative (2 Commands))+

```bash
# Update all (monthly)
cd spine_api && uv pip install --upgrade-package minor -r requirements.txt
cd ../frontend && npm update

# Run all tests
cd spine_api && pytest tests/ -v
cd ../frontend && npm test
```

**My insight:**   
2 commands = **2 minutes**. Turborepo = 2 hours setup.   
As solo dev, **simplicity > DRY** (Don't Repeat Yourself).

---

## 6. License Compliance (Check Once))+

### What to Check (MIT/Apache = Safe))+

```bash
# Python
cd spine_api
pip-licenses  # Shows all licenses

# Node.js
cd frontend
npx license-checker --summary
```

**My insight:**   
MIT/Apache = **safe** (can use commercially).   
AGPL = **DANGER** (must open-source your code). 

---

## 7. Current State vs Deps Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Python deps | pyproject.toml + uv.lock | ✅ Same |
| Node deps | package.json + lock | ✅ Same |
| Security scan | None | `pip-audit` + `npm audit` (monthly) |
| Update strategy | None | Conservative (minor only) |
| Monorepo tools | None | ❌ SKIP — 2 commands |
| License check | None | `pip-licenses` (once) |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Monthly audit? | Yes / No | **YES** — 5 mins/month |
| Auto-update? | Minor / Patch only | **Patch** — safer |
| Monorepo? | Turborepo / None | **NONE** — 2 commands |
| Lock files commit? | Yes / No | **YES** — deterministic builds |
| License check? | Now / Later | **LATER** — unlikely issue |

---

## 9. Next Discussion: Logging & Observability+

Now that we know **HOW to manage deps**, we need to discuss: **WHERE do logs go?**

Key questions for next discussion:
1. **Structured logging** — JSON logs vs text?
2. **Log storage** — Railway/Vercel built-in vs S3?
3. **Log rotation** — keep 7 days? 30 days?
4. **Log levels** — DEBUG vs INFO vs ERROR?
5. **Solo dev reality** — what's the MINIMUM logging needed?

---

**Next file:** `Docs/discussions/logging_observability_2026-04-29.md`
