# Code Quality Tools — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, keep code clean+  
**Approach:** Independent analysis — minimum viable quality, not enterprise  

---

## 1. The Core Truth: You're Solo, But Code Quality = Insurance+

### Your Reality (Solo Dev))

| Task | Manual | Automated (5 mins setup) |
|------|--------|--------------------------|
| **Format code** | ❌ 30 mins + forget | ✅ Black/Prettier auto-runs |
| **Sort imports** | ❌ Forget + messy | ✅ isort/ESLint auto-runs |
| **Type check** | ❌ Run manually | ✅ mypy in CI |
| **Lint** | ❌ Miss errors | ✅ ESLint in CI |

**My insight:**   
As solo dev, **automate quality** (setup once, runs forever).   
Bad code = YOU debug it 3x longer.

---

## 2. My Code Quality Model (Lean, Practical))

### Python Tools (spine_api, src/)+

| Tool | What It Does | Setup Time | Why You Need It |
|------|--------------|-------------|-------------------|
| **Black** | Auto-format PEP8 | 2 mins | Consistent style, zero thinking |
| **isort** | Sort imports | 1 min | Clean imports, avoid cycles |
| **mypy** | Static type check | 3 mins | Catch `NoneType` errors before runtime |
| **pytest-cov** | Coverage report | 1 min | Know if tests actually cover |

### Setup (5 Minutes Total))

```bash
# spine_api/ and src/ (Python)
cd spine_api && uv pip install black isort mypy pytest-cov

# .pyproject.toml (already exists, add config)
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true  # Strict mode

[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=40"
```

**My insight:**   
`disallow_untyped_defs = true` = stricter, catches bugs.   
Start strict, relax only if needed.

---

### Pre-commit Hook (Auto-runs on `git commit`)+

```yaml
# .pre-commit-config.yaml (in repo root)
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

# Setup (1 minute)
pip install pre-commit
pre-commit install  # Installs git hook
```

**My insight:**   
`pre-commit install` = runs Black/isort/mypy BEFORE each commit.   
If Black reformats → commit fails, fix → re-stage → commit again.

---

### Next.js Tools (frontend/)+

| Tool | What It Does | Setup Time | Why You Need It |
|------|--------------|-------------|-------------------|
| **ESLint** | Catches JS/TS bugs | 2 mins | `undefined` errors before runtime |
| **Prettier** | Auto-format code | 1 min | Consistent style, zero thinking |
| **TypeScript** | Static types | Built-in | Catch type errors before runtime |

### Setup (3 Minutes Total))

```json
// frontend/.eslintrc.json
{
  "extends": ["next/core-web-vitals", "plugin:@typescript-eslint/recommended"],
  "rules": {
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "react-hooks/exhaustive-deps": "warn",  // Relax: warning not error
    "@typescript-eslint/no-explicit-any": "warn"  // Relax: allow `any` with warning
  }
}

// frontend/.prettierrc
{
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "semi": true
  "tabWidth": 2
}
```

**My insight:**   
`no-explicit-any` = warning, not error.   
TypeScript is hard, don't block commits for minor issues.

---

### VSCode Settings (Auto-format on Save)+

```json
// .vscode/settings.json (in repo root, commit this!)
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.rulers": [100]
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**My insight:**   
Commit `.vscode/settings.json` → same settings for YOU on any machine.   
`formatOnSave` = zero thinking about formatting. 

---

## 3. CI Integration (GitHub Actions))

### What to Add (5 Mins to CI YAML)+

```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  python-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3+
      
      - name: Setup Python
        uses: actions/setup-python@v4+
        with:
          python-version: '3.11'+
      
      - name: Install deps
        run: |
          cd spine_api
          pip install uv
          uv pip install -r requirements.txt
          uv pip install black isort mypy+
      
      - name: Run Black (check only)
        run: |
          black --check spine_api src/+
      
      - name: Run isort (check only)
        run: |
          isort --check-only spine_api src/+
      
      - name: Run mypy
        run: |
          cd src
          mypy . --ignore-missing-imports+
  
  frontend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3+
      
      - name: Setup Node
        uses: actions/setup-node@v4+
        with:
          node-version: '20'+
      
      - name: Install deps
        run: |
          cd frontend
          npm ci+
      
      - name: Run ESLint
        run: |
          cd frontend
          npm run lint  # Add "lint": "eslint ." to package.json+
      
      - name: Run Prettier (check only)
        run: |
          cd frontend
          npx prettier --check .+
```

**My insight:**   
`--check` flag = don't reformat, just FAIL if not formatted.   
CI fails → you know BEFORE merging to main. 

---

## 4. Current State vs Quality Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Python formatter | None | Black (auto-formats) |
| Import sorting | None | isort (auto-sorts) |
| Type checking | None | mypy (static analysis) |
| Pre-commit hook | None | Auto-runs on `git commit` |
| ESLint | None | Catches JS/TS bugs |
| Prettier | None | Auto-formats TS/TSX |
| VSCode settings | None | Committed `.vscode/` (consistent) |
| CI integration | None | GitHub Actions runs quality |

---

## 5. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Black? | Now / Later | **NOW** — 2 mins, zero effort after |
| mypy strict? | Strict / Relaxed | **Relaxed** — `warn_return_any` only |
| Pre-commit? | Yes / No | **YES** — auto-blocks bad commits |
| ESLint strict? | Strict / Relaxed | **Relaxed** — warnings not errors |
| CI quality? | Now / Later | **NOW** — add to existing workflow |

---

## 6. Next Discussion: Dependency Management+

Now that we know **HOW to keep code clean**, we need to discuss: **HOW to manage deps?**

Key questions for next discussion:
1. **pyproject.toml** — uv/pip deps, how to organize?
2. **package.json** — npm vs pnpm, deps vs devDeps?
3. **Lock files** — `uv.lock`, `package-lock.json`, commit or not?
4. **Security scanning** — `npm audit`, `pip-audit`?
5. **Solo dev reality** — what's the MINIMUM dep management?

---

**Next file:** `Docs/discussions/dependency_management_2026-04-29.md`
