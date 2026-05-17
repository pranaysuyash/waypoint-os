# Collection Link Re-expose — Design Plan
**Date:** 2026-05-17 (revised 2026-05-18)
**Status:** Implemented on `review/collection-link-reexpose-encrypted-token` — awaiting review sign-off before merge to master
**Scope:** Trip Workspace → Ops → Customer Collection Link
**Not in scope:** payment collection, public itinerary checker, document upload portal

---

## Problem Statement

After page reload, browser restart, or a second operator session, the Ops page shows:

> "Active link exists (expires …). Generating a new link will revoke the old one."

But the operator cannot see or copy the URL. The actual `collection_url` is only
available in `linkInfo` state, which is populated only when `generateCollectionLink()`
is called in the current session. `getCollectionLink()` returns `CollectionLinkStatus`,
which has no `collection_url` field. So `linkInfo` is `null` on reload even when
`linkStatus.has_active_token` is `true`.

To re-share the link the operator must generate a new one — which revokes the old URL
and silently invalidates any in-flight customer submission via the old token.

---

## Inspection Findings

### 1. Where is the active collection token stored?

`booking_collection_tokens` PostgreSQL table (`spine_api/models/tenant.py`):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Token record PK |
| `trip_id` | FK → trips | |
| `agency_id` | FK → agencies | Tenant boundary |
| `token_hash` | SHA-256 hex | **Plain token is never persisted** |
| `status` | active / revoked / used / expired | |
| `expires_at` | timestamptz | |
| `created_by` | user_id | |
| `revoked_at` | nullable | |
| `used_at` | nullable | |

The plain token is generated via `secrets.token_urlsafe(32)` in
`collection_service.generate_token()`. Only the SHA-256 hash is written to the DB.
**The plain token is returned once — to the generating request — and then gone.**

### 2. Does the backend store enough data to reconstruct `collection_url`?

No. The plain token is not stored. Only the hash is stored. SHA-256 is one-way.
The URL cannot be reconstructed from current DB state.

### 3. Does GET /collection-link currently return only status metadata or the full `collection_url`?

Status metadata only. Current `CollectionLinkStatusResponse`:

```python
class CollectionLinkStatusResponse(BaseModel):
    has_active_token: bool
    token_id: Optional[str] = None
    expires_at: Optional[str] = None
    status: Optional[str] = None
    has_pending_submission: bool
```

No `collection_url` field. The GET handler calls `get_active_token_for_trip()` which
returns the `BookingCollectionToken` ORM record — which contains only `token_hash`,
not the plain token.

### 4. Is it safe to return `collection_url` to authenticated agency users?

Yes, with guardrails:

- The operator already has the right to generate and revoke the link.
- The URL is already time-limited (default 168 hours), single-use after customer
  submission, and revocable at any time.
- Re-showing it to the same authenticated agency operator does not expand its audience.

The only risk is an operator copying it to an unintended party — identical operational
risk to the original "generate and paste to customer" workflow.

**What must NOT happen:** `collection_url` must never appear on any public or
unauthenticated endpoint. The public `GET /api/public/booking-collection/...`
endpoint must not return it.

### 5. What auth / agency / stage / security constraints must hold?

All of the following must be true before returning `collection_url`:

1. Request carries valid JWT → `get_current_agency` succeeds
2. Token `status == "active"` (not revoked, not used, not expired)
3. Token `expires_at > now()` (expiry check in `get_active_token_for_trip`)
4. Token `agency_id == agency.id` (enforced by RLS + `get_trip_for_agency`)
5. Token `trip_id` belongs to the requesting agency (same trip ownership check)

Nothing new — these all already hold for the GET endpoint.

### 6. Should the fix be backend-first, frontend-only, or hybrid?

**Backend-first, then a small frontend type/display update.**

Session/localStorage approaches fail for other operators, other devices, browser
restart, and support handoffs. The fix belongs in the backend contract.

---

## Encryption Infrastructure Audit

Before choosing a storage strategy, the codebase was surveyed for existing encryption
support. The infrastructure is already present and directly applicable.

### What exists

**`src/security/encryption.py`**
- Fernet symmetric encryption via `ENCRYPTION_KEY` env var
- Dev fallback key for non-production modes; raises `ValueError` if `ENCRYPTION_KEY`
  unset in `DATA_PRIVACY_MODE=production`
