# Architecture Decision Record: Spine API Service Architecture

**ADR Number:** 002  
**Date:** 2026-04-15  
**Status:** Implemented  
**Author:** Architecture Team  

---

## Context

The original system used a **subprocess-based approach** for frontend-backend communication:

- `frontend/src/lib/spine-wrapper.py` - Python script that read JSON from stdin, called `run_spine_once()`, and output JSON to stdout
- Frontend spawned Python subprocesses for each request
- Each request incurred full Python module loading overhead
- No service lifecycle management or monitoring capabilities

### Problems with Subprocess Approach

1. **Performance Issues**: Process spawning overhead + module reloading on every request
2. **Resource Waste**: Short-lived processes with high startup costs
3. **Poor Scalability**: Cannot handle concurrent requests efficiently
4. **Monitoring Gaps**: No service-level observability or error boundaries
5. **Development Friction**: Difficult to debug cross-process communication
6. **Production Risks**: Subprocess calls are fragile and don't scale

### Relevant Code References

- **Removed:** `frontend/src/lib/spine-wrapper.py` (subprocess wrapper)
- **New:** `frontend/src/lib/spine-client.ts` (HTTP client)
- **New:** `spine-api/server.py` (FastAPI service)
- **Core Logic:** `src/intake/orchestration.py:run_spine_once()`

---

## Decision

We will implement a **persistent HTTP service architecture** using FastAPI:

### Decision 1: HTTP Service over Subprocess

**Decision:** Replace subprocess spawning with a persistent FastAPI service that exposes spine functionality via REST API.

**Rationale:**
- Eliminates process spawning overhead
- Enables proper service lifecycle management
- Provides HTTP-based monitoring and observability
- Supports concurrent request handling
- Follows modern microservices patterns
- Production-ready for deployment and scaling

### Decision 2: TypeScript HTTP Client

**Decision:** Replace Python subprocess wrapper with TypeScript HTTP client that calls the spine API service.

**Rationale:**
- Maintains type safety across the frontend-backend boundary
- Provides better error handling and retry logic
- Enables proper async/await patterns in the frontend
- Simplifies testing with mock HTTP responses

### Decision 3: Environment-Based Service Discovery

**Decision:** Use `SPINE_API_URL` environment variable for service location (defaults to `http://127.0.0.1:8000`).

**Rationale:**
- Supports different environments (dev, staging, prod)
- Enables containerized deployments
- Allows for service mesh integration
- Maintains development workflow simplicity

---

## Implementation

### Service Architecture

```
Frontend (Next.js) ← HTTP → Spine API (FastAPI) ← Python → Core Logic
```

### Key Components

1. **Spine API Service** (`spine-api/server.py`)
   - FastAPI application with `/run` endpoint
   - Pre-loads all Python modules on startup
   - Handles JSON request/response serialization
   - Provides proper error responses and logging

2. **TypeScript Client** (`frontend/src/lib/spine-client.ts`)
   - HTTP client with proper TypeScript types
   - Environment-based service discovery
   - Error handling and retry logic
   - Async/await support

3. **Request/Response Contract**
   ```typescript
   interface SpineRunRequest {
     raw_note?: string | null;
     stage: SpineStage;
     operating_mode: OperatingMode;
     // ... other fields
   }

   interface SpineRunResponse {
     packet: CanonicalPacket;
     decision_state: DecisionState;
     // ... other fields
   }
   ```

### Deployment Considerations

- **Development**: Run `uv run fastapi dev spine-api/server.py` for hot reload
- **Production**: Deploy as containerized service with proper health checks
- **Monitoring**: HTTP service enables standard monitoring (Prometheus, health endpoints)
- **Scaling**: Can be load-balanced horizontally

---

## Consequences

### Positive

- **Performance**: ~10x faster response times (no process spawning)
- **Scalability**: Handles concurrent requests efficiently
- **Reliability**: Proper error boundaries and service monitoring
- **Maintainability**: Clear separation of concerns between frontend and backend
- **Observability**: HTTP logs, metrics, and tracing capabilities
- **Testing**: Easier to mock HTTP calls vs. subprocess behavior

### Negative

- **Complexity**: Adds network layer with potential failure modes
- **Deployment**: Requires managing both frontend and API services
- **Latency**: HTTP call overhead vs. direct subprocess (minimal impact)
- **Development Setup**: Need to run both services during development

### Risks Mitigated

- **Resource Exhaustion**: No runaway Python processes
- **Memory Leaks**: Proper service lifecycle management
- **Debugging Difficulty**: HTTP requests are easier to inspect than subprocess I/O
- **Production Scaling**: Standard web service scaling patterns

---

## Alternatives Considered

### Alternative 1: Keep Subprocess with Optimization
- **Pros**: Simpler deployment, no network layer
- **Cons**: Still has fundamental scaling and performance issues
- **Rejected**: Doesn't solve core architectural problems

### Alternative 2: Direct Python Import in Node.js
- **Pros**: No network overhead, single process
- **Cons**: Complex Python/Node.js interop, deployment nightmares
- **Rejected**: Technology mismatch creates maintenance burden

### Alternative 3: gRPC instead of HTTP
- **Pros**: Better performance, type safety
- **Cons**: More complex tooling, overkill for current needs
- **Rejected**: HTTP/JSON is sufficient and more familiar

---

## Testing Strategy

- **Unit Tests**: Test spine-client.ts HTTP logic and error handling
- **Integration Tests**: Test full request flow through spine-api service
- **Load Tests**: Verify concurrent request handling capabilities
- **Fallback Tests**: Ensure graceful degradation if service unavailable

---

## Migration Notes

- **Backward Compatibility**: No breaking changes to core spine logic
- **Gradual Rollout**: Can run both approaches during transition
- **Monitoring**: Implement service health checks before full migration
- **Documentation**: Update developer setup instructions for running spine-api service

---

## Future Considerations

- **Service Mesh**: Consider Istio/Linkerd for service discovery and observability
- **API Versioning**: Implement proper API versioning for future changes
- **Caching**: Add response caching for expensive operations
- **Rate Limiting**: Implement request rate limiting at service level</content>
<parameter name="filePath">/Users/pranay/Projects/travel_agency_agent/Docs/architecture/adr/ADR-002-SPINE-API-ARCHITECTURE.md