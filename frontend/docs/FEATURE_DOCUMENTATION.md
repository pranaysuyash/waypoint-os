# Travel Agency Agent - Feature Documentation

## Table of Contents
1. [Inbox Sorting](#inbox-sorting)
2. [Multi-Currency Support](#multi-currency-support)
3. [Editable Workspace Fields](#editable-workspace-fields)
4. [Field Change Logging / Audit Trail](#field-change-logging--audit-trail)
5. [Smart Combobox with Fuzzy Matching](#smart-combobox-with-fuzzy-matching)

---

## Inbox Sorting

**Location**: `frontend/src/app/inbox/page.tsx`

### Features
- **8 Sort Options**: Priority, Destination, Value, Party Size, Dates, State, Age, SLA Status
- **Bidirectional**: Ascending/Descending toggle for each sort
- **Persistent**: Sort selection maintained during session

### Usage
```
1. Click "Sort by [option]" button in inbox header
2. Select desired sort field from dropdown
3. Toggle direction with ↑/↓ buttons
```

### Implementation Notes
- Uses `SortKey` type for type-safe sorting
- Priority sorting has built-in tiebreaker (SLA status)
- State sorting follows: Red > Amber > Blue > Green

---

## Multi-Currency Support

**Locations**:
- `frontend/src/lib/currency.ts` - Currency utilities
- `frontend/src/contexts/CurrencyContext.tsx` - Currency context
- `frontend/src/components/workspace/panels/IntakePanel.tsx` - Budget field

### Supported Currencies
- INR (₹) - Indian Rupee
- USD ($) - US Dollar
- EUR (€) - Euro
- GBP (£) - British Pound
- AED (د.إ) - UAE Dirham
- SGD (S$) - Singapore Dollar
- THB (฿) - Thai Baht
- AUD (A$) - Australian Dollar
- CAD (C$) - Canadian Dollar
- JPY (¥) - Japanese Yen

### Features
- **Currency Recording**: Budget stored with original currency
- **Symbol Display**: Proper currency symbols for each
- **Locale Formatting**: Region-specific number formatting
- **No Conversion**: Focus on recording, not converting

### API
```typescript
// Format money for display
formatMoney(amount: number, currency: SupportedCurrency): string

// Parse budget string to Money object
parseBudgetString(input: string): Money | null

// Format compact (e.g., ₹2L, $5k)
formatMoneyCompact(amount: number, currency: SupportedCurrency): string

// Get currency options for dropdown
getCurrencyOptions(): CurrencyOption[]
```

### Example Usage
```typescript
import { formatMoney, parseBudgetString, CURRENCY_CONFIG } from '@/lib/currency';

// Display budget
const display = formatMoney(200000, 'INR'); // "₹2,00,000"

// Parse user input
const parsed = parseBudgetString("2 lac USD");
// Returns: { amount: 200000, currency: 'USD' }
```

---

## Editable Workspace Fields

**Location**: `frontend/src/components/workspace/panels/IntakePanel.tsx`

### Editable Fields
1. **Destination** - Text input
2. **Type** - Combobox (see Smart Combobox)
3. **Party Size** - Number input
4. **Date Window** - Text input
5. **Budget** - Amount + Currency selector

### Usage
```
1. Hover over any trip detail field
2. Click edit (pencil) icon that appears
3. Modify the value
4. Click ✓ to save or ✕ to cancel
```

### Features
- **Inline Editing**: No modal, edit directly in place
- **Visual Feedback**: Blue border indicates edit mode
- **Validation**: Numeric fields validate on save
- **Auto-save**: Changes persisted immediately

---

## Field Change Logging / Audit Trail

**Locations**:
- `frontend/src/types/audit.ts` - Type definitions
- `frontend/src/hooks/useFieldAuditLog.ts` - Audit hook
- `frontend/src/components/workspace/panels/ChangeHistoryPanel.tsx` - UI component

### Tracked Changes
- Field name
- Change type (create, update, delete, restore)
- Previous value
- New value
- User who made change
- Timestamp (ISO 8601)
- Optional reason

### Features
- **LocalStorage Persistence**: Changes survive page refresh
- **Change Summary**: Total changes, last edit info
- **Expandable Details**: Click to see full change details
- **Export**: Download audit log as JSON
- **Per-Trip**: Each trip has isolated audit log

### API
```typescript
const {
  logChange,           // Log a field change
  getChanges,          // Get all changes for trip
  getChangesForField,  // Get changes for specific field
  getLatestChangeForField, // Get most recent change for field
  getAuditLog,         // Get complete audit log
  clearChanges,        // Clear all changes (with confirmation)
  exportChanges,       // Export as JSON string
} = useFieldAuditLog({ tripId, userId, userName });
```

### Example Usage
```typescript
// Log a change
logChange(
  'destination',        // field
  'update',             // change type
  'Paris',              // previous value
  'London',             // new value
  'Customer requested'   // optional reason
);

// Get recent changes
const changes = getChanges();

// Get audit summary
const summary = getChangeSummary(changes);
// { totalChanges, changesByField, changesByUser, lastChangeAt, lastChangeBy }
```

### Storage Format
```json
{
  "tripId": "trip-123",
  "changes": [
    {
      "id": "change_1234567890_abc123",
      "tripId": "trip-123",
      "field": "destination",
      "changeType": "update",
      "previousValue": "Paris",
      "newValue": "London",
      "changedBy": "agent-1",
      "changedByName": "Sarah Chen",
      "timestamp": "2026-04-22T10:30:00.000Z",
      "reason": "Customer requested change"
    }
  ],
  "lastModified": "2026-04-22T10:30:00.000Z",
  "version": 5
}
```

---

## Smart Combobox with Fuzzy Matching

**Locations**:
- `frontend/src/lib/combobox.ts` - Combobox utilities
- `frontend/src/components/ui/SmartCombobox.tsx` - React component

### Features
- **Predefined Options**: Dropdown with common values
- **Custom Entry**: Type to add new options
- **Title Case Normalization**: "honeymoon" → "Honeymoon"
- **Duplicate Prevention**: Normalization prevents duplicates
- **Fuzzy Matching**: Suggests similar existing options
- **Near-Duplicate Detection**: Warns if input ≈ existing option

### Predefined Options

#### Trip Types
```
Honeymoon, Family Vacation, Adventure, Beach, Pilgrimage,
Business, Weekend Getaway, Group Tour, Luxury, Backpacking,
Cultural, Wildlife, Cruise, Wellness, Solo Trip
```

#### Destinations
```
International: Thailand, Dubai, Singapore, Bali, Maldives,
Europe, Switzerland, Paris, Japan, Vietnam, Sri Lanka, Nepal, Malaysia

Domestic: Andaman, Kerala, Goa, Himachal, Kashmir, Rajasthan,
Ladakh, North East, Delhi, Mumbai
```

#### Accommodation Types
```
Hotel, Resort, Villa, Hostel, Homestay, Houseboat, Glamping, Camp
```

#### Meal Plans
```
Room Only (EP), Breakfast (CP), Half Board, Full Board, All Inclusive
```

### Fuzzy Matching Algorithm
- **Levenshtein Distance**: Character edit distance
- **Similarity Score**: 0-1 (1 = exact match)
- **Threshold**: 0.6 for suggestions, 0.85 for duplicate detection

### API
```typescript
// Title case normalization
toTitleCase(input: string): string

// Check if values match after normalization
valuesMatch(a: string, b: string): boolean

// Calculate similarity score (0-1)
calculateSimilarity(a: string, b: string): number

// Find fuzzy matches
findFuzzyMatches(input, options, threshold): FuzzyMatch[]

// Find near duplicate
findNearDuplicate(input, options, threshold): ComboboxOption | null

// Add custom option (with duplicate check)
addCustomOption(value, existingOptions): { options, wasAdded, normalizedValue }
```

### Component Usage
```tsx
import { SmartCombobox } from '@/components/ui/SmartCombobox';
import { TRIP_TYPE_OPTIONS } from '@/lib/combobox';

<SmartCombobox
  value={tripType}
  onChange={setTripType}
  options={TRIP_TYPE_OPTIONS}
  label="Trip Type"
  placeholder="Select or type trip type..."
  allowCustom={true}
  fuzzyThreshold={0.6}
  duplicateThreshold={0.85}
/>
```

### Normalization Examples
| Input | Normalized | Matched To |
|-------|------------|------------|
| "honeymoon" | "Honeymoon" | Honeymoon |
| "HONEYMOON" | "Honeymoon" | Honeymoon |
| "famly vacaton" | "Famly Vacaton" | → Suggest "Family Vacation" |
| "thialand" | "Thialand" | → Suggest "Thailand" |
| "beach relax" | "Beach Relax" | → Suggest "Beach / Relaxation" |

---

## Integration Guide

### Adding SmartCombobox to IntakePanel

```tsx
import { SmartCombobox } from '@/components/ui/SmartCombobox';
import { TRIP_TYPE_OPTIONS, DESTINATION_OPTIONS } from '@/lib/combobox';

// Replace existing type field with:
<SmartCombobox
  value={editValues.type}
  onChange={(val) => setEditValues(prev => ({ ...prev, type: val }))}
  options={TRIP_TYPE_OPTIONS}
  label="Trip Type"
  placeholder="Select or type trip type..."
/>

// Replace destination field with:
<SmartCombobox
  value={editValues.destination}
  onChange={(val) => setEditValues(prev => ({ ...prev, destination: val }))}
  options={DESTINATION_OPTIONS}
  label="Destination"
  placeholder="Select or type destination..."
/>
```

### Adding Change History Panel to Workspace

```tsx
import { ChangeHistoryPanel } from '@/components/workspace/panels/ChangeHistoryPanel';

// Add to your workspace layout:
<ChangeHistoryPanel tripId={tripId} trip={trip} />
```

---

## Future Enhancements

1. **Backend Sync**: Move audit logs from localStorage to backend API
2. **Currency Rates**: Fetch real-time exchange rates from API
3. **Collaborative Editing**: Real-time updates when multiple agents work
4. **Change Revert**: Revert to previous value from audit log
5. **Bulk Updates**: Apply same change to multiple trips
6. **Advanced Filters**: Filter inbox by currency, date range, etc.
7. **Field-Level Permissions**: Restrict who can edit certain fields
