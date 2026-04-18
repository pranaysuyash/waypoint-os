# Hybrid Decision Engine - Operational Runbook

**Version**: 1.0
**Last Updated**: 2026-04-18

## Overview

This runbook covers operational procedures for the Hybrid Decision Engine in production.

## Architecture Recap

```
Request → Cache → Rules → LLM → Default
          ↓        ↓       ↓       ↓
         ₹0      ₹0      ₹0.10   ₹0
```

## Quick Reference

| Component | Health Check | Recovery Time |
|-----------|--------------|---------------|
| Cache | Disk check | N/A (always available) |
| Rules | Deterministic | N/A (always available) |
| LLM (Gemini) | Circuit breaker | 60s timeout |
| Default | Fallback | N/A (always available) |

## Health Check Endpoints

### GET /health

Returns overall system health.

**Response:**
```json
{
  "healthy": true,
  "status": "healthy",
  "timestamp": "2026-04-18T10:30:00Z",
  "components": {
    "cache": {"healthy": true},
    "rules": {"healthy": true},
    "llm": {
      "healthy": true,
      "available": true,
      "circuit_state": "closed",
      "failure_count": 0,
      "last_failure": null
    }
  },
  "metrics": {
    "total_decisions": 1000,
    "cache_hit_rate": 0.45,
    "rule_hit_rate": 0.35,
    "llm_call_rate": 0.20,
    "avg_latency_ms": 45.2,
    "error_rate": 0.01
  },
  "issues": []
}
```

**Status Values:**
- `healthy` - All systems normal
- `degraded` - Partial degradation (LLM circuit half-open, high latency)
- `unhealthy` - Critical issues (high error rate, LLM circuit open)

### GET /health/metrics

Returns detailed metrics in Prometheus format.

### GET /health/telemetry

Returns telemetry snapshot for the last 5 minutes.

## Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error rate | > 2% | > 5% | Check logs, investigate |
| P99 latency | > 1s | > 5s | Check LLM, cache |
| LLM circuit state | half_open | open | Monitor, reset if needed |
| Free decision rate | < 30% | < 20% | Add more rules |
| Cache hit rate | < 20% | < 10% | Check cache storage |

## Common Issues and Resolutions

### Issue: LLM Circuit Breaker Open

**Symptoms:**
- `llm.circuit_state = "open"`
- `llm_failure_count` increasing
- All decisions from cache/rules/default

**Diagnosis:**
```bash
# Check recent logs
tail -f logs/hybrid_engine.log | grep "LLM"

# Check health status
curl http://localhost:8000/health
```

**Resolution:**
1. Identify root cause (API key, rate limit, network)
2. Fix root cause
3. Wait for timeout (60s) or manually reset:
   ```python
   from src.decision.health import get_health_checker
   health = get_health_checker()
   health.reset_circuit_breaker()
   ```

### Issue: Low Cache Hit Rate

**Symptoms:**
- `cache_hit_rate < 20%`
- High LLM call rate
- Increased costs

**Diagnosis:**
```bash
# Check cache directory
ls -lh data/decision_cache/

# Check cache keys
python -c "
from src.decision.cache_storage import DecisionCacheStorage
storage = DecisionCacheStorage()
stats = storage.get_stats()
print(stats)
"
```

**Resolution:**
1. Verify cache directory is writable
2. Check cache key generation (no collisions)
3. Analyze decision patterns for common cases
4. Add rules for common patterns

### Issue: High Error Rate

**Symptoms:**
- `error_rate > 5%`
- Decision failures in logs

**Diagnosis:**
```bash
# Check error types
grep "ERROR" logs/hybrid_engine.log | sort | uniq -c

# Check specific error
grep "ERROR: cache_key" logs/hybrid_engine.log
```

**Resolution:**
1. Identify error pattern
2. Fix underlying issue or add better error handling
3. Consider rule addition to prevent LLM calls

### Issue: High Latency

**Symptoms:**
- `p99_latency_ms > 1000`
- Slow decision responses

**Diagnosis:**
```bash
# Check which component is slow
grep "latency" logs/hybrid_engine.log | tail -20

# Profile engine
python -m cProfile -o profile.stats src/decision/hybrid_engine.py
```

**Resolution:**
1. If LLM slow: Check network, consider faster model
2. If cache slow: Check disk I/O
3. If rules slow: Profile rule code

## Scheduled Procedures

### Daily (Automated)

- [ ] Health check runs every minute
- [ ] Metrics exported to monitoring
- [ ] Cache backup to object storage

### Weekly (Manual)

- [ ] Review metrics dashboard
- [ ] Check for new decision patterns
- [ ] Identify rule expansion opportunities
- [ ] Review cost vs free decision rate

### Monthly (Manual)

- [ ] Review and update rules
- [ ] Clean up old cache entries
- [ ] Update documentation
- [ ] Plan new rule development

