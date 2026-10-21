# TRV-N04 Scratch Artifacts Cleanup Receipt

**Date:** 2026-10-21  
**Author:** Waypoint OS Audit Wave  
**Status:** Executed & Verified  
**Operator Decision:** Authorized permanent deletion and documentation of root-level scratch files.

---

## 1. Deleted Artifacts Inventory

The following non-tracked ad-hoc artifacts at the project root were verified as obsolete, safely documented, and deleted:

| File Path | Original Size | Last Modified | Original Intent & Classification |
|---|---|---|---|
| `dogfood_cookies.txt` | 131 bytes | 2026-04-26 | Stale session cookie jar from a manual local browser dogfooding session. Superseded by Playwright programmatic authentication fixtures. |
| `test_audit.db` | 0 bytes | 2026-05-02 | Empty SQLite file touched during ad-hoc audit store experimentation. Superseded by `tmp_path` pytest fixtures. |
| `test_audit_str.db` | 0 bytes | 2026-05-02 | Empty SQLite file touched during ad-hoc audit store experimentation. Superseded by `tmp_path` pytest fixtures. |
| `test_booking.db` | 0 bytes | 2026-05-14 | Empty SQLite file touched during ad-hoc booking task experimentation. Superseded by `tmp_path` pytest fixtures. |

---

## 2. Supersession & Impact Analysis

- **Zero Test Impact**: All automated backend and frontend test suites (`pytest`, `vitest`) use isolated `tmp_path` fixtures or mock persistence. No test or production module references these root-level files.
- **Security & Secret Hygiene**: Deleting `dogfood_cookies.txt` removes residual authentication tokens from the filesystem, ensuring zero risk of accidental exposure in logs, bundles, or git staging.

---

## 3. Steps to Reproduce (If Ever Needed)

If an operator or developer needs to reproduce local dogfooding credentials or isolated SQLite test databases:

### A. Generating a Local Dogfood Cookie Jar
1. Start the backend:
   ```bash
   cd spine_api && uv run uvicorn spine_api.server:app --port 8000
   ```
2. In another terminal, authenticate and write cookies to a secure, ignored path:
   ```bash
   curl -s -c .tmp_cookies.txt -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "operator@example.com", "password": "..."}'
   ```
3. Use the session cookie for testing:
   ```bash
   curl -s -b .tmp_cookies.txt http://localhost:8000/api/workspace
   ```

### B. Creating Isolated Test Databases
Do not touch the repository root. Always use a temporary directory or in-memory SQLite:
```python
import sqlite3
import tempfile

# Option 1: In-memory
conn = sqlite3.connect(":memory:")

# Option 2: Isolated temp file
with tempfile.NamedTemporaryFile(suffix=".db") as f:
    conn = sqlite3.connect(f.name)
```
In pytest tests, always use the built-in `tmp_path` fixture:
```python
def test_sqlite_feature(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
```