- `encrypt(str) -> str` — Fernet-encrypts a string, returns base64 ciphertext
- `decrypt(str) -> str` — decrypts; falls back to returning original on failure
  (for plaintext legacy data)

**`spine_api/services/private_fields.py`** — shared helpers for all services
- `encrypt_field(value: str) -> dict` → `{"__encrypted_blob": True, "v": 1, "ciphertext": ...}`
- `decrypt_field(blob: dict) -> str` — decrypts single-string field blobs
- `encrypt_blob(data: dict) -> dict` / `decrypt_blob(data: dict) -> dict` — for JSON objects

**`BookingConfirmation` model** — established pattern
```python
# spine_api/models/tenant.py
supplier_name_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
confirmation_number_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
notes_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
external_ref_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
```
Stored as JSON blobs, encrypted with `encrypt_field`, decrypted on read with
`decrypt_field`. Same Fernet key. No migration complexity.

**Conclusion:** Option D (store encrypted plain token + keep token_hash) is
immediately implementable using the existing `encrypt_field` / `decrypt_field`
helpers and the `_encrypted` JSON column pattern. No new infrastructure required.

---

## Design Decision

### Why not store `collection_url` plaintext (Option A — original recommendation)

The initial design proposed adding `collection_url TEXT NULLABLE`. This works as a
patch but is a first-principles mistake:

> A customer collection link is a bearer credential. Anyone with the URL can submit
> booking data for that trip until expiry/revoke/use.

Storing the full URL in plaintext means:
1. The bearer secret lives in the DB in recoverable form
2. Any DB dump or direct SQL access exposes active link secrets
3. The URL bakes in `PUBLIC_COLLECTION_BASE_URL` — if the domain changes, stored URLs
   point to the old domain (requires revoke/regenerate for all active links)

### Why not store `plain_token` plaintext (Option B)

Stores a raw bearer secret directly. Strictly worse than Option A. Rejected.

### Why not store `encrypted_collection_url` (Option C)

Better than plaintext. Downsides:
- Stores more than the minimum secret material (the token is the secret; the base URL
  is configuration)
- Bakes in `PUBLIC_COLLECTION_BASE_URL` at generation time — URL assembled at storage
  rather than at read time

Option D is cleaner.

### Chosen: Option D — store `plain_token_encrypted` + keep `token_hash`

```
token_hash                  → public lookup identity (unchanged)
plain_token_encrypted (JSON) → authenticated re-display secret (new, encrypted at rest)
```

**At generation time:**
- Generate plain token (unchanged)
- Hash it for `token_hash` (unchanged)
- Encrypt it with `encrypt_field(plain_token)` → store in `plain_token_encrypted`
- Return plain token once to caller (unchanged)

**At authenticated GET time:**
- Fetch active token record (unchanged)
- `decrypt_field(token.plain_token_encrypted)` → recover plain token
- Assemble `collection_url` from current `PUBLIC_COLLECTION_BASE_URL` + plain token
- Return `collection_url` in response

**Benefits:**
- Stores only the secret (minimum required material)
- URL assembled at read time → `PUBLIC_COLLECTION_BASE_URL` changes take effect
  immediately on next GET for any active link
- Follows established `BookingConfirmation` column pattern exactly
- Zero new infrastructure — reuses `encrypt_field` / `decrypt_field`

**Note on base URL flexibility:**
Because the URL is assembled at GET time, changing `PUBLIC_COLLECTION_BASE_URL`
affects all subsequent GET responses for active tokens immediately. The link already
shared with the customer (via the original generate response) used the old base URL.
If the domain changes mid-active-token, the operator would see a URL that differs from
what was originally sent to the customer. This is an acceptable edge case — domain
changes are infrequent, and any active link can be revoked and regenerated.

Compare to plaintext `collection_url` storage: that approach preserves the exact URL
that was originally shared, but at the cost of storing a bearer secret in plaintext.
Option D accepts the domain-change edge case in exchange for proper secret handling.

---

## Recommended Contract

### Backend model change (`spine_api/models/tenant.py`)

