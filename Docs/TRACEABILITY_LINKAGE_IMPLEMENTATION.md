# Traceability Linkage Implementation

## Overview

The traceability linkage system connects TeamPerformanceChart metrics to audit trails, enabling operators to drill down from performance data to individual trip decisions and their supporting context.

## Architecture

### Components

1. **TeamPerformanceChart** (`frontend/src/components/visual/TeamPerformanceChart.tsx`)
   - Interactive chart displaying agent KPIs
   - Clickable metrics: Conversion Rate, Response Time, CSAT, Workload
   - Emits drill-down events via `onDrillDown` callback
   - Supports optional drill-down mode

2. **MetricDrillDownDrawer** (`frontend/src/components/workspace/panels/MetricDrillDownDrawer.tsx`)
   - Right-side drawer that opens when metric is clicked
   - Shows list of trips associated with selected metric
   - Displays trip status, suitability scores, decision reasons
   - Navigates to trip timeline when trip is selected

3. **API Route** (`frontend/src/app/api/insights/agent-trips/route.ts`)
   - Proxies requests to analytics backend
   - Returns trip data filtered by agent and metric
   - Gracefully handles errors by returning empty list

4. **Insights Page** (`frontend/src/app/owner/insights/page.tsx`)
   - Integrates TeamPerformanceChart with drill-down capability
   - Manages drill-down state (open/closed, selected agent/metric)
   - Routes selected trips to workspace timeline view

## Flow

```
User clicks metric on chart
    ↓
TeamPerformanceChart.onDrillDown() fires
    ↓
OwnerInsightsPage opens MetricDrillDownDrawer
    ↓
API fetches trip data: /api/insights/agent-trips?agentId=X&metric=Y
    ↓
Drawer displays list of trips with summaries
    ↓
User clicks trip
    ↓
Navigate to /workspace/[tripId]
    ↓
TimelinePanel displays full decision timeline
```

## Data Structures

### DrillDownMetric
```typescript
interface DrillDownMetric {
  type: 'conversion' | 'response_time' | 'csat' | 'workload';
  value: number;
  label: string;
  tripCount?: number;
}
```

### TripData (API Response)
```typescript
interface TripData {
  tripId: string;
  destinationName?: string;
  status: 'approved' | 'rejected' | 'pending';
  responseTime?: number;
  suitabilityScore?: number;
  decisionReason?: string;
  createdAt?: string;
}
```

## Key Features

### 1. Interactive Metrics
- Metrics have hover effects when drill-down enabled
- Selected agent card highlights with blue border
- Hint text shows "Click on any metric to drill down"

### 2. Trip Drilling
- Supports all four metric types
- Shows trip summary with key details
- Displays decision reason when available
- Status indicators (approved/rejected/pending) with color coding

### 3. Error Handling
- Graceful degradation if analytics service unavailable
- Returns empty trips list instead of error
- Shows user-friendly error message in drawer
- Displays "No trips found" for empty results

### 4. Performance
- Trip data fetched on drawer open
- Minimal loading state flicker (300ms delay)
- No-store cache for fresh data on each drill-down

## Edge Cases

1. **No userId on agent**: Drill-down callbacks not fired if agent lacks userId
2. **Incomplete trip data**: Optional fields safely undefined
3. **Concurrent updates**: State properly isolated per drill-down instance
4. **Network errors**: Fallback to empty state, not error page

## Testing

### Unit Tests (23 new tests)

#### TeamPerformanceChart Drill-Down (10 tests)
- Rendering drill-down hint when enabled
- Click handlers for all metric types
- Callback invocations with correct arguments
- Agent card highlighting on selection
- Cursor styling based on drill-down mode

#### MetricDrillDownDrawer (13 tests)
- Drawer visibility toggling
- Trip data fetching
- Loading and error states
- Trip list rendering
- Trip selection and navigation
- Close button and overlay interactions

#### E2E Tests (3 tests)
- Complete drill-down flow: metric → trips → timeline
- Error handling during drill-down
- Empty results display

### Test Coverage
- 160 passing tests (+ 26 new tests)
- 14 pre-existing failures (unrelated)
- All new functionality covered

## Integration Points

1. **TimelinePanel**: Drill-down destination for trip viewing
2. **useTeamMetrics Hook**: Data source for performance metrics
3. **useRouter Hook**: Navigation to workspace after trip selection
4. **SuitabilitySignal Component**: Could be enhanced with drill-down to flag details

## Future Enhancements

1. **Trip Timeline Linking**: Show which flags caused approval/rejection
2. **Metric Filtering**: Time-range filtering for drill-down data
3. **Bulk Actions**: Select multiple trips from drawer for batch operations
4. **Metric Comparison**: Compare metrics across agents in same drawer
5. **Export**: Export drill-down results to CSV/PDF

## API Contracts

### GET /api/insights/agent-trips
```
Query Parameters:
  - agentId: string (required)
  - metric: 'conversion' | 'response_time' | 'csat' | 'workload' (optional)

Response (200):
{
  agentId: string;
  metric: string;
  trips: TripData[];
  count: number;
}

Error (400):
{
  error: "agentId is required"
}
```

## Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox
- ES2020+ JavaScript

## Accessibility
- ARIA labels on interactive elements
- Keyboard navigation (Tab, Enter)
- Color-independent status indicators
- High contrast colors (GitHub dark theme)

## Performance Notes
- Drawer renders async to prevent UI blocking
- Trip list virtualization recommended for 100+ trips
- API caches disabled to show real-time data

## Deployment Checklist

- [ ] Ensure TimelinePanel is deployed and accessible
- [ ] Verify analytics service endpoints
- [ ] Test drill-down with various agent/metric combinations
- [ ] Verify error handling in staging
- [ ] Monitor API response times
- [ ] Check that trip URLs resolve correctly

## Known Limitations

1. Analytics service must be configured and accessible
2. Trip data availability depends on audit trail completeness
3. Suitability scores require decision stage execution
4. Real-time updates require polling (no WebSocket)
