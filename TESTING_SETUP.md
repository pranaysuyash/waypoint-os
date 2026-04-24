# Testing Credentials & Setup Notes

## Test Database Credentials

| Email | Password | Details |
|-------|----------|---------|
| newuser@test.com | testpass123 | Created via signup - full account with agency |

**Note:** Just use the signup form at http://localhost:3000/signup to create new test accounts.

## Backend Connection

- **Database URL:** `postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os`
- **Database:** `waypoint_os`
- **User:** `waypoint`

## Startup Commands

```bash
# Start with database connection
DATABASE_URL="postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os" ./dev.sh

# Or just (if DATABASE_URL is exported in environment)
./dev.sh
```

## Key Fixes Applied (2026-04-23)

1. **`spine_api/__init__.py`** - Created empty file to make spine_api a Python package for imports
2. **`src/analytics/review.py`** - Added sys.path setup for `persistence` module import
3. **`spine_api/watchdog.py`** - Added sys.path fix for imports
4. **`frontend/src/lib/api-client.ts`** - Fixed baseUrl to empty string for relative URLs
5. **`frontend/src/app/api/auth/signup/route.ts`** - Created auth proxy route
6. **`frontend/src/app/api/auth/login/route.ts`** - Created auth proxy route

## Troubleshooting

**ModuleNotFoundError: No module named 'persistence'**
- This was fixed by adding project root to sys.path before imports in `src/analytics/review.py`

**404 on /api/auth/signup**
- This was fixed by creating the missing API routes in `frontend/src/app/api/auth/`

**Backend won't start**
- Make sure PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Make sure DATABASE_URL is set when starting