# API Documentation Part 4: Error Handling

> Error codes, responses, and troubleshooting

**Series:** API Documentation
**Previous:** [Part 3: Integration Guide](./API_DOCUMENTATION_03_INTEGRATION.md)

---

## Table of Contents

1. [Error Response Format](#error-response-format)
2. [HTTP Status Codes](#http-status-codes)
3. [Error Codes Reference](#error-codes-reference)
4. [Common Errors](#common-errors)
5. [Retry Logic](#retry-logic)
6. [Troubleshooting Guide](#troubleshooting-guide)

---

## Error Response Format

### Standard Error Structure

```typescript
// All API errors follow this structure

interface ApiError {
  // Error identifier
  error: string;

  // Human-readable message
  message: string;

  // Detailed error code
  code: string;

  // HTTP status code
  status: number;

  // Request ID for support
  request_id: string;

  // Additional details
  details?: ErrorDetails;

  // Help links
  help?: {
    url: string;
    title: string;
  };
}

interface ErrorDetails {
  // Field-specific errors
  fields?: Record<string, string[]>;

  // Validation constraints
  constraints?: Record<string, unknown>;

  // Suggested corrections
  suggestions?: string[];

  // Related resources
  related?: Array<{
    resource: string;
    id: string;
  }>;
}

// Example error response
{
  "error": "validation_error",
  "message": "The request data is invalid.",
  "code": "VALIDATION_ERROR",
  "status": 422,
  "request_id": "req_1234567890abcdef",
  "details": {
    "fields": {
      "email": ["Must be a valid email address"],
      "check_in": ["Must be a future date", "Cannot be more than 1 year in the future"]
    },
    "suggestions": [
      "Use format: YYYY-MM-DD for dates",
      "Email should contain @ and a domain"
    ]
  },
  "help": {
    "url": "https://docs.travelagency.com/api/errors/validation",
    "title": "Understanding Validation Errors"
  }
}
```

### Error Types

```typescript
// Error categorization

interface ErrorTypes {
  // Client errors (4xx)
  client: {
    validation: 'Invalid request data';
    authentication: 'Missing or invalid credentials';
    authorization: 'Insufficient permissions';
    not_found: 'Resource does not exist';
    conflict: 'Resource state conflict';
    rate_limit: 'Too many requests';
  };

  // Server errors (5xx)
  server: {
    internal: 'Unexpected server error';
    service_unavailable: 'Service temporarily down';
    gateway_timeout: 'Upstream service timeout';
    database: 'Database operation failed';
  };
}

// Type guards
function isClientError(error: ApiError): boolean {
  return error.status >= 400 && error.status < 500;
}

function isServerError(error: ApiError): boolean {
  return error.status >= 500;
}

function isRetriableError(error: ApiError): boolean {
  return [
    408, // Request Timeout
    429, // Too Many Requests
    500, // Internal Server Error
    502, // Bad Gateway
    503, // Service Unavailable
    504, // Gateway Timeout
  ].includes(error.status);
}
```

---

## HTTP Status Codes

### 2xx Success Codes

```typescript
interface SuccessCodes {
  200: {
    name: 'OK';
    description: 'Request succeeded';
    usage: 'GET, PATCH, DELETE requests';
    example: 'Retrieved booking details';
  };

  201: {
    name: 'Created';
    description: 'Resource created successfully';
    usage: 'POST requests';
    example: 'Booking created';
  };

  202: {
    name: 'Accepted';
    description: 'Request accepted for processing';
    usage: 'Async operations';
    example: 'Payment processing started';
  };

  204: {
    name: 'No Content';
    description: 'Success, no response body';
    usage: 'DELETE requests';
    example: 'Booking cancelled';
  };
}
```

### 4xx Client Error Codes

```typescript
interface ClientErrorCodes {
  400: {
    name: 'Bad Request';
    description: 'Invalid request data';
    causes: ['Malformed JSON', 'Invalid query params', 'Missing required fields'];
    solution: 'Check request format and data';
  };

  401: {
    name: 'Unauthorized';
    description: 'Authentication required or failed';
    causes: ['Missing token', 'Expired token', 'Invalid token'];
    solution: 'Provide valid access token';
  };

  403: {
    name: 'Forbidden';
    description: 'Insufficient permissions';
    causes: ['User lacks permission', 'Resource access restricted'];
    solution: 'Check user permissions';
  };

  404: {
    name: 'Not Found';
    description: 'Resource does not exist';
    causes: ['Invalid ID', 'Resource deleted', 'Wrong endpoint'];
    solution: 'Verify resource ID and endpoint';
  };

  409: {
    name: 'Conflict';
    description: 'Resource state conflicts';
    causes: ['Duplicate booking', 'Version conflict', 'State mismatch'];
    solution: 'Resolve conflict before retrying';
  };

  422: {
    name: 'Unprocessable Entity';
    description: 'Semantic validation errors';
    causes: ['Invalid date range', 'Invalid email', 'Constraint violation'];
    solution: 'Fix validation errors';
  };

  429: {
    name: 'Too Many Requests';
    description: 'Rate limit exceeded';
    causes: ['Too many requests', 'Burst traffic'];
    solution: 'Wait and retry with backoff';
  };
}
```

### 5xx Server Error Codes

```typescript
interface ServerErrorCodes {
  500: {
    name: 'Internal Server Error';
    description: 'Unexpected server error';
    causes: ['Unhandled exception', 'System failure'];
    solution: 'Report to support with request_id';
  };

  502: {
    name: 'Bad Gateway';
    description: 'Invalid response from upstream';
    causes: ['Upstream service failure', 'Network issues'];
    solution: 'Retry with backoff';
  };

  503: {
    name: 'Service Unavailable';
    description: 'Service temporarily unavailable';
    causes: ['Maintenance', 'Overloaded', 'Upstream down'];
    solution: 'Retry after delay';
  };

  504: {
    name: 'Gateway Timeout';
    description: 'Upstream service timeout';
    causes: ['Slow upstream', 'Network latency'];
    solution: 'Retry with longer timeout';
  };
}
```

---

## Error Codes Reference

### Authentication Errors

```typescript
// AUTH_* error codes

interface AuthErrors {
  AUTH_MISSING_TOKEN: {
    code: 'AUTH_MISSING_TOKEN';
    status: 401;
    message: 'Authentication token is required';
    solution: 'Include Authorization header with Bearer token';
  };

  AUTH_INVALID_TOKEN: {
    code: 'AUTH_INVALID_TOKEN';
    status: 401;
    message: 'Authentication token is invalid';
    solution: 'Obtain new token via login or refresh';
  };

  AUTH_EXPIRED_TOKEN: {
    code: 'AUTH_EXPIRED_TOKEN';
    status: 401;
    message: 'Authentication token has expired';
    solution: 'Refresh token using refresh endpoint';
  };

  AUTH_INVALID_CREDENTIALS: {
    code: 'AUTH_INVALID_CREDENTIALS';
    status: 401;
    message: 'Invalid email or password';
    solution: 'Check credentials and try again';
  };

  AUTH_REFRESH_FAILED: {
    code: 'AUTH_REFRESH_FAILED';
    status: 401;
    message: 'Token refresh failed';
    solution: 'Re-authenticate with login';
  };
}
```

### Validation Errors

```typescript
// VALIDATION_* error codes

interface ValidationErrors {
  VALIDATION_ERROR: {
    code: 'VALIDATION_ERROR';
    status: 422;
    message: 'Request data validation failed';
    solution: 'Fix field-specific validation errors';
  };

  VALIDATION_INVALID_EMAIL: {
    code: 'VALIDATION_INVALID_EMAIL';
    status: 422;
    message: 'Email address is invalid';
    solution: 'Provide valid email format (user@domain.com)';
  };

  VALIDATION_INVALID_DATE: {
    code: 'VALIDATION_INVALID_DATE';
    status: 422;
    message: 'Date format is invalid';
    solution: 'Use YYYY-MM-DD format';
  };

  VALIDATION_DATE_RANGE: {
    code: 'VALIDATION_DATE_RANGE';
    status: 422;
    message: 'Check-out date must be after check-in date';
    solution: 'Provide valid date range';
  };

  VALIDATION_PAST_DATE: {
    code: 'VALIDATION_PAST_DATE';
    status: 422;
    message: 'Date cannot be in the past';
    solution: 'Use future dates only';
  };

  VALIDATION_MISSING_FIELD: {
    code: 'VALIDATION_MISSING_FIELD';
    status: 422;
    message: 'Required field is missing';
    solution: 'Include all required fields';
  };

  VALIDATION_INVALID_FORMAT: {
    code: 'VALIDATION_INVALID_FORMAT';
    status: 422;
    message: 'Data format is invalid';
    solution: 'Check data format matches expected schema';
  };
}
```

### Resource Errors

```typescript
// RESOURCE_* error codes

interface ResourceErrors {
  RESOURCE_NOT_FOUND: {
    code: 'RESOURCE_NOT_FOUND';
    status: 404;
    message: 'Requested resource does not exist';
    solution: 'Verify resource ID and endpoint';
  };

  RESOURCE_ALREADY_EXISTS: {
    code: 'RESOURCE_ALREADY_EXISTS';
    status: 409;
    message: 'Resource already exists';
    solution: 'Use update instead of create, or use different identifier';
  };

  RESOURCE_VERSION_CONFLICT: {
    code: 'RESOURCE_VERSION_CONFLICT';
    status: 409;
    message: 'Resource version conflict';
    solution: 'Fetch latest version and retry';
  };

  RESOURCE_LOCKED: {
    code: 'RESOURCE_LOCKED';
    status: 409;
    message: 'Resource is locked by another operation';
    solution: 'Wait and retry';
  };

  RESOURCE_STATE_INVALID: {
    code: 'RESOURCE_STATE_INVALID';
    status: 422;
    message: 'Resource state does not allow this operation';
    solution: 'Check resource state and valid transitions';
  };
}
```

### Booking Errors

```typescript
// BOOKING_* error codes

interface BookingErrors {
  BOOKING_NOT_FOUND: {
    code: 'BOOKING_NOT_FOUND';
    status: 404;
    message: 'Booking does not exist';
    solution: 'Verify booking ID';
  };

  BOOKING_NOT_AVAILABLE: {
    code: 'BOOKING_NOT_AVAILABLE';
    status: 422;
    message: 'Accommodation not available for selected dates';
    solution: 'Choose different dates or accommodation';
  };

  BOOKING_ALREADY_CANCELLED: {
    code: 'BOOKING_ALREADY_CANCELLED';
    status: 422;
    message: 'Booking is already cancelled';
    solution: 'No action needed';
  };

  BOOKING_CANNOT_CANCEL: {
    code: 'BOOKING_CANNOT_CANCEL';
    status: 422;
    message: 'Booking cannot be cancelled';
    solution: 'Check cancellation policy and deadline';
  };

  BOOKING_PAYMENT_REQUIRED: {
    code: 'BOOKING_PAYMENT_REQUIRED';
    status: 422;
    message: 'Payment required to confirm booking';
    solution: 'Complete payment process';
  };

  BOOKING_EXPIRED: {
    code: 'BOOKING_EXPIRED';
    status: 422;
    message: 'Booking reservation has expired';
    solution: 'Create new booking';
  };
}
```

### Payment Errors

```typescript
// PAYMENT_* error codes

interface PaymentErrors {
  PAYMENT_FAILED: {
    code: 'PAYMENT_FAILED';
    status: 422;
    message: 'Payment processing failed';
    solution: 'Try different payment method or contact bank';
  };

  PAYMENT_INSUFFICIENT_FUNDS: {
    code: 'PAYMENT_INSUFFICIENT_FUNDS';
    status: 422;
    message: 'Insufficient funds for payment';
    solution: 'Use different payment method or add funds';
  };

  PAYMENT_CARD_DECLINED: {
    code: 'PAYMENT_CARD_DECLINED';
    status: 422;
    message: 'Card was declined';
    solution: 'Use different card or contact bank';
  };

  PAYMENT_EXPIRED_CARD: {
    code: 'PAYMENT_EXPIRED_CARD';
    status: 422;
    message: 'Card has expired';
    solution: 'Use different card or update card details';
  };

  PAYMENT_INVALID_CVC: {
    code: 'PAYMENT_INVALID_CVC';
    status: 422;
    message: 'CVC is invalid';
    solution: 'Verify CVC and try again';
  };

  PAYMENT_ALREADY_PROCESSED: {
    code: 'PAYMENT_ALREADY_PROCESSED';
    status: 409;
    message: 'Payment has already been processed';
    solution: 'Check payment status before retrying';
  };

  PAYMENT_REFUND_FAILED: {
    code: 'PAYMENT_REFUND_FAILED';
    status: 422;
    message: 'Refund processing failed';
    solution: 'Contact support';
  };

  PAYMENT_AMOUNT_INVALID: {
    code: 'PAYMENT_AMOUNT_INVALID';
    status: 422;
    message: 'Payment amount is invalid';
    solution: 'Verify amount is positive and within limits';
  };
}
```

### Rate Limit Errors

```typescript
// RATE_LIMIT_* error codes

interface RateLimitErrors {
  RATE_LIMIT_EXCEEDED: {
    code: 'RATE_LIMIT_EXCEEDED';
    status: 429;
    message: 'Rate limit has been exceeded';
    solution: 'Wait and retry with backoff';
  };

  RATE_LIMIT_DAILY_EXCEEDED: {
    code: 'RATE_LIMIT_DAILY_EXCEEDED';
    status: 429;
    message: 'Daily rate limit has been exceeded';
    solution: 'Wait until daily limit resets (midnight UTC)';
  };

  RATE_LIMIT_BURST_EXCEEDED: {
    code: 'RATE_LIMIT_BURST_EXCEEDED';
    status: 429;
    message: 'Burst rate limit has been exceeded';
    solution: 'Add delay between requests';
  };
}
```

---

## Common Errors

### Invalid Token Error

```typescript
// Error: Expired access token

{
  "error": "authentication_error",
  "message": "Authentication token has expired",
  "code": "AUTH_EXPIRED_TOKEN",
  "status": 401,
  "request_id": "req_1234567890abcdef"
}

// Solution: Refresh the token
async function handleExpiredToken() {
  try {
    const newToken = await refreshToken();
    localStorage.setItem('access_token', newToken);

    // Retry original request
    return await api.request(originalRequest);
  } catch (error) {
    // Refresh failed, redirect to login
    window.location.href = '/login';
  }
}
```

### Validation Error

```typescript
// Error: Invalid booking data

{
  "error": "validation_error",
  "message": "The request data is invalid.",
  "code": "VALIDATION_ERROR",
  "status": 422,
  "request_id": "req_1234567890abcdef",
  "details": {
    "fields": {
      "check_in": ["Must be a future date", "Cannot be more than 1 year in the future"],
      "check_out": ["Must be after check-in date"],
      "guests.adults": ["Must be at least 1"]
    },
    "suggestions": [
      "Use format: YYYY-MM-DD for dates",
      "Check-out must be at least 1 day after check-in"
    ]
  }
}

// Solution: Display validation errors to user
function displayValidationErrors(error: ApiError) {
  const fieldErrors = error.details?.fields || {};

  for (const [field, messages] of Object.entries(fieldErrors)) {
    const input = document.querySelector(`[name="${field}"]`);
    if (input) {
      input.setCustomValidity(messages[0]);
      input.reportValidity();
    }
  }

  // Show suggestions
  if (error.details?.suggestions) {
    showSuggestions(error.details.suggestions);
  }
}
```

### Rate Limit Error

```typescript
// Error: Too many requests

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit has been exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "status": 429,
  "request_id": "req_1234567890abcdef",
  "details": {
    "retry_after": 60,
    "limit": 100,
    "window": "1 hour"
  }
}

// Solution: Implement exponential backoff
async function requestWithBackoff<T>(
  request: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  let attempt = 0;
  let delay = 1000; // Start with 1 second

  while (attempt < maxRetries) {
    try {
      return await request();
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        attempt++;
        const retryAfter = error.details?.retry_after || delay;

        if (attempt >= maxRetries) {
          throw new Error('Max retries exceeded');
        }

        await sleep(retryAfter * 1000);
        delay *= 2; // Exponential backoff
      } else {
        throw error;
      }
    }
  }

  throw new Error('Max retries exceeded');
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
```

### Not Found Error

```typescript
// Error: Resource not found

{
  "error": "not_found",
  "message": "Requested resource does not exist",
  "code": "RESOURCE_NOT_FOUND",
  "status": 404,
  "request_id": "req_1234567890abcdef",
  "details": {
    "resource_type": "booking",
    "resource_id": "bk_invalid"
  }
}

// Solution: Handle gracefully
async function getBookingOrRedirect(bookingId: string) {
  try {
    return await api.get(`/api/bookings/${bookingId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      // Redirect to not found page
      window.location.href = '/404';
      return null;
    }
    throw error;
  }
}
```

---

## Retry Logic

### Exponential Backoff

```typescript
// Retry strategy with exponential backoff

interface RetryConfig {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableErrors: number[];
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 5,
  initialDelay: 1000, // 1 second
  maxDelay: 60000, // 60 seconds
  backoffMultiplier: 2,
  retryableErrors: [408, 429, 500, 502, 503, 504],
};

async function retryWithBackoff<T>(
  request: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const finalConfig = { ...defaultRetryConfig, ...config };
  let delay = finalConfig.initialDelay;

  for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
    try {
      return await request();
    } catch (error) {
      if (error instanceof ApiError) {
        // Check if error is retryable
        if (!finalConfig.retryableErrors.includes(error.status)) {
          throw error;
        }

        // Don't retry on last attempt
        if (attempt >= finalConfig.maxRetries) {
          throw error;
        }

        // Check for Retry-After header
        const retryAfter = error.response?.headers.get('Retry-After');
        if (retryAfter) {
          delay = parseInt(retryAfter, 10) * 1000;
        }

        // Wait before retrying
        await sleep(Math.min(delay, finalConfig.maxDelay));

        // Calculate next delay with exponential backoff
        delay *= finalConfig.backoffMultiplier;

        // Add jitter to prevent thundering herd
        delay += Math.random() * 1000;
      } else {
        throw error;
      }
    }
  }

  throw new Error('Max retries exceeded');
}
```

### Idempotent Retry

```typescript
// Safe retry for idempotent operations

class IdempotentRequest {
  private seenRequests = new Map<string, Promise<unknown>>();

  async request<T>(
    key: string,
    requestFn: () => Promise<T>
  ): Promise<T> {
    // Check if request is in flight
    if (this.seenRequests.has(key)) {
      return this.seenRequests.get(key) as Promise<T>;
    }

    // Create new request
    const promise = requestFn()
      .then((result) => {
        this.seenRequests.delete(key);
        return result;
      })
      .catch((error) => {
        this.seenRequests.delete(key);
        throw error;
      });

    this.seenRequests.set(key, promise);

    return promise;
  }
}

// Usage for payment operations
const idempotent = new IdempotentRequest();

async function createPayment(bookingId: string, amount: number) {
  const idempotencyKey = `${bookingId}-${amount}-${Date.now()}`;

  return idempotent.request(
    idempotencyKey,
    () => api.post('/api/payments', {
      booking_id: bookingId,
      amount,
      idempotency_key: idempotencyKey,
    })
  );
}
```

---

## Troubleshooting Guide

### Debug Mode

```typescript
// Enable debug logging

class DebugApiClient extends ApiClient {
  private debug: boolean;

  constructor(config: ApiClientConfig & { debug?: boolean }) {
    super(config);
    this.debug = config.debug || false;
  }

  override async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const requestId = crypto.randomUUID();
    const startTime = Date.now();

    if (this.debug) {
      console.log(`[${requestId}] Request:`, {
        endpoint,
        method: options.method,
        headers: options.headers,
        body: options.body,
      });
    }

    try {
      const response = await super.request<T>(endpoint, options);

      if (this.debug) {
        const duration = Date.now() - startTime;
        console.log(`[${requestId}] Response:`, {
          duration: `${duration}ms`,
          data: response,
        });
      }

      return response;
    } catch (error) {
      if (this.debug) {
        const duration = Date.now() - startTime;
        console.error(`[${requestId}] Error:`, {
          duration: `${duration}ms`,
          error,
        });
      }
      throw error;
    }
  }
}

// Usage
const api = new DebugApiClient({
  baseURL: 'https://api.travelagency.com',
  getAccessToken: async () => getToken(),
  debug: true, // Enable debug logging
});
```

### Common Issues and Solutions

```typescript
// Issue: CORS errors

interface CORSIssue {
  problem: 'CORS policy blocks request';
  cause: 'API not configured for your origin';
  solution: [
    'Add your domain to allowed origins in API settings',
    'Or proxy requests through your backend',
  ];
}

// Solution: Backend proxy
// Instead of calling API directly from frontend:
// const response = await fetch('https://api.travelagency.com/api/bookings');

// Proxy through your backend:
const response = await fetch('/api/proxy/bookings', {
  headers: {
    'X-API-Endpoint': 'https://api.travelagency.com/api/bookings',
  },
});
```

```typescript
// Issue: Timeout errors

interface TimeoutIssue {
  problem: 'Request timeout';
  cause: 'Slow network or server';
  solution: [
    'Increase timeout duration',
    'Implement retry logic',
    'Check network connectivity',
  ];
}

// Solution: Configurable timeout
class TimeoutApiClient extends ApiClient {
  private timeout: number;

  constructor(config: ApiClientConfig & { timeout?: number }) {
    super(config);
    this.timeout = config.timeout || 30000; // 30 seconds default
  }

  override async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      return await super.request<T>(endpoint, {
        ...options,
        signal: controller.signal,
      });
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }
}
```

```typescript
// Issue: Large payload errors

interface LargePayloadIssue {
  problem: 'Request payload too large';
  cause: 'Sending too much data in single request';
  solution: [
    'Use pagination',
    'Request only needed fields',
    'Split into multiple requests',
  ];
}

// Solution: Sparse fieldsets
const booking = await api.get('/api/bookings/bk_123?fields=id,status,total_price');

// Instead of getting all fields
const bookingFull = await api.get('/api/bookings/bk_123');
```

### Getting Support

```typescript
// Always include request_id in support requests

async function handleApiError(error: ApiError): Promise<void> {
  // Log error details
  console.error('API Error:', {
    code: error.code,
    status: error.status,
    message: error.message,
    request_id: error.request_id,
  });

  // Show user-friendly message
  showErrorMessage(error.message);

  // If server error, report to support
  if (isServerError(error)) {
    await reportToSupport({
      error_code: error.code,
      request_id: error.request_id,
      timestamp: new Date().toISOString(),
      user_action: 'Describe what you were doing',
    });
  }
}

async function reportToSupport(details: SupportDetails): Promise<void> {
  await fetch('/api/support/tickets', {
    method: 'POST',
    body: JSON.stringify({
      subject: `API Error: ${details.error_code}`,
      description: `
Request ID: ${details.request_id}
Error Code: ${details.error_code}
Timestamp: ${details.timestamp}

What I was doing:
${details.user_action}
      `.trim(),
    }),
  });
}
```

### Health Check Endpoint

```typescript
// Check API health before making requests

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'down';
  services: {
    api: 'up' | 'down';
    database: 'up' | 'down';
    cache: 'up' | 'down';
  };
  version: string;
}