```python
class BookingCollectionToken(Base):
    # ... existing fields unchanged ...
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # NEW — encrypted plain token for authenticated re-display
    # Stores encrypt_field(plain_token) → {"__encrypted_blob": True, "v": 1, "ciphertext": ...}
    # Nullable for backwards compat with pre-migration rows.
    plain_token_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
```

### Backend service change (`spine_api/services/collection_service.py`)

```python
from spine_api.services.private_fields import encrypt_field

async def generate_token(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    created_by: str,
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> tuple[str, BookingCollectionToken]:
    # ... revoke existing tokens (unchanged) ...

    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()

    record = BookingCollectionToken(
        trip_id=trip_id,
        agency_id=agency_id,
        token_hash=token_hash,
        plain_token_encrypted=encrypt_field(plain_token),  # NEW
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        created_by=created_by,
    )
    # ... rest unchanged ...
```

No signature change to `generate_token` — the encryption is internal.

### Backend endpoint change (`spine_api/server.py`)

`CollectionLinkStatusResponse`:
```python
class CollectionLinkStatusResponse(BaseModel):
    has_active_token: bool
    token_id: Optional[str] = None
    collection_url: Optional[str] = None   # NEW — only set for active, non-expired token
    expires_at: Optional[str] = None
    status: Optional[str] = None
    has_pending_submission: bool
```

`get_collection_link_status` handler:
```python
from spine_api.services.private_fields import decrypt_field

async def get_collection_link_status(
    trip_id: str, agency: Agency = Depends(get_current_agency)
):
    # ... existing trip check and token fetch unchanged ...

    # Assemble collection_url from encrypted token (authenticated only)
    collection_url = None
    if token and token.plain_token_encrypted:
        plain = decrypt_field(token.plain_token_encrypted)
        if plain:
            base_url = os.getenv("PUBLIC_COLLECTION_BASE_URL", "")
            path = f"/api/public/booking-collection/{agency.id}/{plain}"
            collection_url = f"{base_url}{path}" if base_url else path

    return CollectionLinkStatusResponse(
        has_active_token=token is not None,
        token_id=token.id if token else None,
        collection_url=collection_url,          # NEW
        expires_at=token.expires_at.isoformat() if token else None,
        status=token.status if token else None,
        has_pending_submission=pending is not None,
    )
```

`collection_url` is `None` when: no active token, token is expired, token is revoked
or used, or `plain_token_encrypted` is null (pre-migration rows).

### Alembic migration

```python
op.add_column(
    "booking_collection_tokens",
    sa.Column("plain_token_encrypted", postgresql.JSON(), nullable=True),
)
```

Nullable — no backfill needed. Pre-migration rows return `collection_url: null` from
GET, showing the current "Active link exists…" hint without a URL. Acceptable for
the migration window.

### Frontend type change (`frontend/src/lib/api-client.ts`)

```typescript
export interface CollectionLinkStatus {
  has_active_token: boolean;
  token_id: string | null;
  collection_url?: string | null;   // NEW
  expires_at: string | null;
  status: string | null;
  has_pending_submission: boolean;
}
```

### Frontend display change (`DataIntakeZone.tsx`)

Compute a single resolved URL that prefers `linkInfo` (just generated this session)
and falls back to `linkStatus.collection_url` (loaded from server on mount):

```tsx
const displayUrl = linkInfo?.collection_url ?? linkStatus?.collection_url ?? null;
```

Update all URL display, copy, and input references to use `displayUrl` instead of
`linkInfo?.collection_url`. The URL input and Copy button render whenever
`displayUrl` is non-null — regardless of whether `linkInfo` is populated.

Update `handleCopyLink`:
```tsx
const handleCopyLink = useCallback(() => {
  if (!displayUrl) return;
  navigator.clipboard.writeText(displayUrl).then(() => {
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  });
}, [displayUrl]);
```

---

## Security Guardrails

| Rule | Status |
|------|--------|
| Plain token encrypted at rest in `plain_token_encrypted` | Implemented via `encrypt_field` |
| `collection_url` only returned from authenticated agency endpoint | `get_current_agency` dependency, unchanged |
| `collection_url` null for revoked / used / expired tokens | `get_active_token_for_trip` returns None; null propagates |
| `collection_url` not logged in audit event details | Audit events log metadata only — preserve as-is |
| `plain_token_encrypted` not logged anywhere | Treat as opaque blob; never include in audit details |
| Public endpoint unaffected | `public_collection.py` uses `validate_token(db, plain_token)` — unchanged |
| One-active-token semantics preserved | `generate_token` revokes prior active tokens before inserting — unchanged |
| RLS on `booking_collection_tokens` unchanged | Registered in `RLS_TENANT_TABLES` — unchanged |

