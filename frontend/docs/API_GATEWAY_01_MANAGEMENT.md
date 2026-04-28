# API Gateway — Architecture & Management

> Research document for API gateway design, request routing, and lifecycle management.

---

## Key Questions

1. **Do we need a dedicated API gateway, or does Next.js API routing suffice?**
2. **How do we route requests between the frontend, spine API, and third-party services?**
3. **What cross-cutting concerns belong in the gateway (auth, logging, CORS, compression)?**
4. **How do we manage multiple backend services through a single entry point?**
5. **What's the deployment and scaling strategy for the gateway layer?**

---

## Research Areas

### Gateway Architecture Options

```typescript
type GatewayArchitecture =
  | 'nextjs_api_routes'      // Current approach — frontend proxies
  | 'dedicated_gateway'      // Kong, Ambassador, custom
  | 'service_mesh'           // Istio, Linkerd
  | 'cloud_managed';         // AWS API Gateway, Apigee

interface GatewayConfig {
  architecture: GatewayArchitecture;
  routes: GatewayRoute[];
  middleware: GatewayMiddleware[];
  errorHandling: ErrorHandlingConfig;
}

interface GatewayRoute {
  path: string;                  // Incoming path pattern
  method: string;
  target: BackendTarget;
  auth: AuthRequirement;
  rateLimit: RateLimitConfig;
  cache: CacheConfig;
  timeout: number;               // Ms
  retry: RetryConfig;
}

type BackendTarget =
  | { type: 'spine_api'; path: string }
  | { type: 'external'; baseUrl: string }
  | { type: 'internal_service'; serviceName: string }
  | { type: 'static'; content: string };
```

### Current State Assessment

The project currently uses Next.js API routes with a proxy-core module (`frontend/src/lib/proxy-core.ts`) and a route map (`frontend/src/lib/route-map.ts`). This works for a single backend but has limitations:

- No independent scaling of gateway vs. frontend
- All API traffic flows through Next.js server
- Limited observability into API call patterns
- Rate limiting is per-route, not global
- No circuit breaker for external service failures

### Cross-Cutting Concerns

```typescript
interface GatewayMiddleware {
  name: string;
  phase: 'pre_auth' | 'post_auth' | 'pre_proxy' | 'post_proxy';
  config: Record<string, unknown>;
}

// Middleware stack:
// 1. Request logging (method, path, IP, user-agent)
// 2. CORS handling
// 3. Rate limiting
// 4. Authentication (JWT validation)
// 5. Authorization (role/permission check)
// 6. Request transformation (header mapping)
// 7. Proxy to backend
// 8. Response transformation
// 9. Response caching
// 10. Response logging (status, duration, size)
```

### Service Registry

```typescript
interface ServiceRegistry {
  services: RegisteredService[];
  healthChecks: HealthCheckConfig[];
  discovery: 'static' | 'dynamic';
}

interface RegisteredService {
  serviceName: string;
  instances: ServiceInstance[];
  loadBalance: 'round_robin' | 'least_connections' | 'random';
  circuitBreaker: CircuitBreakerConfig;
}

interface ServiceInstance {
  url: string;
  healthy: boolean;
  lastHealthCheck: Date;
  metadata: Record<string, string>;
}

interface CircuitBreakerConfig {
  failureThreshold: number;       // Failures before opening
  resetTimeout: number;           // Ms before trying again
  halfOpenRequests: number;       // Test requests in half-open state
}
```

---

## Open Problems

1. **Gateway bottleneck** — All API traffic through a single gateway creates a single point of failure and potential bottleneck.

2. **WebSocket proxying** — Real-time features (conversation UX) need WebSocket support through the gateway, which not all gateways handle well.

3. **Backend for frontend (BFF) pattern** — The current Next.js API routes act as a BFF. Moving to a separate gateway may break this pattern or require restructuring.

4. **Cold start latency** — If the gateway is serverless (cloud-managed), cold starts add latency to the first request.

5. **Migration path** — Moving from Next.js proxy routes to a dedicated gateway requires careful migration without breaking existing clients.

---

## Next Steps

- [ ] Audit current API routing architecture and identify bottlenecks
- [ ] Evaluate API gateway solutions (Kong, AWS API Gateway, custom)
- [ ] Design migration path from Next.js proxy to gateway
- [ ] Study BFF pattern compatibility with dedicated gateway
- [ ] Benchmark current proxy latency vs. direct backend calls