async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch('/api/health');

  if (!response.ok) {
    throw new Error('Health check failed');
  }

  return response.json();
}

// Usage before critical operations
async function createBookingWithHealthCheck(bookingData: BookingData) {
  const health = await checkHealth();

  if (health.status !== 'healthy') {
    throw new Error('API is not healthy. Please try again later.');
  }

  if (health.services.database === 'down') {
    throw new Error('Database is unavailable. Please try again later.');
  }

  return api.post('/api/bookings', bookingData);
}
```

---

## Summary

API error handling guidelines for the travel agency platform:

- **Error Format**: Consistent structure with code, message, details
- **Status Codes**: Proper HTTP codes for all scenarios
- **Error Codes**: Specific codes for each error type
- **Retry Logic**: Exponential backoff for retryable errors
- **Debugging**: Request IDs for support, debug mode
- **Best Practices**: Handle errors gracefully, log details, retry when appropriate

**Key Error Handling Principles:**
1. Always check response status before processing
2. Implement retry logic for 5xx and 429 errors
3. Display user-friendly messages for 4xx errors
4. Log all errors with request_id for debugging
5. Never expose sensitive data in error messages
6. Use health checks before critical operations

---

**Series Complete:** [API Documentation Master Index](./API_DOCUMENTATION_MASTER_INDEX.md)