---

## Tests

### Backend (`tests/test_booking_collection.py`) — add to `TestCollectionLinkCRUD`

| Test | Assertion |
|------|-----------|
| `test_get_status_includes_collection_url_when_active` | After POST, GET returns `collection_url` non-null, contains agency_id in path |
| `test_get_status_collection_url_null_when_no_token` | GET on trip with no token → `collection_url` is null |
| `test_get_status_collection_url_null_after_revoke` | After DELETE, GET → `collection_url` is null |
| `test_get_status_collection_url_null_after_use` | After customer submit (token used), GET → `collection_url` is null |
| `test_get_status_does_not_return_url_for_expired_active_record` | Token row has `status=active` but `expires_at < now` → `get_active_token_for_trip` returns None → `collection_url` null |
| `test_collection_url_not_exposed_from_public_endpoint` | Public `GET /api/public/booking-collection/...` response does NOT contain `collection_url` key |
| `test_plain_token_encrypted_not_logged_in_audit` | Audit event for generate/revoke does not contain the encrypted blob or plain token value |

### Frontend (`DataIntakeZone.test.tsx`) — add/update

| Test | Assertion |
|------|-----------|
| `shows URL and copy button from linkStatus when linkInfo is null` | `getCollectionLink` resolves with `has_active_token: true, collection_url: '...'`; `generateCollectionLink` NOT called; URL input visible; Copy button visible; Generate New Link still present as secondary action |
| `copy button works from linkStatus collection_url` | Click Copy with URL from `linkStatus.collection_url` → `navigator.clipboard.writeText` called with that URL |
| `revoke clears displayed URL` | Generate link → revoke → URL input gone, generate-only state restored |
| `shows active hint but no URL when linkStatus has no collection_url` | `has_active_token: true, collection_url: null` → hint shown, no URL input (pre-migration / expired-encrypted backwards compat) |

---

## Implementation Order

1. **Alembic migration** — add `plain_token_encrypted JSON NULLABLE` to `booking_collection_tokens`
2. **`private_fields.py`** — no change; `encrypt_field` / `decrypt_field` already exist
3. **`collection_service.generate_token`** — add `plain_token_encrypted=encrypt_field(plain_token)`
4. **`CollectionLinkStatusResponse`** — add `collection_url: Optional[str] = None`
5. **`get_collection_link_status`** — decrypt token, assemble URL, populate `collection_url`
6. **`api-client.ts:CollectionLinkStatus`** — add `collection_url?: string | null`
7. **`DataIntakeZone.tsx`** — compute `displayUrl`, update render and copy handler
8. **Backend tests** — 7 cases (6 existing + 1 new expired-active-row case)
9. **Frontend tests** — 4 updated/new cases

---

## What Not to Build

- No sessionStorage / localStorage caching
- No link history or old URL list
- No expiry extension
- No audit log with raw token, encrypted blob, or assembled URL
- No public endpoint changes
- No new API endpoint — this is a response field addition to the existing GET
- No multi-token semantics — one-active-token-per-trip invariant preserved
- No new encryption infrastructure — reuse `encrypt_field` / `decrypt_field`

---

## Open Questions

- **`PUBLIC_COLLECTION_BASE_URL` in tests:** Env var is unset in CI so URLs are
  path-only. Tests asserting `collection_url` non-null should match against the path
  pattern (`/api/public/booking-collection/...`) or set the env var in the fixture.
- **Pre-migration active tokens:** Any token that exists at migration time will have
  `plain_token_encrypted = null`, so GET returns `collection_url: null`. The operator
  will see the "Active link exists…" hint without a URL. They can revoke and regenerate
  to get a new encrypted token. This is acceptable.
- **Fernet key rotation:** If `ENCRYPTION_KEY` is rotated without re-encrypting
  existing rows, `decrypt_field` will return the original ciphertext string (fallback
  in `decrypt()`). In that case `collection_url` will be null. This matches the general
  encryption posture for all `_encrypted` fields in the codebase.
