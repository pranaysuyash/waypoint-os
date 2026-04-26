# API Documentation Part 2: API Design Guidelines

> REST principles, naming conventions, and versioning

**Series:** API Documentation
**Previous:** [Part 1: OpenAPI Specification](./API_DOCUMENTATION_01_OPENAPI.md)
**Next:** [Part 3: Integration Guide](./API_DOCUMENTATION_03_INTEGRATION.md)

---

## Table of Contents

1. [RESTful Principles](#restful-principles)
2. [Naming Conventions](#naming-conventions)
3. [Resource Design](#resource-design)
4. [Pagination](#pagination)
5. [Filtering and Sorting](#filtering-and-sorting)
6. [Versioning Strategy](#versioning-strategy)

---

## RESTful Principles

### Resource-Oriented Design

```typescript
// ✅ Good: Resource-oriented URLs

// Collections
GET    /api/bookings           # List bookings
POST   /api/bookings           # Create booking
GET    /api/bookings/:id       # Get booking
PATCH  /api/bookings/:id       # Update booking
DELETE /api/bookings/:id       # Cancel booking

// Sub-resources
GET    /api/bookings/:id/payments     # Booking payments
POST   /api/bookings/:id/payments     # Add payment
GET    /api/bookings/:id/messages     # Booking messages

// ❌ Bad: RPC-style URLs
POST   /api/createBooking
POST   /api/getBooking
POST   /api/updateBooking
POST   /api/deleteBooking
```

### HTTP Method Semantics

```typescript
// Standard HTTP methods and their usage

interface HTTPMethods {
  // Safe methods - don't modify state
  safe: {
    GET: 'Retrieve resource';
    HEAD: 'Retrieve headers only';
    OPTIONS: 'Retrieve communication options';
  };

  // Idempotent methods - can be applied multiple times safely
  idempotent: {
    GET: 'Retrieve resource';
    HEAD: 'Retrieve headers only';
    PUT: 'Replace resource (entirely)';
    DELETE: 'Delete resource';
  };

  // Non-idempotent methods
  nonIdempotent: {
    POST: 'Create resource or trigger action';
    PATCH: 'Partial update of resource';
  };
}

// Usage examples
GET    /users/123          # Retrieve user (safe, idempotent)
PUT    /users/123          # Replace user (idempotent)
PATCH  /users/123          # Update user partially (non-idempotent)
DELETE /users/123          # Delete user (idempotent)
POST   /users              # Create user (non-idempotent)
```

### Status Code Guidelines

```typescript
// HTTP status codes by category

interface StatusCodes {
  // 2xx - Success
  success: {
    200: 'OK - Request succeeded';
    201: 'Created - Resource created';
    202: 'Accepted - Request accepted for processing';
    204: 'No Content - Successful, no response body';
  };

  // 3xx - Redirection
  redirect: {
    301: 'Moved Permanently - Use new URL';
    304: 'Not Modified - Use cached version';
  };

  // 4xx - Client Error
  clientError: {
    400: 'Bad Request - Invalid request data';
    401: 'Unauthorized - Authentication required';
    403: 'Forbidden - Insufficient permissions';
    404: 'Not Found - Resource does not exist';
    409: 'Conflict - Resource state conflicts';
    422: 'Unprocessable Entity - Semantic errors';
    429: 'Too Many Requests - Rate limit exceeded';
  };

  // 5xx - Server Error
  serverError: {
    500: 'Internal Server Error';
    503: 'Service Unavailable';
  };
}

// Usage guidelines
export function chooseStatusCode(scenario: Scenario): number {
  switch (scenario) {
    // Success cases
    case 'resource_retrieved':
      return 200;
    case 'resource_created':
      return 201;
    case 'async_processing':
      return 202;
    case 'resource_deleted':
      return 204;

    // Client errors
    case 'invalid_json':
      return 400;
    case 'missing_auth':
      return 401;
    case 'insufficient_perms':
      return 403;
    case 'resource_not_found':
      return 404;
    case 'resource_conflict':
      return 409;
    case 'validation_failed':
      return 422;
    case 'rate_limit_exceeded':
      return 429;

    // Server errors
    case 'server_error':
      return 500;
    case 'service_unavailable':
      return 503;
  }
}
```

---

## Naming Conventions

### URL Naming

```typescript
// URL naming rules

interface URLNamingRules {
  // Use lowercase letters
  case: 'lowercase';

  // Use hyphens for multi-word names
  wordSeparator: 'hyphen';

  // Use plural nouns for collections
  collections: 'plural';

  // Use kebab-case for multi-word
  multiWord: 'kebab-case';
}

// Examples
const goodURLs = [
  '/api/bookings',
  '/api/booking-payments',
  '/api/users/:user-id/destinations',
];

const badURLs = [
  '/api/Bookings',              // Don't use PascalCase
  '/api/bookings/',             // Don't use trailing slash
  '/api/booking',               // Use plural for collections
  '/api/bookingPayments',       // Don't use camelCase
  '/api/booking_payments',      // Use kebab-case, not snake_case
];
```

### Property Naming

```typescript
// JSON property naming conventions

interface PropertyNaming {
  // Use snake_case for JSON properties
  format: 'snake_case';

  // Be consistent across the API
  consistency: 'strict';

  // Avoid abbreviations (unless widely known)
  abbreviations: ['id', 'url', 'uri', 'http', 'https'];
}

// Examples
const goodJSON = {
  booking_id: 'bk_123',
  user_id: 'usr_456',
  destination: 'Paris, France',
  check_in_date: '2025-06-01',
  total_price: 1000,
};

const badJSON = {
  bookingId: 'bk_123',        // camelCase (inconsistent with REST conventions)
  bookingID: 'bk_123',        // PascalCase
  uid: 'usr_456',             // Use full names (user_id)
  dest: 'Paris, France',      // Avoid abbreviations
  tp: 1000,                   // Unclear abbreviation
};
```

### Query Parameter Naming

```typescript
// Query parameter naming

interface QueryParamRules {
  // Use snake_case for consistency
  format: 'snake_case';

  // Boolean values use clear names
  booleans: 'is_/has_ prefix';

  // Date ranges use from/to or start/end
  dateRanges: 'from/to or start/end';

  // Sorting uses sort with +/- prefix
  sorting: 'sort with +/- for direction';
}

// Examples
const queryParams = {
  // Filtering
  status: 'confirmed',
  user_id: 'usr_123',
  destination: 'Paris',

  // Boolean flags
  is_active: true,
  has_payment: false,

  // Date ranges
  from: '2025-06-01',
  to: '2025-06-30',

  // Sorting (- for descending)
  sort: '-created_at',
  sort: 'total_price',

  // Pagination
  page: 1,
  limit: 20,

  // Search
  q: 'Paris',
};
```

---

## Resource Design

### Resource Structure

```typescript
// Resource representation guidelines

interface ResourceDesign {
  // Include resource identifier
  id: string;

  // Include canonical URL
  self: string;

  // Include timestamps
  timestamps: {
    created_at: string;
    updated_at: string;
    deleted_at?: string;
  };

  // Use consistent structure
  consistency: 'nested vs flat';
}

// Example: Booking resource
interface BookingResource {
  // Resource identifier
  id: string;

  // Links (HATEOAS)
  links: {
    self: string;
    user: string;
    payments: string;
  };

  // Attributes
  destination: string;
  dates: {
    start: string;
    end: string;
  };
  guests: number;
  status: BookingStatus;

  // Relationships
  relationships: {
    user: {
      data: { id: string; type: string };
      links: { self: string; related: string };
    };
  };

  // Metadata
  meta: {
    created_at: string;
    updated_at: string;
    version: number;
  };
}
```

### Sparse Fieldsets

```typescript
// Allow clients to request only the fields they need

// GET /api/bookings?fields=id,status,total_price

interface FieldsetRequest {
  fields: string[]; // Comma-separated list of fields
}

export function selectFields(resource: any, fields: string[]): any {
  if (!fields || fields.length === 0) {
    return resource; // Return all fields
  }

  const selected = {};
  for (const field of fields) {
    if (field in resource) {
      selected[field] = resource[field];
    }
  }

  return selected;
}

// Example usage
const booking = {
  id: 'bk_123',
  user_id: 'usr_456',
  destination: 'Paris',
  dates: { start: '2025-06-01', end: '2025-06-07' },
  guests: 2,
  status: 'confirmed',
  total_price: 1000,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
};

// GET /api/bookings/bk_123?fields=id,status,total_price
const sparse = selectFields(booking, ['id', 'status', 'total_price']);
// { id: 'bk_123', status: 'confirmed', total_price: 1000 }
```

### Resource Relationships

```typescript
// Including related resources

// GET /api/bookings/bk_123?include=user,payments

interface IncludeRequest {
  include: string[]; // Comma-separated list of relationships
}

interface BookingWithIncludes {
  booking: Booking;
  included?: {
    user?: User;
    payments?: Payment[];
  };
}

export async function getBookingWithIncludes(
  bookingId: string,
  includes: string[]
): Promise<BookingWithIncludes> {
  const booking = await getBooking(bookingId);
  const result: BookingWithIncludes = { booking };

  if (includes.includes('user')) {
    const user = await getUser(booking.user_id);
    result.included = { ...result.included, user };
  }

  if (includes.includes('payments')) {
    const payments = await getPaymentsByBooking(bookingId);
    result.included = { ...result.included, payments };
  }

  return result;
}
```

---

## Pagination

### Cursor-Based Pagination

```typescript
// Cursor-based pagination for large datasets

interface CursorPagination {
  cursor?: string;      // Opaque cursor
  limit?: number;       // Page size (1-100)
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    next_cursor?: string;
    has_next: boolean;
    limit: number;
  };
}

export async function getBookingsCursor(
  cursor?: string,
  limit = 20
): Promise<PaginatedResponse<Booking>> {
  // Decode cursor (contains timestamp and ID)
  let cursorData;
  try {
    cursorData = JSON.parse(Buffer.from(cursor, 'base64').toString());
  } catch {
    cursorData = { timestamp: Date.now(), id: null };
  }

  // Fetch items
  const items = await db.query.bookings.findMany({
    where: cursorData.id
      ? and(
          lt(bookings.createdAt, new Date(cursorData.timestamp)),
          lt(bookings.id, cursorData.id)
        )
      : undefined,
    orderBy: [desc(bookings.createdAt), desc(bookings.id)],
    limit: limit + 1, // Fetch one extra to check for more
  });

  const hasMore = items.length > limit;
  const data = hasMore ? items.slice(0, limit) : items;

  // Create next cursor
  let next_cursor;
  if (hasMore) {
    const lastItem = data[data.length - 1];
    const cursorData = {
      timestamp: lastItem.createdAt.toISOString(),
      id: lastItem.id,
    };
    next_cursor = Buffer.from(JSON.stringify(cursorData)).toString('base64');
  }

  return {
    data,
    pagination: {
      next_cursor,
      has_next: hasMore,
      limit,
    },
  };
}
```

### Offset-Based Pagination

```typescript
// Offset-based pagination (simpler, but less efficient)

interface OffsetPagination {
  page?: number;       // Page number (default: 1)
  limit?: number;      // Items per page (default: 20)
}

export async function getBookingsOffset(
  page = 1,
  limit = 20
): Promise<PaginatedResponse<Booking>> {
  const total = await db.query.bookings.count();
  const totalPages = Math.ceil(total / limit);
  const offset = (page - 1) * limit;

  const data = await db.query.bookings.findMany({
    limit,
    offset,
    orderBy: [desc(bookings.createdAt)],
  });

  return {
    data,
    pagination: {
      page,
      limit,
      total,
      total_pages: totalPages,
      has_next: page < totalPages,
      has_prev: page > 1,
    },
  };
}
```

---

## Filtering and Sorting

### Filtering

```typescript
// Filtering by query parameters

interface FilterOptions {
  // Equality
  status?: string;
  user_id?: string;

  // Comparison
  total_price_gte?: number;
  total_price_lte?: number;

  // Date ranges
  created_from?: string;
  created_to?: string;

  // Array matching
  destinations?: string[];

  // Search
  q?: string;
}

export function buildWhereClause(filters: FilterOptions) {
  const conditions = [];

  if (filters.status) {
    conditions.push(eq(bookings.status, filters.status));
  }

  if (filters.user_id) {
    conditions.push(eq(bookings.userId, filters.user_id));
  }

  if (filters.total_price_gte) {
    conditions.push(gte(bookings.totalPrice, filters.total_price_gte));
  }

  if (filters.total_price_lte) {
    conditions.push(lte(bookings.totalPrice, filters.total_price_lte));
  }

  if (filters.created_from) {
    conditions.push(gte(bookings.createdAt, new Date(filters.created_from)));
  }

  if (filters.created_to) {
    conditions.push(lte(bookings.createdAt, new Date(filters.created_to)));
  }

  return and(...conditions);
}
```

### Sorting

```typescript
// Sorting by query parameters

interface SortOptions {
  sort?: string;  // field name or -field_name for descending
}

export function buildOrderBy(sort?: string) {
  const defaultSort = [desc(bookings.createdAt)];

  if (!sort) {
    return defaultSort;
  }

  const isDescending = sort.startsWith('-');
  const field = sort.replace(/^[+-]/, '');

  const sortMap: Record<string, any> = {
    created_at: bookings.createdAt,
    updated_at: bookings.updatedAt,
    total_price: bookings.totalPrice,
    destination: bookings.destination,
    status: bookings.status,
  };

  const column = sortMap[field];
  if (!column) {
    return defaultSort;
  }

  return isDescending ? [desc(column)] : [asc(column)];
}
```

---

## Versioning Strategy

### URL Versioning

```typescript
// Version in URL path

// Pros:
// - Clear versioning
// - Easy to route different versions
// - Separate documentation per version
//
// Cons:
// - Longer URLs
// - Requires changing client URLs

const versionedRoutes = {
  v1: '/api/v1/bookings',
  v2: '/api/v2/bookings',
};

// Middleware for version routing
export function apiVersion(version: string) {
  return (req: Request, res: Response, next: () => void) => {
    req.apiVersion = version;
    next();
  };
}
```

### Header Versioning

```typescript
// Version in header

// Pros:
// - Cleaner URLs
// - Versioning is optional (default to latest)
//
// Cons:
// - Less discoverable
// - Harder to route

const versionedRequest = new Request('https://api.travelagency.com/bookings', {
  headers: {
    'Accept': 'application/vnd.travelagency.v2+json',
    'API-Version': '2',
  },
});
```

### Our Strategy: URL Versioning with Defaults

```typescript
// Use URL versioning with support for unversioned requests

interface VersionStrategy {
  // Versioned URLs point to specific versions
  versioned: '/api/v2/bookings';

  // Unversioned URLs point to latest stable
  latest: '/api/bookings';

  // Deprecation timeline
  deprecation: {
    v1: 'deprecated until 2026-12-31',
    v2: 'current',
  };
}

// Version detection middleware
export function detectVersion(req: Request): string {
  const url = new URL(req.url);

  // Check URL path
  const versionMatch = url.pathname.match(/^\/api\/v(\d+)\//);
  if (versionMatch) {
    return versionMatch[1];
  }

  // Check header
  const headerVersion = req.headers.get('API-Version');
  if (headerVersion) {
    return headerVersion;
  }

  // Default to latest
  return '2';
}
```

### Version Deprecation

```typescript
// Handle deprecated versions

interface DeprecationHeaders {
  'API-Version': string;
  'Sunset': string;           // Date when version is retired
  'Deprecation': string;       // Warning message
  'Link': string;              // Link to migration guide
}

export function handleDeprecatedVersion(req: Request): Response | null {
  const version = detectVersion(req);

  if (version === '1') {
    return new Response(
      JSON.stringify({
        error: 'API v1 is deprecated',
        message: 'Please migrate to API v2',
        migration_guide: 'https://docs.travelagency.com/api/v1-to-v2',
      }),
      {
        status: 200,
        headers: {
          'API-Version': '1',
          'Sunset': '2026-12-31',
          'Deprecation': 'true',
          'Link': '<https://docs.travelagency.com/api/v2>; rel="successor-version"',
        },
      }
    );
  }

  return null;
}
```

---

## Summary

API design guidelines for the travel agency platform:

- **RESTful**: Resource-oriented URLs, proper HTTP methods
- **Naming**: lowercase URLs, snake_case properties, kebab-case multi-word
- **Pagination**: Cursor-based for large datasets, offset-based for small
- **Filtering**: Query parameters with clear naming (gte, lte, from, to)
- **Sorting**: sort parameter with +/- for direction
- **Versioning**: URL-based with /api/v2/ pattern, unversioned points to latest

**Key Principles:**
- Consistency over cleverness
- Clear, predictable patterns
- Good documentation
- Backward compatibility when possible

---

**Next:** [Part 3: Integration Guide](./API_DOCUMENTATION_03_INTEGRATION.md) — Authentication, SDKs, and webhooks
