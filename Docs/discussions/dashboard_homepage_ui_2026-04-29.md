# Dashboard/Homepage UI — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, what YOU see on login  
**Approach:** Independent analysis — minimum viable dashboard  

---

## 1. The Core Truth: YOU Need Quick Overview+

### Your Reality (Solo Dev))

| Widget | Why You Need It | Priority |
|--------|--------------|----------|
| **Today's Tasks** | "Reply to Ravi, send voucher" | 🔴 CRITICAL |
| **This Month's Revenue** | ₹1.2L vs ₹1.5L last month | 🔴 CRITICAL |
| **Alerts Summary** | 2 VIP messages, 1 EMI overdue | HIGH |
| **Recent Enquiries** | 5 latest (reply within 4h) | HIGH |
| **Upcoming Travels** | Ravi → Bali tomorrow! | MEDIUM |
| **Quick Stats** | 20 enquiries this month | LOW |

**My insight:**   
Dashboard = **YOUR command center**.   
3 widgets = enough (today's tasks, revenue, alerts).

---

## 2. My Dashboard Model (Lean, Practical))+

### What YOU See (5 Widgets Max))+

```typescript+
// app/page.tsx (homepage)+
import { useQuery } from "@tanstack/react-query";

export default function Dashboard() {
  // Fetch data+
  const { data: stats } = useQuery(['dashboard-stats'], fetchStats);
  const { data: tasks } = useQuery(['today-tasks'], fetchTodayTasks);
  const { data: alerts } = useQuery(['alerts'], fetchAlerts);

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1>Welcome back, Ravi! 👋</h1>
      <p className="text-gray-500 mb-6">Tuesday, April 29, 2026</p>

      {/* Row 1: Quick Stats */}      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard+
          title="This Month's Revenue"
          value={`₹${stats?.revenue?.toLocaleString()}`}
          change={stats?.revenue_change}%}
          icon="💰"
        />
        <StatCard+
          title="Enquiries"+
          value={stats?.enquiry_count}
          change={stats?.enquiry_change}%}
          icon="📩"
        />
        <StatCard+
          title="Conversion Rate"+
          value={`${stats?.conversion_rate?.toFixed(1)}%`}
          change={stats?.conversion_change}%}
          icon="📊"
        />
      </div>

      {/* Row 2: Today's Tasks + Alerts */}      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <TaskList tasks={tasks?.items || []} />
        <AlertSummary alerts={alerts?.items || []} />
      </div>

      {/* Row 3: Recent Enquiries */}      
      <RecentEnquiries />
    </div>
  );
}
```

**My insight:**   
3 rows = **5 minutes coding**.   
StatCard = reuse everywhere.

---

### StatCard Component (Reusable))+

```typescript+
// components/StatCard.tsx+
export function StatCard({ title, value, change, icon }: {
  title: string;
  value: string;
  change: number;
  icon: string;
}) {
  const isPositive = change >= 0;

  return (
    <div className="border rounded p-4 bg-white shadow-sm">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm text-gray-500">{title}</h3>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? '↑' : '↓'} {Math.abs(change)}% vs last month
      </p>
    </div>
  );
}
```

**My insight:**   
`change` = green ↑ or red ↓.   
Reuse for ALL stats.

---

## 3. Today's Tasks Widget (CRITICAL))+

### What YOU See (Actionable))+

```typescript+
// components/TaskList.tsx+
export function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <div className="border rounded p-4 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Today's Tasks 📋</h2>
      {tasks.length === 0 ? (
        <p className="text-gray-500">No tasks! Enjoy ☕️</p>
      ) : (
        <ul className="space-y-2">
          {tasks.map((task) => (
            <li key={task.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${+
                  task.priority === 'CRITICAL' ? 'bg-red-500' :+
                  task.priority === 'HIGH' ? 'bg-orange-500' : 'bg-blue-500'
                }`}></span>
                <span className={task.status === 'DONE' ? 'line-through text-gray-400' : ''}>
                  {task.title}
                </span>
              </div>
              <button+
                onClick={() => markDone(task.id)}
                className="text-sm text-blue-600"
              >
                {task.status === 'DONE' ? '↩️' : '✅'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

**My insight:**   
Priority = red/orange/blue dot.   
Click ✅ = mark done (optimistic UI).

---

### Task Data (From API))+

```typescript+
// lib/api-client.ts+
export async function fetchTodayTasks() {
  const res = await fetch('/api/dashboard/today-tasks');
  return res.json();
}

// API returns:+
[
  {
    "id": "task-001",
    "title": "Reply to Ravi (VIP) — Bali itinerary",
    "priority": "CRITICAL",
    "enquiry_id": "eq-042",
    "due_in": "30 mins",
    "status": "PENDING"
  },
  {
    "id": "task-002",
    "title": "Send voucher to Priya — booking BK-001",
    "priority": "HIGH",
    "booking_id": "bk-001",
    "due_in": "2 hours",
    "status": "PENDING"
  },
  {
    "id": "task-003",
    "title": "Follow up: Phuket Paradise didn't reply",
    "priority": "MEDIUM",
    "enquiry_id": "eq-038",
    "due_in": "4 hours",
    "status": "PENDING"
  }
]
```

**My insight:**   
`due_in` = countdown timer.   
Click title → opens enquiry/booking.

---

## 4. Alerts Summary Widget (HIGH))+

### What YOU See (Immediate))+

```typescript+
// components/AlertSummary.tsx+
export function AlertSummary({ alerts }: { alerts: Alert[] }) {
  const critical = alerts.filter(a => a.severity === 'CRITICAL').length;
  const high = alerts.filter(a => a.severity === 'HIGH').length;
  const medium = alerts.filter(a => a.severity === 'MEDIUM').length;

  return (
    <div className="border rounded p-4 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Alerts Summary 🚨</h2>
      <div className="flex gap-4 mb-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">{critical}</p>
          <p className="text-xs text-gray-500">Critical</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-orange-600">{high}</p>
          <p className="text-xs text-gray-500">High</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">{medium}</p>
          <p className="text-xs text-gray-500">Medium</p>
        </div>
      </div>
      <button+
        onClick={() => router.push('/alerts')}
        className="w-full bg-red-50 text-red-600 p-2 rounded text-sm"
      >
        View All Alerts →
      </button>
    </div>
  );
}
```

**My insight:**   
3 numbers = immediate status.   
Click "View All" → `/alerts` page.

---

## 5. Recent Enquiries Widget (HIGH))+

### What YOU See (Quick Access))+

```typescript+
// components/RecentEnquiries.tsx+
export function RecentEnquiries() {
  const { data: enquiries } = useQuery(['recent-enquiries'], () =>
    fetch('/api/enquiries?limit=5').then(r => r.json())
  );

  return (
    <div className="border rounded p-4 bg-white shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Recent Enquiries 📩</h2>
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left">Customer</th>
            <th className="text-left">Destination</th>
            <th className="text-left">Status</th>
            <th className="text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {enquiries?.map((eq) => (
            <tr key={eq.enquiry_id} className="border-t">
              <td className="py-2">
                {eq.customer_name}
                {eq.is_vip && <span className="ml-1 text-xs bg-yellow-100 px-1 rounded">VIP</span>}
              </td>
              <td className="py-2">{eq.destination}</td>
              <td className="py-2">
                <span className={`text-xs px-2 py-1 rounded ${
                  eq.status === 'RECEIVED' ? 'bg-blue-100 text-blue-800' :+
                  eq.status === 'DRAFTING' ? 'bg-yellow-100 text-yellow-800' :+
                  'bg-green-100 text-green-800'
                }`}>
                  {eq.status}
                </span>
              </td>
              <td className="py-2 text-right">
                <button+
                  onClick={() => router.push(`/enquiries/${eq.enquiry_id}`)}
                  className="text-sm text-blue-600"
                >
                  Open →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**My insight:**   
VIP badge = yellow dot.   
Click "Open →" = instant access.

---

## 6. API Endpoint (5 Minutes))+

### Backend: Dashboard Data))+

```python+
# spine_api/routers/dashboard.py+

router = APIRouter()

@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Return stats for dashboard."""
    return {
        "revenue": 1200000,  # ₹12L+
        "revenue_change": 12.5,  # +12.5%+
        "enquiry_count": 20,
        "enquiry_change": -5.0,  # -5%+
        "conversion_rate": 49.0,
        "conversion_change": 2.0  # +2%+
    }

@router.get("/api/dashboard/today-tasks")
async def get_today_tasks():
    """Return today's tasks."""
    return [
        {
            "id": "task-001",
            "title": "Reply to Ravi (VIP) — Bali itinerary",
            "priority": "CRITICAL",
            "enquiry_id": "eq-042",
            "due_in": "30 mins",
            "status": "PENDING"
        }
    ]

@router.get("/api/enquiries")
async def get_enquiries(limit: int = 5):
    """Return recent enquiries."""
    enquiries = db.get_recent_enquiries(limit)
    return [
        {
            "enquiry_id": eq.id,
            "customer_name": eq.customer_name_cache,
            "destination": eq.destination_cache,
            "status": eq.status,
            "is_vip": eq.customer_segment == "VIP"
        }
        for eq in enquiries
    ]
```

**My insight:**   
Mock data = start. Replace with real DB calls later.   
`due_in` = calculated from `enquiry.created_at`.

---

## 7. Current State vs Dashboard Model)+-

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Homepage | Next.js scaffold | 3-row dashboard |
| Stats widgets | None | Revenue, Enquiries, Conversion |
| Today's tasks | None | 5 tasks, priority dots |
| Alerts summary | None | Critical/High/Medium counts |
| Recent enquiries | None | 5 latest, VIP badge |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Dashboard now? | Yes / No | **NOW** — 10 mins, YOUR command center |
| Stats widgets? | 3 / 5 / 10 | **3** — revenue, enquiries, conversion |
| Today's tasks? | Yes / No | **YES** — YOUR todo list |
| Alerts summary? | Yes / No | **YES** — immediate status |
| Recent enquiries? | 5 / 10 | **5** — quick access |

---

## 9. FINAL COUNT: What's Been DONE vs LEFT+

### ✅ DONE (42 Discussion Docs):
1. Enquiry types & stages
2. Channels & acquisition (user's inputs)
3. Customer model
4. Human agent model (SKIPED)
5. Vendor model
6. Communication model
7. Booking model
8. System architecture
9. Payments (status-only)
10. Notifications & alerts
11. Roles & Permissions (SKIPED)
12. Search & Discovery
13. Reporting & Analytics
14. Audit & Compliance
15. Testing Strategy
16. Mobile & PWA
17. Backup & Security
18. Integrations
19. Onboarding
20. Performance & Scaling
21. Localization & Offline
22. Domain & Hosting & Legal
23. Marketing & SEO
24. Monitoring & Alerting
25. Business Continuity
26. Third-Party Risks
27. API Documentation
28. Environment Management
29. CI/CD Pipeline
30. Code Quality Tools
31. Dependency Management
32. Logging & Observability
33. Error Handling & UX
34. Data Export & Portability
35. Session Management
36. Rate Limiting
37. Feature Flags & Toggles
38. Implementation Roadmap (LIVING)
39. Pricing Engine
40. Itinerary Builder
41. Document Generation
42. **Dashboard/Homepage UI** (just wrote)

### ❌ LEFT (Not Yet Written):
1. **Calendar & Availability** (internal booking calendar)
2. **FINAL Code Check** (check existing code against 42 docs)

---

## 10. Next Step: Calendar & Availability+

Key questions for next discussion:
1. **Internal calendar** — which dates are booked?
2. **Hotel availability** — which hotels are full?
3. **Google Calendar sync** — already discussed, but internal view?
4. **Solo dev reality** — what's the MINIMUM calendar needed?

---

**Next file:** `Docs/discussions/calendar_availability_2026-04-29.md`