## Performance Tuning

### Increasing Rule Hit Rate

1. **Analyze LLM calls:**
   ```python
   # Find decisions using LLM
   from src.decision.telemetry import get_telemetry
   telemetry = get_telemetry()
   snapshot = telemetry.get_snapshot()
   print(snapshot.decisions_by_source)  # Look at 'llm' count
   ```

2. **Identify patterns:**
   - Review LLM prompts
   - Look for repeated inputs
   - Check for deterministic outcomes

3. **Add rules:** See [How to Add a Decision Rule](../development/how_to_add_a_decision_rule.md)

4. **Validate:**
   ```bash
   python tools/validation/structured_validator.py
   ```

### Cache Optimization

1. **Tune cache size:**
   ```python
   # In cache_storage.py
   MAX_ENTRIES_PER_TYPE = 1000  # Increase if needed
   ```

2. **Adjust TTL:**
   ```python
   # In cache_schema.py
   DEFAULT_TTL_DAYS = 30  # Increase for longer cache
   ```

3. **Preload cache:**
   ```python
   # Load common decisions on startup
   from src.decision.hybrid_engine import HybridDecisionEngine
   engine = HybridDecisionEngine()
   # Common scenarios will be cached on first use
   ```

## Emergency Procedures

### All Decisions Failing

**Symptoms:**
- 100% error rate
- No decisions returning

**Immediate Actions:**
1. Check if service is running: `systemctl status hybrid-engine`
2. Check logs: `tail -100 logs/hybrid_engine.log`
3. Restart service: `systemctl restart hybrid-engine`
4. If restart fails, check dependencies

### LLM API Outage

**Symptoms:**
- LLM circuit breaker open
- Only cache/rules/default working

**Immediate Actions:**
1. Verify LLM API status (Gemini status page)
2. Check API key validity
3. Monitor circuit breaker - it will auto-recover
4. Consider adding emergency rules for common cases

### Cache Storage Full

**Symptoms:**
- Cache write errors
- Decreasing cache hit rate

**Immediate Actions:**
1. Check disk space: `df -h data/decision_cache/`
2. Clean up old entries: `rm data/decision_cache/*_old.json`
3. Increase cache size or disk space

## Monitoring Setup

### Prometheus Export

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'hybrid_decision_engine'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

Key panels:
- Total decisions (rate)
- Cache hit rate (gauge)
- Rule hit rate (gauge)
- LLM call rate (gauge)
- P99 latency (gauge)
- Error rate (gauge)
- Cost per decision (gauge)
- LLM circuit state (status)

### Alerts

```yaml
# alert_rules.yml
groups:
  - name: hybrid_engine
    rules:
      - alert: HighErrorRate
        expr: hybrid_decision_error_rate > 0.05
        for: 5m
        annotations:
          summary: "High error rate in hybrid engine"

      - alert: LowFreeDecisionRate
        expr: hybrid_decision_cache_hit_rate + hybrid_decision_rule_hit_rate < 0.3
        for: 15m
        annotations:
          summary: "Low free decision rate - consider adding rules"

      - alert: LLMCircuitOpen
        expr: hybrid_decision_llm_circuit_state == 1
        for: 1m
        annotations:
          summary: "LLM circuit breaker is open"
```

## Deployment Checklist

### Before Deploying

- [ ] All tests passing: `pytest tests/`
- [ ] Validation passing: `python tools/validation/structured_validator.py`
- [ ] Health check responding: `curl /health`
- [ ] Metrics exporting: `curl /health/metrics`
- [ ] Cache directory writable: `ls -ld data/decision_cache/`
- [ ] LLM API key configured (if using LLM)
- [ ] Monitoring configured

### After Deploying

- [ ] Verify health status: `curl /health`
- [ ] Check metrics are updating
- [ ] Monitor first 100 decisions
- [ ] Check for any errors in logs
- [ ] Verify cache is being populated

### Rollback Plan

If issues detected:
1. Revert to previous version
2. Clear cache if schema changed: `rm data/decision_cache/*.json`
3. Restart service
4. Verify health check passes

## Contact and Escalation

| Role | Contact | Responsibilities |
|------|---------|-----------------|
| On-Call | [Slack #on-call] | Immediate response |
| Engineering Lead | [email] | Escalation, architecture |
| Product Owner | [email] | Feature decisions, priorities |

## Additional Resources

- [Hybrid Decision Architecture](HYBRID_DECISION_ARCHITECTURE_2026-04-16.md)
- [Validation Report](validation/hybrid_engine_validation_report.md)
- [How to Add a Decision Rule](../development/how_to_add_a_decision_rule.md)
- [Tools Guide](../../tools/validation/README.md)

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-04-18 | 1.0 | Initial operational runbook |
