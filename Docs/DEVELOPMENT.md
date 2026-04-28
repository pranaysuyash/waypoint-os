# Development Guide

## PATCHABLE_FIELDS Governance Pattern

### Overview

The `PATCHABLE_FIELDS` allowlist is a security and integrity control that explicitly declares which Trip fields can be modified via the PATCH endpoint. This pattern prevents accidental or malicious modification of immutable fields like `id`, `createdAt`, `updatedAt`, and other system-managed properties.

### Why Does It Exist?

Without an explicit allowlist, any field in the Trip object could potentially be modified via PATCH requests, including:
- System fields (`id`, `createdAt`, `updatedAt`) - modifying these breaks data integrity
- Sensitive fields that should only be set at creation time
- Fields managed by the backend logic that shouldn't be overwritten

The allowlist ensures that only intentionally patchable fields are modifiable, blocking everything else at the API layer.

### Where It Lives

**Frontend API route** (source of truth for backend-accessible fields):
```
frontend/src/app/api/trips/[id]/route.ts
```

Example implementation:
```typescript
// Line ~30
const PATCHABLE_FIELDS = new Set([
  "customerMessage",
  "agentNotes",
  "budget",
  "follow_up_due_date",
]);

// Usage in PATCH handler
const updates: Partial<Trip> = {};
for (const key of Object.keys(body)) {
  if (PATCHABLE_FIELDS.has(key)) {
    updates[key] = body[key];
  }
}
// Only updates with allowed keys are sent to backend
```

### Adding a New Patchable Field

When you need to make a new Trip field editable via PATCH, follow this checklist:

#### Step 1: Define the Field in Frontend Interface
**File**: `frontend/src/lib/api-client.ts`
```typescript
export interface Trip {
  // ... existing fields
  newField?: string;  // Add your new field
}
```

#### Step 2: Add Field to Backend Model
**File**: `spine_api/persistence.py`
```python
class Trip(Base):
    # ... existing columns
    new_field = Column(String, nullable=True)  # Match frontend type
```

#### Step 3: **CRITICAL** - Add Field to PATCHABLE_FIELDS
**File**: `frontend/src/app/api/trips/[id]/route.ts`
```typescript
const PATCHABLE_FIELDS = new Set([
  "customerMessage",
  "agentNotes",
  "budget",
  "follow_up_due_date",
  "newField",  // <-- ADD HERE
]);
```

Without this step, PATCH requests with the new field will silently ignore it.

#### Step 4: Update PATCH Endpoint Docstring
**File**: `frontend/src/app/api/trips/[id]/route.ts`
```typescript
/**
 * PATCH /api/trips/:id
 * Update a trip. Modifiable fields: customerMessage, agentNotes, budget, 
 * follow_up_due_date, newField
 */
```

#### Step 5: Write Tests for the New Field
Create a round-trip test to verify the field can be set via PATCH and retrieved via GET:

```typescript
// tests/integration/trip-patch.test.ts
test('PATCH updates newField', async () => {
  // Create trip
  const createRes = await fetch('/api/trips', {
    method: 'POST',
    body: JSON.stringify({ raw_note: 'Test' })
  });
  const trip = await createRes.json();

  // Patch field
  const patchRes = await fetch(`/api/trips/${trip.id}`, {
    method: 'PATCH',
    body: JSON.stringify({ newField: 'updated value' })
  });
  const updated = await patchRes.json();
  expect(updated.newField).toBe('updated value');

  // Verify persistence
  const getRes = await fetch(`/api/trips/${trip.id}`);
  const retrieved = await getRes.json();
  expect(retrieved.newField).toBe('updated value');
});
```

### Common Mistake: Field Patchable But Not In Allowlist

**Problem**: You add a field to the Trip interface and backend model, tests pass (using direct mutations), but PATCH requests silently drop the field.

**Root Cause**: Field was not added to `PATCHABLE_FIELDS`.

**Prevention**: The checklist above catches this. The test in Step 5 will fail if the field isn't in PATCHABLE_FIELDS, since the PATCH response won't contain the new value.

### Verification

After adding a new field:

1. Verify it's in the allowlist: `grep -n "PATCHABLE_FIELDS" frontend/src/app/api/trips/[id]/route.ts`
2. Run tests: `npm run test -- trip-patch.test.ts`
3. Manual verification:
   ```bash
   # Start dev server
   npm run dev

   # Try patching the field
   curl -X PATCH http://localhost:3000/api/trips/123 \
     -H "Content-Type: application/json" \
     -d '{"newField": "test"}'

   # Verify the response contains the updated field
   ```

## Related Documentation

- **User Guide**: See `Docs/USER_GUIDE.md` for operator-facing documentation on using Call Capture
- **Deployment**: See `Docs/DEPLOYMENT.md` for deployment and rollback procedures
- **Launch Checklist**: See `Docs/UNIT1_LAUNCH_CHECKLIST.md` for pre-launch verification
