# AIML_04: AI Operations & Governance

> Model monitoring, cost optimization, safety rails, and governance for production AI/ML systems

---

## Document Overview

**Series:** AI/ML Patterns
**Document:** 4 of 4
**Focus:** AI Operations & Governance
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Model Monitoring](#model-monitoring)
4. [Cost Tracking & Optimization](#cost-tracking--optimization)
5. [Prompt Engineering & Versioning](#prompt-engineering--versioning)
6. [A/B Testing Framework](#ab-testing-framework)
7. [Safety & Content Moderation](#safety--content-moderation)
8. [Rate Limiting & Resource Management](#rate-limiting--resource-management)
9. [Compliance & Auditing](#compliance--auditing)
10. [Incident Response](#incident-response)
11. [API Specification](#api-specification)
12. [Testing Scenarios](#testing-scenarios)

---

## 1. Introduction

### What is AI Operations & Governance?

AI Operations (AIOps) and Governance ensure that AI/ML systems run reliably, efficiently, and safely in production. This includes:

- **Model Monitoring**: Detecting performance degradation and drift
- **Cost Management**: Tracking and optimizing AI API costs
- **Prompt Versioning**: Managing and versioning prompts
- **A/B Testing**: Validating prompt and model changes
- **Safety Rails**: Preventing harmful outputs
- **Rate Limiting**: Managing API quotas and costs
- **Compliance**: Meeting regulatory requirements
- **Incident Response**: Handling AI-related failures

### Why It Matters

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model Drift** | Degraded recommendations | Continuous monitoring |
| **Cost Overrun** | Unexpected bills | Budget alerts and optimization |
| **Prompt Issues** | Poor user experience | Versioning and A/B testing |
| **Safety Failures** | Harmful content | Content moderation |
| **Compliance Breach** | Legal penalties | Audit trails |

---

## 2. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AI Operations & Governance Layer                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Model       │  │ Cost        │  │ Prompt      │  │ Safety   │  │
│  │ Monitor     │  │ Tracker     │  │ Manager     │  │ Rails    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬─────┘  │
│         │                │                │               │         │
│  ┌──────▼────────────────▼────────────────▼───────────────▼─────┐  │
│  │                   Governance Engine                          │  │
│  └──────┬──────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │              Alerting & Notification System                  │  │
│  └──────┬──────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │              Analytics & Reporting Dashboard                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Monitoring** | Prometheus, Grafana, Custom metrics |
| **Logging** | ELK Stack, Cloud Logging |
| **Alerting** | PagerDuty, Slack, Email |
| **Cost Tracking** | Custom cost service, Cloud billing APIs |
| **Prompt Management** | Database with versioning |
| **A/B Testing** | Custom experiment framework |
| **Safety** | OpenAI Moderation API, Custom filters |

---

## 3. Model Monitoring

### Performance Metrics

```typescript
// monitoring/model-metrics.ts

export interface ModelPerformanceMetrics {
  // LLM metrics
  latency: {
    p50: number;
    p95: number;
    p99: number;
    avg: number;
  };
  throughput: number;  // requests per second
  errorRate: number;   // percentage

  // Quality metrics
  outputQuality: {
    avgRating: number;        // user feedback
    helpfulness: number;      // helpful vs not helpful
    regenerationRate: number; // how often users regenerate
  };

  // Cost metrics
  costPerRequest: number;
  costPerToken: number;
  totalCost: number;

  // Usage metrics
  tokensPerRequest: {
    input: number;
    output: number;
    total: number;
  };
}

/**
 * Model performance monitor
 */
export class ModelMonitor {
  private metricsStore: MetricsStore;
  private alertManager: AlertManager;

  /**
   * Record model inference metrics
   */
  async recordInference(metrics: {
    model: string;
    latency: number;
    inputTokens: number;
    outputTokens: number;
    success: boolean;
    userId?: string;
  }): Promise<void> {
    const timestamp = Date.now();

    // Record latency
    await this.metricsStore.record({
      metric: 'model_inference_latency',
      tags: {
        model: metrics.model,
        success: metrics.success.toString()
      },
      value: metrics.latency,
      timestamp
    });

    // Record token usage
    await this.metricsStore.record({
      metric: 'model_tokens_used',
      tags: {
        model: metrics.model,
        token_type: 'input'
      },
      value: metrics.inputTokens,
      timestamp
    });

    await this.metricsStore.record({
      metric: 'model_tokens_used',
      tags: {
        model: metrics.model,
        token_type: 'output'
      },
      value: metrics.outputTokens,
      timestamp
    });

    // Record success/failure
    await this.metricsStore.record({
      metric: 'model_inference_success',
      tags: { model: metrics.model },
      value: metrics.success ? 1 : 0,
      timestamp
    });

    // Check for anomalies
    await this.checkAnomalies(metrics.model);
  }

  /**
   * Check for performance anomalies
   */
  private async checkAnomalies(model: string): Promise<void> {
    // Get recent metrics
    const recent = await this.metricsStore.query({
      metric: 'model_inference_latency',
      tags: { model },
      timeRange: '5m'
    });

    if (recent.length < 10) return;

    // Calculate statistics
    const values = recent.map(r => r.value);
    const mean = this.mean(values);
    const stdDev = this.standardDeviation(values, mean);

    // Check if latest value is outlier (> 3 sigma)
    const latest = values[values.length - 1];
    const zScore = Math.abs((latest - mean) / stdDev);

    if (zScore > 3) {
      await this.alertManager.sendAlert({
        severity: 'warning',
        title: `Model latency anomaly detected for ${model}`,
        description: `Latest latency ${latest.toFixed(0)}ms is ${zScore.toFixed(1)}σ from mean`,
        metadata: { model, latest, mean, stdDev, zScore }
      });
    }

    // Check error rate
    const errors = await this.metricsStore.query({
      metric: 'model_inference_success',
      tags: { model },
      timeRange: '5m',
      aggregation: 'avg'
    });

    const errorRate = 1 - (errors[0]?.value || 1);

    if (errorRate > 0.05) {  // 5% error threshold
      await this.alertManager.sendAlert({
        severity: 'critical',
        title: `High error rate for ${model}`,
        description: `Error rate is ${(errorRate * 100).toFixed(1)}%`,
        metadata: { model, errorRate }
      });
    }
  }

  /**
   * Get model performance summary
   */
  async getPerformanceSummary(
    model: string,
    timeRange: string = '1h'
  ): Promise<ModelPerformanceMetrics> {
    // Get latency percentiles
    const latencyData = await this.metricsStore.query({
      metric: 'model_inference_latency',
      tags: { model },
      timeRange,
      aggregation: 'percentiles',
      percentiles: [50, 95, 99]
    });

    // Get token usage
    const inputTokens = await this.metricsStore.query({
      metric: 'model_tokens_used',
      tags: { model, token_type: 'input' },
      timeRange,
      aggregation: 'sum'
    });

    const outputTokens = await this.metricsStore.query({
      metric: 'model_tokens_used',
      tags: { model, token_type: 'output' },
      timeRange,
      aggregation: 'sum'
    });

    // Get error rate
    const successRate = await this.metricsStore.query({
      metric: 'model_inference_success',
      tags: { model },
      timeRange,
      aggregation: 'avg'
    });

    const requestCount = await this.metricsStore.query({
      metric: 'model_inference_latency',
      tags: { model },
      timeRange,
      aggregation: 'count'
    });

    return {
      latency: {
        p50: latencyData.find(d => d.percentile === 50)?.value || 0,
        p95: latencyData.find(d => d.percentile === 95)?.value || 0,
        p99: latencyData.find(d => d.percentile === 99)?.value || 0,
        avg: this.mean(latencyData.map(d => d.value))
      },
      throughput: requestCount[0]?.value / 3600 || 0,  // per second
      errorRate: 1 - (successRate[0]?.value || 1),
      outputQuality: await this.getOutputQualityMetrics(model, timeRange),
      costPerRequest: await this.calculateCostPerRequest(model, timeRange),
      costPerToken: await this.calculateCostPerToken(model),
      totalCost: await this.calculateTotalCost(model, timeRange),
      tokensPerRequest: {
        input: inputTokens[0]?.value / requestCount[0]?.value || 0,
        output: outputTokens[0]?.value / requestCount[0]?.value || 0,
        total: (inputTokens[0]?.value + outputTokens[0]?.value) / requestCount[0]?.value || 0
      }
    };
  }
}
```

### Drift Detection

```typescript
// monitoring/drift-detector.ts

export interface DriftDetectionResult {
  drifted: boolean;
  driftScore: number;  // 0-1, higher = more drift
  driftType: 'input' | 'output' | 'performance' | 'concept';
  details: DriftDetails;
  recommendation: string;
}

export interface DriftDetails {
  // Input drift
  inputDistributionChange?: number;
  featureDrift?: Map<string, number>;

  // Output drift
  outputDistributionChange?: number;
  predictionDrift?: Map<string, number>;

  // Performance drift
  performanceChange?: {
    accuracy: number;
    latency: number;
  };

  // Concept drift
  conceptDriftDetected?: boolean;
}

/**
 * Detect model drift
 */
export class DriftDetector {
  private baselineStore: BaselineStore;
  private metricsStore: MetricsStore;

  /**
   * Check for drift in model performance
   */
  async detectDrift(modelId: string): Promise<DriftDetectionResult> {
    // Get baseline metrics
    const baseline = await this.baselineStore.getBaseline(modelId);

    // Get current metrics
    const current = await this.getCurrentMetrics(modelId);

    const results: DriftDetectionResult = {
      drifted: false,
      driftScore: 0,
      driftType: 'performance',
      details: {},
      recommendation: ''
    };

    // Check input drift
    const inputDrift = await this.checkInputDrift(modelId, baseline, current);
    if (inputDrift.score > 0.3) {
      results.drifted = true;
      results.driftScore = Math.max(results.driftScore, inputDrift.score);
      results.details.inputDistributionChange = inputDrift.score;
      results.details.featureDrift = inputDrift.features;
    }

    // Check output drift
    const outputDrift = await this.checkOutputDrift(modelId, baseline, current);
    if (outputDrift.score > 0.3) {
      results.drifted = true;
      results.driftScore = Math.max(results.driftScore, outputDrift.score);
      results.details.outputDistributionChange = outputDrift.score;
      results.details.predictionDrift = outputDrift.predictions;
    }

    // Check performance drift
    const perfDrift = this.checkPerformanceDrift(baseline, current);
    if (perfDrift.significant) {
      results.drifted = true;
      results.driftScore = Math.max(results.driftScore, perfDrift.score);
      results.details.performanceChange = perfDrift;
    }

    // Check concept drift
    const conceptDrift = await this.checkConceptDrift(modelId, baseline, current);
    if (conceptDrift.detected) {
      results.drifted = true;
      results.driftScore = Math.max(results.driftScore, conceptDrift.score);
      results.details.conceptDriftDetected = true;
    }

    // Generate recommendation
    results.recommendation = this.generateRecommendation(results);

    return results;
  }

  /**
   * Check for input feature drift
   */
  private async checkInputDrift(
    modelId: string,
    baseline: BaselineMetrics,
    current: CurrentMetrics
  ): Promise<{ score: number; features: Map<string, number> }> {
    const featureDrift = new Map<string, number>();

    // Compare feature distributions
    for (const [feature, baselineDist] of baseline.inputFeatures) {
      const currentDist = current.inputFeatures.get(feature);

      if (!currentDist) {
        featureDrift.set(feature, 1);  // Complete drift - feature missing
        continue;
      }

      // Calculate Population Stability Index (PSI)
      const psi = this.calculatePSI(baselineDist, currentDist);
      featureDrift.set(feature, psi);
    }

    // Overall drift score
    const avgDrift = Array.from(featureDrift.values())
      .reduce((a, b) => a + b, 0) / featureDrift.size;

    return { score: avgDrift, features: featureDrift };
  }

  /**
   * Calculate Population Stability Index
   */
  private calculatePSI(
    baseline: Distribution,
    current: Distribution
  ): number {
    let psi = 0;

    const bins = this.mergeBins(baseline.bins, current.bins);

    for (const bin of bins) {
      const expected = baseline.bins.get(bin) || 0;
      const actual = current.bins.get(bin) || 0;

      if (expected === 0) continue;

      const expectedPct = expected / baseline.total;
      const actualPct = actual / current.total;

      if (actualPct === 0) {
        psi -= expectedPct;  // Handle zero bins
      } else {
        psi += (actualPct - expectedPct) * Math.log(actualPct / expectedPct);
      }
    }

    return psi;
  }

  /**
   * Check for concept drift (relationship between input and output changed)
   */
  private async checkConceptDrift(
    modelId: string,
    baseline: BaselineMetrics,
    current: CurrentMetrics
  ): Promise<{ detected: boolean; score: number }> {
    // Compare model accuracy on new data vs baseline
    const baselineAccuracy = baseline.performance.accuracy;
    const currentAccuracy = current.performance.accuracy;

    const accuracyDrop = baselineAccuracy - currentAccuracy;

    // Significant accuracy drop indicates concept drift
    if (accuracyDrop > 0.1) {  // 10% drop threshold
      return {
        detected: true,
        score: accuracyDrop
      };
    }

    return { detected: false, score: 0 };
  }

  private generateRecommendation(result: DriftDetectionResult): string {
    if (!result.drifted) {
      return 'No significant drift detected. Continue monitoring.';
    }

    if (result.details.performanceChange) {
      const perfChange = result.details.performanceChange;
      if (perfChange.accuracy < -0.1) {
        return 'Significant accuracy drop detected. Consider retraining model with recent data.';
      }
      if (perfChange.latency > 0.5) {
        return 'Latency increased significantly. Check infrastructure and model serving.';
      }
    }

    if (result.details.inputDistributionChange && result.details.inputDistributionChange > 0.5) {
      return 'Significant input drift detected. Review data pipeline and consider retraining.';
    }

    if (result.details.conceptDriftDetected) {
      return 'Concept drift detected. The relationship between inputs and outputs has changed. Retraining recommended.';
    }

    return 'Drift detected. Review model performance and consider retraining.';
  }
}
```

---

## 4. Cost Tracking & Optimization

### Cost Tracker

```typescript
// cost/tracker.ts

export interface CostReport {
  period: { start: Date; end: Date };
  totalCost: number;
  costByModel: Map<string, ModelCost>;
  costByEndpoint: Map<string, number>;
  costByUser: Map<string, number>;
  costTrend: CostTrend[];
  forecast: CostForecast;
  optimization: OptimizationOpportunity[];
}

export interface ModelCost {
  model: string;
  totalCost: number;
  requestCount: number;
  costPerRequest: number;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  costPer1kTokens: number;
}

/**
 * AI cost tracking and optimization
 */
export class CostTracker {
  private costStore: CostStore;
  private pricing: PricingTable;

  /**
   * Record API cost
   */
  async recordCost(cost: {
    model: string;
    endpoint: string;
    inputTokens: number;
    outputTokens: number;
    userId?: string;
    requestId: string;
  }): Promise<number> {
    const pricing = this.pricing.get(cost.model);
    const inputCost = (cost.inputTokens / 1000) * pricing.inputPrice;
    const outputCost = (cost.outputTokens / 1000) * pricing.outputPrice;
    const totalCost = inputCost + outputCost;

    await this.costStore.record({
      requestId: cost.requestId,
      model: cost.model,
      endpoint: cost.endpoint,
      userId: cost.userId,
      timestamp: new Date(),
      inputTokens: cost.inputTokens,
      outputTokens: cost.outputTokens,
      totalTokens: cost.inputTokens + cost.outputTokens,
      inputCost,
      outputCost,
      totalCost
    });

    return totalCost;
  }

  /**
   * Generate cost report
   */
  async generateReport(
    timeRange: { start: Date; end: Date }
  ): Promise<CostReport> {
    const costs = await this.costStore.query(timeRange);

    // Aggregate by model
    const costByModel = new Map<string, ModelCost>();
    for (const cost of costs) {
      const model = cost.model;
      const existing = costByModel.get(model);

      if (existing) {
        existing.totalCost += cost.totalCost;
        existing.requestCount++;
        existing.inputTokens += cost.inputTokens;
        existing.outputTokens += cost.outputTokens;
        existing.totalTokens += cost.totalTokens;
      } else {
        costByModel.set(model, {
          model,
          totalCost: cost.totalCost,
          requestCount: 1,
          costPerRequest: cost.totalCost,
          inputTokens: cost.inputTokens,
          outputTokens: cost.outputTokens,
          totalTokens: cost.totalTokens,
          costPer1kTokens: this.pricing.get(model).inputPrice
        });
      }
    }

    // Calculate cost per request for each model
    for (const modelCost of costByModel.values()) {
      modelCost.costPerRequest = modelCost.totalCost / modelCost.requestCount;
    }

    // Aggregate by endpoint
    const costByEndpoint = new Map<string, number>();
    for (const cost of costs) {
      const existing = costByEndpoint.get(cost.endpoint) || 0;
      costByEndpoint.set(cost.endpoint, existing + cost.totalCost);
    }

    // Aggregate by user
    const costByUser = new Map<string, number>();
    for (const cost of costs) {
      if (!cost.userId) continue;
      const existing = costByUser.get(cost.userId) || 0;
      costByUser.set(cost.userId, existing + cost.totalCost);
    }

    // Get cost trend
    const costTrend = await this.getCostTrend(timeRange);

    // Generate forecast
    const forecast = await this.forecastCost(timeRange);

    // Find optimization opportunities
    const optimization = await this.findOptimizations(costs);

    return {
      period: timeRange,
      totalCost: Array.from(costByModel.values()).reduce((s, c) => s + c.totalCost, 0),
      costByModel,
      costByEndpoint,
      costByUser,
      costTrend,
      forecast,
      optimization
    };
  }

  /**
   * Find cost optimization opportunities
   */
  private async findOptimizations(costs: CostRecord[]): Promise<OptimizationOpportunity[]> {
    const opportunities: OptimizationOpportunity[] = [];

    // Check for high-token usage endpoints
    const byEndpoint = new Map<string, { tokens: number; count: number }>();
    for (const cost of costs) {
      const existing = byEndpoint.get(cost.endpoint) || { tokens: 0, count: 0 };
      byEndpoint.set(cost.endpoint, {
        tokens: existing.tokens + cost.totalTokens,
        count: existing.count + 1
      });
    }

    for (const [endpoint, data] of byEndpoint) {
      const avgTokens = data.tokens / data.count;

      // High average tokens could indicate inefficiency
      if (avgTokens > 3000) {
        opportunities.push({
          type: 'high_token_usage',
          endpoint,
          impact: 'medium',
          description: `Average ${avgTokens.toFixed(0)} tokens per request`,
          suggestion: 'Consider prompt optimization or response summarization',
          potentialSavings: data.count * (avgTokens - 2000) * 0.00001  // Rough estimate
        });
      }
    }

    // Check for expensive model usage where cheaper could work
    const gpt4Usage = costs.filter(c => c.model.includes('gpt-4'));
    const gpt35Usage = costs.filter(c => c.model.includes('gpt-3.5'));

    if (gpt4Usage.length > gpt35Usage.length * 2) {
      opportunities.push({
        type: 'model_downgrade',
        endpoint: 'multiple',
        impact: 'high',
        description: 'High GPT-4 usage detected',
        suggestion: 'Consider using GPT-3.5 for simpler tasks',
        potentialSavings: (gpt4Usage.length * 0.05) - (gpt4Usage.length * 0.002)  // Price difference
      });
    }

    // Check for high error rates (wasted money)
    const errors = costs.filter(c => c.error);
    const errorRate = errors.length / costs.length;

    if (errorRate > 0.05) {
      opportunities.push({
        type: 'error_reduction',
        endpoint: 'multiple',
        impact: 'high',
        description: `${(errorRate * 100).toFixed(1)}% error rate detected`,
        suggestion: 'Fix error handling to reduce wasted API calls',
        potentialSavings: errors.reduce((s, e) => s + e.totalCost, 0)
      });
    }

    return opportunities.sort((a, b) => b.potentialSavings - a.potentialSavings);
  }

  /**
   * Forecast future costs
   */
  private async forecastCost(
    historicalPeriod: { start: Date; end: Date }
  ): Promise<CostForecast> {
    // Get historical data points
    const dailyCosts = await this.costStore.getDailyCosts(historicalPeriod);

    if (dailyCosts.length < 7) {
      return {
        next7Days: 0,
        next30Days: 0,
        confidence: 'low'
      };
    }

    // Simple linear regression for trend
    const n = dailyCosts.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = dailyCosts.reduce((s, d) => s + d.cost, 0);
    const sumXY = dailyCosts.reduce((s, d, i) => s + (i * d.cost), 0);
    const sumXX = (n * (n - 1) * (2 * n - 1)) / 6;

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Forecast next 7 and 30 days
    const avgDailyCost = dailyCosts.reduce((s, d) => s + d.cost, 0) / n;
    const trendFactor = slope > 0 ? 1 + (slope * 7) / avgDailyCost : 1;

    return {
      next7Days: avgDailyCost * 7 * trendFactor,
      next30Days: avgDailyCost * 30 * trendFactor,
      confidence: dailyCosts.length >= 30 ? 'high' : 'medium'
    };
  }
}
```

### Cost Optimization

```typescript
// cost/optimizer.ts

/**
 * Cost optimization strategies
 */
export class CostOptimizer {
  /**
   * Optimize prompt to reduce tokens
   */
  optimizePrompt(prompt: string): {
    optimized: string;
    originalTokens: number;
    optimizedTokens: number;
    savings: number;
  } {
    const originalTokens = this.estimateTokens(prompt);

    let optimized = prompt;

    // Remove redundant whitespace
    optimized = optimized.replace(/\s+/g, ' ');

    // Remove common filler phrases
    optimized = optimized.replace(/Please note that/gi, 'Note:');
    optimized = optimized.replace(/It is important to/gi, '');
    optimized = optimized.replace(/In order to/gi, 'To');

    // Shorten common phrases
    optimized = optimized.replace(/as soon as possible/gi, 'ASAP');
    optimized = optimized.replace(/for example/gi, 'e.g.');
    optimized = optimized.replace(/that is to say/gi, 'i.e.');

    // Remove repetitive instructions
    optimized = this.removeRepetitiveInstructions(optimized);

    const optimizedTokens = this.estimateTokens(optimized);
    const savings = originalTokens - optimizedTokens;

    return {
      optimized,
      originalTokens,
      optimizedTokens,
      savings
    };
  }

  /**
   * Suggest model selection based on task complexity
   */
  suggestModel(task: {
    type: string;
    inputTokens: number;
    requiredOutputTokens: number;
    complexity: 'simple' | 'medium' | 'complex';
  }): { model: string; reasoning: string; estimatedCost: number } {
    const { type, inputTokens, requiredOutputTokens, complexity } = task;

    // Simple tasks can use cheaper models
    if (complexity === 'simple' && inputTokens < 1000) {
      return {
        model: 'gpt-3.5-turbo',
        reasoning: 'Simple task with low token count - GPT-3.5 is sufficient',
        estimatedCost: ((inputTokens + requiredOutputTokens) / 1000) * 0.002
      };
    }

    // Medium complexity tasks
    if (complexity === 'medium' && inputTokens < 4000) {
      return {
        model: 'gpt-3.5-turbo',
        reasoning: 'Medium complexity task - try GPT-3.5 first, upgrade if needed',
        estimatedCost: ((inputTokens + requiredOutputTokens) / 1000) * 0.002
      };
    }

    // Complex tasks or high token count
    if (complexity === 'complex' || inputTokens >= 4000) {
      return {
        model: 'gpt-4-turbo',
        reasoning: 'Complex task or high token count - GPT-4 recommended for quality',
        estimatedCost: ((inputTokens + requiredOutputTokens) / 1000) * 0.01
      };
    }

    // Default to GPT-3.5
    return {
      model: 'gpt-3.5-turbo',
      reasoning: 'Default to cost-effective option',
      estimatedCost: ((inputTokens + requiredOutputTokens) / 1000) * 0.002
    };
  }

  /**
   * Implement caching for repeated requests
   */
  async getCachedOrGenerate(
    request: LLMRequest,
    cache: CacheStore,
    generateFn: () => Promise<LLMResponse>
  ): Promise<LLMResponse> {
    const cacheKey = this.generateCacheKey(request);

    // Check cache
    const cached = await cache.get(cacheKey);
    if (cached) {
      return {
        ...cached,
        fromCache: true
      };
    }

    // Generate response
    const response = await generateFn();

    // Cache response (if successful)
    if (!response.error) {
      await cache.set(cacheKey, response, {
        ttl: 3600  // 1 hour
      });
    }

    return response;
  }

  /**
   * Implement semantic caching
   */
  async getSemanticCachedOrGenerate(
    request: LLMRequest,
    cache: SemanticCacheStore,
    generateFn: () => Promise<LLMResponse>,
    similarityThreshold: number = 0.95
  ): Promise<LLMResponse> {
    // Generate embedding for request
    const embedding = await this.generateEmbedding(request.prompt);

    // Find similar cached requests
    const similar = await cache.findSimilar(embedding, {
      threshold: similarityThreshold,
      limit: 1
    });

    if (similar.length > 0) {
      const cached = similar[0];
      return {
        ...cached.response,
        fromCache: true,
        similarity: cached.similarity
      };
    }

    // Generate response
    const response = await generateFn();

    // Cache with embedding
    if (!response.error) {
      await cache.set(embedding, {
        request,
        response,
        timestamp: new Date()
      });
    }

    return response;
  }

  private generateCacheKey(request: LLMRequest): string {
    return crypto
      .createHash('sha256')
      .update(JSON.stringify({
        model: request.model,
        prompt: request.prompt,
        temperature: request.temperature,
        maxTokens: request.maxTokens
      }))
      .digest('hex');
  }
}
```

---

## 5. Prompt Engineering & Versioning

### Prompt Management

```typescript
// prompt/manager.ts

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  version: number;
  status: 'draft' | 'active' | 'archived';
  template: string;
  variables: string[];
  metadata: {
    author: string;
    createdAt: Date;
    updatedAt: Date;
    usageCount: number;
    avgRating?: number;
  };
  config: {
    model: string;
    temperature?: number;
    maxTokens?: number;
    stopSequences?: string[];
  };
}

/**
 * Prompt template manager with versioning
 */
export class PromptManager {
  private store: PromptStore;
  private versionControl: VersionControl;

  /**
   * Create new prompt template
   */
  async create(template: Omit<PromptTemplate, 'id' | 'version' | 'metadata'>): Promise<PromptTemplate> {
    const newTemplate: PromptTemplate = {
      ...template,
      id: this.generateId(),
      version: 1,
      metadata: {
        author: template.metadata.author,
        createdAt: new Date(),
        updatedAt: new Date(),
        usageCount: 0
      }
    };

    await this.store.save(newTemplate);
    return newTemplate;
  }

  /**
   * Update prompt template (creates new version)
   */
  async update(
    id: string,
    updates: Partial<PromptTemplate>,
    author: string
  ): Promise<PromptTemplate> {
    const current = await this.store.get(id);
    if (!current) {
      throw new Error(`Prompt template ${id} not found`);
    }

    // Archive current version
    await this.versionControl.archive(id, current);

    // Create new version
    const newVersion: PromptTemplate = {
      ...current,
      ...updates,
      id,  // Keep same ID
      version: current.version + 1,
      metadata: {
        ...current.metadata,
        updatedAt: new Date()
      }
    };

    await this.store.save(newVersion);
    return newVersion;
  }

  /**
   * Render prompt template with variables
   */
  async render(
    id: string,
    variables: Record<string, any>
  ): Promise<string> {
    const template = await this.getActiveVersion(id);

    let rendered = template.template;

    // Replace variables
    for (const [key, value] of Object.entries(variables)) {
      const placeholder = `{{${key}}}`;
      rendered = rendered.replace(new RegExp(placeholder, 'g'), String(value));
    }

    // Check for missing variables
    const missing = template.variables.filter(
      v => !Object.prototype.hasOwnProperty.call(variables, v)
    );

    if (missing.length > 0) {
      throw new Error(`Missing required variables: ${missing.join(', ')}`);
    }

    // Track usage
    await this.trackUsage(id);

    return rendered;
  }

  /**
   * Get active version of template
   */
  async getActiveVersion(id: string): Promise<PromptTemplate> {
    const template = await this.store.get(id);
    if (!template) {
      throw new Error(`Prompt template ${id} not found`);
    }

    // If not active, get from version control
    if (template.status !== 'active') {
      const active = await this.versionControl.getActive(id);
      if (active) {
        return active;
      }
    }

    return template;
  }

  /**
   * Rollback to previous version
   */
  async rollback(id: string, toVersion?: number): Promise<PromptTemplate> {
    const current = await this.store.get(id);
    if (!current) {
      throw new Error(`Prompt template ${id} not found`);
    }

    const targetVersion = toVersion || current.version - 1;

    // Get archived version
    const archived = await this.versionControl.getArchived(id, targetVersion);
    if (!archived) {
      throw new Error(`Version ${targetVersion} not found for ${id}`);
    }

    // Archive current
    await this.versionControl.archive(id, current);

    // Restore archived as active
    const restored: PromptTemplate = {
      ...archived,
      status: 'active',
      metadata: {
        ...archived.metadata,
        updatedAt: new Date()
      }
    };

    await this.store.save(restored);
    return restored;
  }

  /**
   * Compare two versions
   */
  async diff(
    id: string,
    version1: number,
    version2: number
  ): Promise<PromptDiff> {
    const v1 = await this.versionControl.getArchived(id, version1);
    const v2 = await this.versionControl.getArchived(id, version2);

    if (!v1 || !v2) {
      throw new Error('One or both versions not found');
    }

    // Compute diff
    const templateDiff = this.computeTextDiff(v1.template, v2.template);
    const configDiff = this.computeConfigDiff(v1.config, v2.config);

    return {
      template: templateDiff,
      config: configDiff,
      variables: {
        added: v2.variables.filter(v => !v1.variables.includes(v)),
        removed: v1.variables.filter(v => !v2.variables.includes(v))
      }
    };
  }
}
```

### Prompt Testing

```typescript
// prompt/testing.ts

/**
 * Prompt testing and evaluation
 */
export class PromptTester {
  /**
   * Test prompt against test cases
   */
  async test(
    templateId: string,
    testCases: PromptTestCase[]
  ): Promise<PromptTestResult> {
    const template = await this.promptManager.getActiveVersion(templateId);
    const results: TestCaseResult[] = [];

    for (const testCase of testCases) {
      // Render prompt
      const prompt = await this.promptManager.render(templateId, testCase.variables);

      // Execute
      const start = Date.now();
      const response = await this.llmClient.complete({
        ...template.config,
        prompt
      });
      const latency = Date.now() - start;

      // Evaluate
      const evaluation = await this.evaluate(response.text, testCase.expected);

      results.push({
        testCaseId: testCase.id,
        passed: evaluation.passed,
        response: response.text,
        expected: testCase.expected,
        evaluation,
        latency,
        tokens: response.usage?.total_tokens || 0
      });
    }

    // Aggregate results
    const passed = results.filter(r => r.passed).length;
    const avgLatency = results.reduce((s, r) => s + r.latency, 0) / results.length;
    const avgTokens = results.reduce((s, r) => s + r.tokens, 0) / results.length;

    return {
      templateId,
      templateVersion: template.version,
      totalCases: testCases.length,
      passed,
      failed: testCases.length - passed,
      passRate: passed / testCases.length,
      avgLatency,
      avgTokens,
      results
    };
  }

  /**
   * Evaluate response against expected output
   */
  private async evaluate(
    response: string,
    expected: PromptTestCase['expected']
  ): Promise<EvaluationResult> {
    const evaluation: EvaluationResult = {
      passed: true,
      scores: {},
      details: []
    };

    // Check required content
    if (expected.includes) {
      for (const item of expected.includes) {
        const included = response.toLowerCase().includes(item.toLowerCase());
        evaluation.scores[item] = included ? 1 : 0;

        if (!included) {
          evaluation.passed = false;
          evaluation.details.push(`Missing required content: ${item}`);
        }
      }
    }

    // Check excluded content
    if (expected.excludes) {
      for (const item of expected.excludes) {
        const excluded = !response.toLowerCase().includes(item.toLowerCase());
        evaluation.scores[`exclude_${item}`] = excluded ? 1 : 0;

        if (!excluded) {
          evaluation.passed = false;
          evaluation.details.push(`Should not contain: ${item}`);
        }
      }
    }

    // Check format
    if (expected.format) {
      const formatValid = this.checkFormat(response, expected.format);
      evaluation.scores.format = formatValid ? 1 : 0;

      if (!formatValid) {
        evaluation.passed = false;
        evaluation.details.push(`Format does not match: ${expected.format}`);
      }
    }

    // Semantic similarity (if expected output provided)
    if (expected.output) {
      const similarity = await this.computeSimilarity(response, expected.output);
      evaluation.scores.similarity = similarity;

      if (similarity < 0.7) {
        evaluation.passed = false;
        evaluation.details.push(`Low semantic similarity: ${similarity.toFixed(2)}`);
      }
    }

    return evaluation;
  }

  /**
   * Run A/B test between two prompt versions
   */
  async abTest(
    templateId: string,
    versionA: number,
    versionB: number,
    trafficSplit: number = 0.5,  // 50% to each version
    duration: number = 7 * 24 * 60 * 60 * 1000  // 7 days
  ): Promise<ABTestResult> {
    const experimentId = this.generateExperimentId();

    // Set up experiment
    await this.experimentStore.create({
      experimentId,
      templateId,
      variants: [
        { version: versionA, traffic: trafficSplit },
        { version: versionB, traffic: 1 - trafficSplit }
      ],
      startTime: new Date(),
      endTime: new Date(Date.now() + duration)
    });

    // Return experiment info
    return {
      experimentId,
      templateId,
      variants: [
        { version: versionA, name: 'Version A' },
        { version: versionB, name: 'Version B' }
      ],
      trafficSplit,
      duration,
      status: 'running'
    };
  }

  /**
   * Get A/B test results
   */
  async getABTestResults(experimentId: string): Promise<ABTestResults> {
    const experiment = await this.experimentStore.get(experimentId);

    const results: Map<number, VariantResult> = new Map();

    for (const variant of experiment.variants) {
      const metrics = await this.metricsStore.query({
        experimentId,
        variant: variant.version
      });

      const totalRequests = metrics.length;
      const avgLatency = metrics.reduce((s, m) => s + m.latency, 0) / totalRequests;
      const avgTokens = metrics.reduce((s, m) => s + m.tokens, 0) / totalRequests;
      const avgRating = metrics.reduce((s, m) => s + (m.rating || 0), 0) /
        metrics.filter(m => m.rating).length;

      results.set(variant.version, {
        version: variant.version,
        totalRequests,
        avgLatency,
        avgTokens,
        avgRating,
        satisfaction: metrics.filter(m => (m.rating || 0) >= 4).length / totalRequests
      });
    }

    // Determine winner
    const variantResults = Array.from(results.values());
    const winner = variantResults.sort((a, b) => b.avgRating - a.avgRating)[0];

    return {
      experimentId,
      variants: variantResults,
      winner: winner.version,
      confidence: this.calculateStatisticalConfidence(variantResults)
    };
  }
}
```

---

## 6. A/B Testing Framework

### Experiment Management

```typescript
// experimentation/experiment.ts

export interface PromptExperiment {
  experimentId: string;
  name: string;
  description: string;
  templateId: string;
  variants: ExperimentVariant[];
  status: 'draft' | 'running' | 'paused' | 'completed';
  config: {
    trafficSplit: number[];
    successMetric: 'rating' | 'satisfaction' | 'conversion';
    minSampleSize: number;
    confidenceLevel: number;
  };
  startTime?: Date;
  endTime?: Date;
  results?: ExperimentResults;
}

export interface ExperimentVariant {
  version: number;
  name: string;
  traffic: number;  // 0-1
  metrics: VariantMetrics;
}

/**
 * A/B testing for prompts and models
 */
export class ExperimentManager {
  private store: ExperimentStore;
  private assignmentService: AssignmentService;
  private stats: StatisticalCalculator;

  /**
   * Create new experiment
   */
  async create(config: Omit<PromptExperiment, 'experimentId' | 'status' | 'metrics'>): Promise<PromptExperiment> {
    // Validate traffic split sums to 1
    const totalTraffic = config.config.trafficSplit.reduce((a, b) => a + b, 0);
    if (Math.abs(totalTraffic - 1) > 0.01) {
      throw new Error('Traffic split must sum to 1');
    }

    const experiment: PromptExperiment = {
      ...config,
      experimentId: this.generateId(),
      status: 'draft',
      variants: config.variants.map((v, i) => ({
        ...v,
        traffic: config.config.trafficSplit[i],
        metrics: {
          exposures: 0,
          successes: 0,
          avgRating: 0,
          avgLatency: 0
        }
      }))
    };

    await this.store.save(experiment);
    return experiment;
  }

  /**
   * Assign user to variant
   */
  async assignVariant(
    experimentId: string,
    userId: string
  ): Promise<ExperimentVariant | null> {
    const experiment = await this.store.get(experimentId);

    if (experiment.status !== 'running') {
      return null;
    }

    // Check if already assigned
    const existing = await this.assignmentService.getAssignment(experimentId, userId);
    if (existing) {
      return experiment.variants.find(v => v.version === existing.variant);
    }

    // Assign using consistent hashing
    const hash = this.consistentHash(userId, experimentId);
    const variantIndex = this.selectVariant(hash, experiment.config.trafficSplit);
    const variant = experiment.variants[variantIndex];

    // Record assignment
    await this.assignmentService.record({
      experimentId,
      userId,
      variant: variant.version,
      timestamp: new Date()
    });

    // Update exposure count
    variant.metrics.exposures++;

    await this.store.save(experiment);

    return variant;
  }

  /**
   * Record outcome
   */
  async recordOutcome(event: {
    experimentId: string;
    userId: string;
    metric: 'rating' | 'satisfaction' | 'conversion';
    value: number;
  }): Promise<void> {
    const assignment = await this.assignmentService.getAssignment(
      event.experimentId,
      event.userId
    );

    if (!assignment) return;

    const experiment = await this.store.get(event.experimentId);
    const variant = experiment.variants.find(
      v => v.version === assignment.variant
    );

    if (!variant) return;

    // Update metrics
    if (event.metric === experiment.config.successMetric) {
      variant.metrics.successes++;
    }

    // Update running average for rating
    if (event.metric === 'rating') {
      const currentTotal = variant.metrics.avgRating * (variant.metrics.exposures - 1);
      variant.metrics.avgRating = (currentTotal + event.value) / variant.metrics.exposures;
    }

    // Check if experiment can be stopped
    await this.checkStoppingRules(experiment);

    await this.store.save(experiment);
  }

  /**
   * Check stopping rules for experiment
   */
  private async checkStoppingRules(experiment: PromptExperiment): Promise<void> {
    const totalExposures = experiment.variants.reduce(
      (s, v) => s + v.metrics.exposures,
      0
    );

    // Check minimum sample size
    if (totalExposures < experiment.config.minSampleSize) {
      return;
    }

    // Perform statistical test
    const results = await this.calculateResults(experiment);

    // Check for significant winner
    if (results.winner && results.confidence > 0.95) {
      // Could auto-stop, but let's just flag it
      experiment.results = results;
      return;
    }

    // Check for futility (no chance of reaching significance)
    if (results.futility) {
      experiment.results = results;
    }
  }

  /**
   * Calculate experiment results with statistical analysis
   */
  private async calculateResults(
    experiment: PromptExperiment
  ): Promise<ExperimentResults> {
    const control = experiment.variants[0];
    const treatment = experiment.variants[1];

    // Perform t-test or z-test depending on metric
    const pValue = this.stats.twoSampleZTest(
      control.metrics.successes,
      control.metrics.exposures,
      treatment.metrics.successes,
      treatment.metrics.exposures
    );

    const winner = pValue < experiment.config.confidenceLevel
      ? (treatment.metrics.avgRating > control.metrics.avgRating
          ? treatment.version
          : control.version)
      : null;

    return {
      variants: experiment.variants.map(v => ({
        version: v.version,
        metrics: v.metrics
      })),
      winner,
      confidence: winner ? 1 - pValue : 0,
      pValue,
      significance: this.interpretPValue(pValue)
    };
  }
}
```

---

## 7. Safety & Content Moderation

### Content Moderation

```typescript
// safety/moderation.ts

export interface ModerationResult {
  flagged: boolean;
  categories: {
    hate: boolean;
    harassment: boolean;
    selfHarm: boolean;
    sexual: boolean;
    violence: boolean;
  };
  scores: Record<string, number>;
  filteredText?: string;
}

/**
 * Content moderation service
 */
export class ContentModeration {
  private openaiModeration: OpenAIModerationClient;
  private customFilters: CustomFilterEngine;

  /**
   * Moderate content
   */
  async moderate(text: string): Promise<ModerationResult> {
    // Check with OpenAI moderation API
    const openaiResult = await this.openaiModeration.check(text);

    // Run custom filters
    const customResult = await this.customFilters.check(text);

    // Combine results
    const flagged = openaiResult.flagged || customResult.flagged;

    const categories = {
      hate: openaiResult.categories.hate || customResult.categories.hate,
      harassment: openaiResult.categories.harassment || customResult.categories.harassment,
      selfHarm: openaiResult.categories.selfHarm || customResult.categories.selfHarm,
      sexual: openaiResult.categories.sexual || customResult.categories.sexual,
      violence: openaiResult.categories.violence || customResult.categories.violence
    };

    const scores = {
      ...openaiResult.scores,
      ...customResult.scores
    };

    // Filter text if needed
    const filteredText = flagged
      ? this.filterText(text, categories)
      : undefined;

    return {
      flagged,
      categories,
      scores,
      filteredText
    };
  }

  /**
   * Filter inappropriate content from text
   */
  private filterText(text: string, categories: ModerationResult['categories']): string {
    let filtered = text;

    // Apply profanity filter
    filtered = this.profanityFilter.filter(filtered);

    // Apply PII redaction
    filtered = this.piiRedactor.redact(filtered);

    return filtered;
  }

  /**
   * Check if response is safe to send to user
   */
  async isSafeToSend(text: string, context: {
    userId?: string;
    userAge?: number;
  }): Promise<{ safe: boolean; reason?: string }> {
    // Moderate content
    const moderation = await this.moderate(text);

    if (moderation.flagged) {
      const flaggedCategories = Object.entries(moderation.categories)
        .filter(([_, flagged]) => flagged)
        .map(([category]) => category);

      return {
        safe: false,
        reason: `Content flagged for: ${flaggedCategories.join(', ')}`
      };
    }

    // Check for PII
    const hasPII = await this.piiRedactor.detect(text);
    if (hasPII && context.userAge && context.userAge < 18) {
      return {
        safe: false,
        reason: 'May contain PII - not safe for minor users'
      };
    }

    return { safe: true };
  }
}
```

### Output Validation

```typescript
// safety/validation.ts

/**
 * Validate AI outputs before sending to users
 */
export class OutputValidator {
  /**
   * Validate response
   */
  async validate(
    response: string,
    context: ValidationContext
  ): Promise<ValidationResult> {
    const issues: ValidationIssue[] = [];

    // Check for refusal messages
    if (this.isRefusal(response)) {
      issues.push({
        type: 'refusal',
        severity: 'info',
        message: 'Model refused to respond'
      });
    }

    // Check for incomplete response
    if (this.isIncomplete(response)) {
      issues.push({
        type: 'incomplete',
        severity: 'warning',
        message: 'Response appears incomplete'
      });
    }

    // Check for hallucinations (if ground truth available)
    if (context.groundTruth) {
      const hallucination = await this.checkHallucination(response, context.groundTruth);
      if (hallucination.detected) {
        issues.push({
          type: 'hallucination',
          severity: 'error',
          message: hallucination.details
        });
      }
    }

    // Check for format compliance
    if (context.expectedFormat) {
      const formatValid = this.checkFormat(response, context.expectedFormat);
      if (!formatValid) {
        issues.push({
          type: 'format',
          severity: 'warning',
          message: `Response does not match expected format: ${context.expectedFormat}`
        });
      }
    }

    // Check length
    if (context.maxLength && response.length > context.maxLength) {
      issues.push({
        type: 'length',
        severity: 'warning',
        message: `Response exceeds max length: ${response.length} > ${context.maxLength}`
      });
    }

    return {
      valid: issues.filter(i => i.severity === 'error').length === 0,
      issues
    };
  }

  /**
   * Check for common refusal patterns
   */
  private isRefusal(response: string): boolean {
    const refusalPatterns = [
      /I (?:can't|cannot|am not able to)/i,
      /I'?m (?:not|unable to) (?:provide|give)/i,
      /I don't have (?:information|access)/i,
      /I'?m (?:sorry|afraid) (?:I )?(?:can't|cannot)/i,
      /As an AI/i
    ];

    return refusalPatterns.some(pattern => pattern.test(response));
  }

  /**
   * Check for incomplete response
   */
  private isIncomplete(response: string): boolean {
    // Ends with ellipsis
    if (/\.{3,6}$/.test(response.trim())) {
      return true;
    }

    // Ends mid-sentence
    if (!/[.!?]\s*$/.test(response.trim())) {
      return true;
    }

    // Has hanging brackets
    const openBrackets = (response.match(/\{/g) || []).length;
    const closeBrackets = (response.match(/\}/g) || []).length;
    if (openBrackets !== closeBrackets) {
      return true;
    }

    return false;
  }

  /**
   * Check for hallucinations
   */
  private async checkHallucination(
    response: string,
    groundTruth: any
  ): Promise<{ detected: boolean; details?: string }> {
    // Extract factual claims from response
    const claims = await this.extractClaims(response);

    // Verify each claim against ground truth
    const incorrect = claims.filter(claim => !this.verifyClaim(claim, groundTruth));

    if (incorrect.length > 0) {
      return {
        detected: true,
        details: `Unverified claims: ${incorrect.map(c => c.text).join(', ')}`
      };
    }

    return { detected: false };
  }

  /**
   * Sanitize output for user display
   */
  sanitize(response: string): string {
    let sanitized = response;

    // Remove any remaining thinking tags
    sanitized = sanitized.replace(/<thinking>.*?<\/thinking>/gs, '');

    // Remove any system prompts that leaked
    sanitized = sanitized.replace(/You are (?:a|an) AI.*?\./gi, '');

    // Remove repetitive text
    sanitized = this.removeRepetitiveText(sanitized);

    // Clean up whitespace
    sanitized = sanitized.replace(/\n{3,}/g, '\n\n');

    return sanitized.trim();
  }
}
```

---

## 8. Rate Limiting & Resource Management

### Rate Limiter

```typescript
// rate-limit/limiter.ts

export interface RateLimitConfig {
  // Per-user limits
  userRequestsPerMinute: number;
  userTokensPerMinute: number;

  // Global limits
  globalRequestsPerSecond: number;
  globalTokensPerSecond: number;

  // Model-specific limits
  modelLimits: Map<string, {
    requestsPerMinute: number;
    tokensPerMinute: number;
  }>;
}

/**
 * AI API rate limiting
 */
export class RateLimiter {
  private config: RateLimitConfig;
  private userLimits: Map<string, UserLimitState>;
  private globalLimits: GlobalLimitState;

  /**
   * Check if request is allowed
   */
  async checkLimit(request: RateLimitRequest): Promise<{
    allowed: boolean;
    retryAfter?: number;
    reason?: string;
  }> {
    const now = Date.now();

    // Check user limits
    const userLimit = this.userLimits.get(request.userId) || this.createEmptyUserLimit();
    const userReset = this.getNextReset(now, 60);  // 1 minute window

    // Update user state
    this.cleanupExpiredUserLimits(now);

    // Check user request rate
    if (userLimit.requests >= this.config.userRequestsPerMinute) {
      return {
        allowed: false,
        retryAfter: userReset - now,
        reason: 'User request rate limit exceeded'
      };
    }

    // Check user token rate
    if (request.estimatedTokens &&
        userLimit.tokens + request.estimatedTokens > this.config.userTokensPerMinute) {
      return {
        allowed: false,
        retryAfter: userReset - now,
        reason: 'User token limit exceeded'
      };
    }

    // Check global limits
    if (this.globalLimits.requests >= this.config.globalRequestsPerSecond) {
      return {
        allowed: false,
        retryAfter: 1000,  // 1 second
        reason: 'Global request rate limit exceeded'
      };
    }

    // Check model-specific limits
    const modelLimit = this.config.modelLimits.get(request.model);
    if (modelLimit) {
      const modelState = this.globalLimits.models.get(request.model) ||
        { requests: 0, tokens: 0 };

      if (modelState.requests >= modelLimit.requestsPerMinute) {
        return {
          allowed: false,
          retryAfter: userReset - now,
          reason: `Model ${request.model} rate limit exceeded`
        };
      }
    }

    // Update limits (request is allowed)
    userLimit.requests++;
    userLimit.tokens += request.estimatedTokens || 0;
    this.userLimits.set(request.userId, userLimit);

    this.globalLimits.requests++;

    return { allowed: true };
  }

  /**
   * Record actual usage after request completes
   */
  async recordUsage(request: RateLimitRequest, actualTokens: number): Promise<void> {
    // Update with actual token count
    const userLimit = this.userLimits.get(request.userId);
    if (userLimit) {
      // Adjust if estimate was off
      const adjustment = actualTokens - (request.estimatedTokens || 0);
      userLimit.tokens += adjustment;
    }
  }

  private getNextReset(now: number, windowSeconds: number): number {
    return Math.ceil(now / (windowSeconds * 1000)) * (windowSeconds * 1000);
  }

  private cleanupExpiredUserLimits(now: number): void {
    const windowStart = now - 60000;  // 1 minute ago

    for (const [userId, limit] of this.userLimits) {
      if (limit.lastUpdate < windowStart) {
        this.userLimits.delete(userId);
      }
    }
  }
}
```

### Budget Management

```typescript
// cost/budget.ts

/**
 * Budget management for AI costs
 */
export class BudgetManager {
  private budgets: Map<string, Budget>;

  /**
   * Set budget limit
   */
  async setBudget(budget: {
    scope: 'global' | 'user' | 'team';
    scopeId?: string;
    period: 'daily' | 'weekly' | 'monthly';
    limit: number;
    alertThreshold: number;  // percentage
  }): Promise<void> {
    const budgetId = this.getBudgetId(budget.scope, budget.scopeId, budget.period);

    this.budgets.set(budgetId, {
      id: budgetId,
      scope: budget.scope,
      scopeId: budget.scopeId,
      period: budget.period,
      limit: budget.limit,
      spent: 0,
      alertThreshold: budget.alertThreshold,
      periodStart: this.getPeriodStart(budget.period),
      alertsSent: []
    });
  }

  /**
   * Check and record cost against budget
   */
  async checkAndRecord(cost: {
    scope: 'user' | 'team';
    scopeId: string;
    amount: number;
  }): Promise<{ allowed: boolean; reason?: string }> {
    const dailyBudget = this.budgets.get(this.getBudgetId('user', cost.scopeId, 'daily'));
    const monthlyBudget = this.budgets.get(this.getBudgetId('user', cost.scopeId, 'monthly'));

    // Check daily budget
    if (dailyBudget) {
      await this.resetBudgetIfNeeded(dailyBudget);

      if (dailyBudget.spent + cost.amount > dailyBudget.limit) {
        return {
          allowed: false,
          reason: 'Daily budget exceeded'
        };
      }

      // Check alert threshold
      const newSpent = dailyBudget.spent + cost.amount;
      const percentage = (newSpent / dailyBudget.limit) * 100;

      if (percentage >= dailyBudget.alertThreshold &&
          !dailyBudget.alertsSent.includes('threshold')) {
        await this.sendAlert({
          type: 'budget_threshold',
          budget: dailyBudget.id,
          percentage: percentage.toFixed(1)
        });
        dailyBudget.alertsSent.push('threshold');
      }

      dailyBudget.spent = newSpent;
    }

    // Check monthly budget
    if (monthlyBudget) {
      await this.resetBudgetIfNeeded(monthlyBudget);

      if (monthlyBudget.spent + cost.amount > monthlyBudget.limit) {
        return {
          allowed: false,
          reason: 'Monthly budget exceeded'
        };
      }

      monthlyBudget.spent += cost.amount;
    }

    return { allowed: true };
  }

  /**
   * Get budget status
   */
  async getBudgetStatus(scope: 'user' | 'team', scopeId: string): Promise<BudgetStatus> {
    const daily = this.budgets.get(this.getBudgetId('user', scopeId, 'daily'));
    const monthly = this.budgets.get(this.getBudgetId('user', scopeId, 'monthly'));

    return {
      daily: daily ? {
        limit: daily.limit,
        spent: daily.spent,
        remaining: daily.limit - daily.spent,
        percentage: (daily.spent / daily.limit) * 100
      } : null,
      monthly: monthly ? {
        limit: monthly.limit,
        spent: monthly.spent,
        remaining: monthly.limit - monthly.spent,
        percentage: (monthly.spent / monthly.limit) * 100
      } : null
    };
  }
}
```

---

## 9. Compliance & Auditing

### Audit Logging

```typescript
// audit/logger.ts

export interface AuditEvent {
  eventId: string;
  timestamp: Date;
  userId?: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  result: 'success' | 'failure';
  error?: string;
}

/**
 * Comprehensive audit logging for AI operations
 */
export class AuditLogger {
  private store: AuditStore;

  /**
   * Log AI request
   */
  async logRequest(event: {
    userId?: string;
    model: string;
    prompt: string;
    promptLength: number;
    response: string;
    responseLength: number;
    latency: number;
    cost: number;
    metadata?: Record<string, any>;
  }): Promise<void> {
    const auditEvent: AuditEvent = {
      eventId: this.generateId(),
      timestamp: new Date(),
      userId: event.userId,
      action: 'ai_request',
      resource: event.model,
      details: {
        promptLength: event.promptLength,
        responseLength: event.responseLength,
        latency: event.latency,
        cost: event.cost,
        ...event.metadata
      },
      result: 'success'
    };

    // Sanitize sensitive data from prompt/response
    auditEvent.details.promptHash = this.hash(event.prompt);
    auditEvent.details.responseHash = this.hash(event.response);

    await this.store.write(auditEvent);
  }

  /**
   * Log prompt template change
   */
  async logPromptChange(event: {
    userId: string;
    templateId: string;
    oldVersion: number;
    newVersion: number;
    changes: string[];
  }): Promise<void> {
    const auditEvent: AuditEvent = {
      eventId: this.generateId(),
      timestamp: new Date(),
      userId: event.userId,
      action: 'prompt_template_updated',
      resource: event.templateId,
      details: {
        oldVersion: event.oldVersion,
        newVersion: event.newVersion,
        changes: event.changes
      },
      result: 'success'
    };

    await this.store.write(auditEvent);
  }

  /**
   * Log model deployment
   */
  async logModelDeployment(event: {
    userId: string;
    modelId: string;
    version: string;
    environment: 'staging' | 'production';
  }): Promise<void> {
    const auditEvent: AuditEvent = {
      eventId: this.generateId(),
      timestamp: new Date(),
      userId: event.userId,
      action: 'model_deployed',
      resource: event.modelId,
      details: {
        version: event.version,
        environment: event.environment
      },
      result: 'success'
    };

    await this.store.write(auditEvent);
  }

  /**
   * Query audit log
   */
  async query(filters: {
    userId?: string;
    action?: string;
    resource?: string;
    startTime?: Date;
    endTime?: Date;
    limit?: number;
  }): Promise<AuditEvent[]> {
    return await this.store.query(filters);
  }
}
```

### Compliance Reporting

```typescript
// compliance/reporting.ts

/**
 * Generate compliance reports for AI operations
 */
export class ComplianceReporter {
  private auditLogger: AuditLogger;
  private costTracker: CostTracker;

  /**
   * Generate AI usage report
   */
  async generateUsageReport(
    period: { start: Date; end: Date },
    scope?: { userId?: string; teamId?: string }
  ): Promise<AIUsageReport> {
    const auditEvents = await this.auditLogger.query({
      action: 'ai_request',
      startTime: period.start,
      endTime: period.end,
      ...scope
    });

    const byModel = new Map<string, {
      requestCount: number;
      totalTokens: number;
      totalCost: number;
      avgLatency: number;
    }>();

    let totalRequests = 0;
    let totalCost = 0;
    let totalTokens = 0;

    for (const event of auditEvents) {
      const model = event.resource;
      const existing = byModel.get(model) || {
        requestCount: 0,
        totalTokens: 0,
        totalCost: 0,
        avgLatency: 0
      };

      existing.requestCount++;
      existing.totalTokens += (event.details.promptLength + event.details.responseLength);
      existing.totalCost += event.details.cost;
      existing.avgLatency = (existing.avgLatency * (existing.requestCount - 1) + event.details.latency) / existing.requestCount;

      byModel.set(model, existing);

      totalRequests++;
      totalCost += event.details.cost;
      totalTokens += event.details.promptLength + event.details.responseLength;
    }

    return {
      period,
      scope,
      summary: {
        totalRequests,
        totalCost,
        totalTokens,
        uniqueModels: byModel.size
      },
      byModel: Array.from(byModel.entries()).map(([model, stats]) => ({
        model,
        ...stats
      })),
      topUsers: await this.getTopUsers(period, 10)
    };
  }

  /**
   * Generate data retention report
   */
  async generateDataRetentionReport(): Promise<DataRetentionReport> {
    // Check what data is stored and for how long
    const report: DataRetentionReport = {
      auditLogs: {
        retentionDays: 365,
        count: await this.auditLogger.count({ age: 'all' }),
        oldestRecord: await this.auditLogger.getOldestDate(),
        newestRecord: await this.auditLogger.getNewestDate()
      },
      promptVersions: {
        retentionDays: 'indefinite',
        count: await this.promptStore.count(),
        oldestVersion: await this.promptStore.getOldestDate()
      },
      cache: {
        retentionDays: 7,
        count: await this.cacheStore.count(),
        hitRate: await this.cacheStore.getHitRate()
      },
      recommendations: {
        retentionDays: 90,
        count: await this.recommendationStore.count(),
        hasUserConsent: await this.consentStore.hasConsentFor('recommendations')
      }
    };

    return report;
  }
}
```

---

## 10. Incident Response

### Incident Management

```typescript
// incidents/manager.ts

export interface AIIncident {
  incidentId: string;
  type: 'model_failure' | 'cost_overrun' | 'safety_breach' | 'performance_degradation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'mitigated' | 'resolved' | 'closed';
  title: string;
  description: string;
  detectedAt: Date;
  resolvedAt?: Date;
  affectedSystems: string[];
  metrics: {
    usersAffected: number;
    requestsFailed: number;
    costImpact: number;
  };
  timeline: IncidentEvent[];
  rootCause?: string;
  resolution?: string;
  postmortem?: string;
}

/**
 * AI incident management
 */
export class IncidentManager {
  private store: IncidentStore;
  private alertManager: AlertManager;

  /**
   * Create incident from alert
   */
  async createFromAlert(alert: Alert): Promise<AIIncident> {
    const incident: AIIncident = {
      incidentId: this.generateId(),
      type: this.classifyAlertType(alert),
      severity: this.classifySeverity(alert),
      status: 'open',
      title: alert.title,
      description: alert.description,
      detectedAt: new Date(),
      affectedSystems: alert.metadata?.affectedSystems || [],
      metrics: {
        usersAffected: 0,
        requestsFailed: 0,
        costImpact: 0
      },
      timeline: [{
        timestamp: new Date(),
        event: 'Incident detected from alert',
        details: alert
      }]
    };

    await this.store.save(incident);

    // Notify on-call
    await this.alertManager.notify({
      severity: incident.severity,
      title: `AI Incident: ${incident.title}`,
      description: incident.description,
      incidentId: incident.incidentId
    });

    return incident;
  }

  /**
   * Update incident status
   */
  async updateStatus(
    incidentId: string,
    status: AIIncident['status'],
    updates: Partial<AIIncident>
  ): Promise<AIIncident> {
    const incident = await this.store.get(incidentId);
    if (!incident) {
      throw new Error(`Incident ${incidentId} not found`);
    }

    incident.status = status;

    // Add timeline event
    incident.timeline.push({
      timestamp: new Date(),
      event: `Status changed to ${status}`,
      details: updates
    });

    // Set resolved time if appropriate
    if (status === 'resolved' || status === 'closed') {
      incident.resolvedAt = new Date();
    }

    // Apply updates
    Object.assign(incident, updates);

    await this.store.save(incident);
    return incident;
  }

  /**
   * Generate postmortem
   */
  async generatePostmortem(incidentId: string): Promise<string> {
    const incident = await this.store.get(incidentId);
    if (!incident) {
      throw new Error(`Incident ${incidentId} not found`);
    }

    const postmortem = `
# AI Incident Postmortem: ${incident.title}

## Summary
- **Incident ID**: ${incident.incidentId}
- **Type**: ${incident.type}
- **Severity**: ${incident.severity}
- **Duration**: ${incident.detectedAt} to ${incident.resolvedAt || 'ongoing'}
- **Users Affected**: ${incident.metrics.usersAffected}

## Timeline
${incident.timeline.map(e =>
  `- **${e.timestamp.toISOString()}**: ${e.event}`
).join('\n')}

## Root Cause
${incident.rootCause || 'Under investigation'}

## Resolution
${incident.resolution || 'Pending'}

## Action Items
${this.generateActionItems(incident).map(item => `- [ ] ${item}`).join('\n')}

## Prevention
${this.generatePreventionItems(incident).map(item => `- [ ] ${item}`).join('\n')}
    `.trim();

    incident.postmortem = postmortem;
    await this.store.save(incident);

    return postmortem;
  }

  private generateActionItems(incident: AIIncident): string[] {
    const items: string[] = [];

    if (incident.type === 'model_failure') {
      items.push('Review model training data for issues');
      items.push('Add additional test cases for failure scenario');
      items.push('Implement fallback model');
    }

    if (incident.type === 'cost_overrun') {
      items.push('Review cost monitoring alerts');
      items.push('Add stricter budget controls');
      items.push('Optimize expensive API calls');
    }

    if (incident.type === 'safety_breach') {
      items.push('Review moderation filters');
      items.push('Add additional safety checks');
      items.push('Review incident with safety team');
    }

    if (incident.type === 'performance_degradation') {
      items.push('Review infrastructure capacity');
      items.push('Add performance alerts');
      items.push('Implement caching for slow queries');
    }

    return items;
  }

  private generatePreventionItems(incident: AIIncident): string[] {
    const items: string[] = [];

    items.push('Update runbook with lessons learned');
    items.push('Add monitoring for early detection');
    items.push('Conduct blameless postmortem meeting');

    return items;
  }
}
```

---

## 11. API Specification

### Monitoring Endpoints

```typescript
// api/monitoring.ts

/**
 * GET /api/ai/monitoring/health
 * Get AI system health status
 */
interface HealthStatusResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  models: Array<{
    name: string;
    status: 'operational' | 'degraded' | 'down';
    latency: {
      p50: number;
      p95: number;
      p99: number;
    };
    errorRate: number;
  }>;
  alerts: Alert[];
}

/**
 * GET /api/ai/monitoring/metrics
 * Get AI metrics
 */
interface MetricsRequest {
  model?: string;
  timeRange: string;  // e.g., '1h', '24h', '7d'
  aggregation?: 'avg' | 'sum' | 'percentiles';
}

interface MetricsResponse {
  latency: number[];
  throughput: number[];
  errorRate: number[];
  tokenUsage: {
    input: number[];
    output: number[];
  };
  cost: number[];
}

/**
 * GET /api/ai/monitoring/drift
 * Check for model drift
 */
interface DriftCheckResponse {
  drifted: boolean;
  driftScore: number;
  driftType: string;
  details: Record<string, any>;
  recommendation: string;
}
```

### Cost Endpoints

```typescript
// api/cost.ts

/**
 * GET /api/ai/cost/report
 * Get cost report
 */
interface CostReportRequest {
  startDate: string;
  endDate: string;
  groupBy?: 'model' | 'endpoint' | 'user' | 'day';
}

interface CostReportResponse {
  period: { start: string; end: string };
  totalCost: number;
  breakdown: Array<{
    group: string;
    cost: number;
    percentage: number;
    change?: number;  // vs previous period
  }>;
  forecast: {
    next7Days: number;
    next30Days: number;
  };
  optimization: Array<{
    type: string;
    description: string;
    potentialSavings: number;
  }>;
}

/**
 * GET /api/ai/cost/budget
 * Get budget status
 */
interface BudgetStatusResponse {
  daily: {
    limit: number;
    spent: number;
    remaining: number;
    percentage: number;
  } | null;
  weekly: {
    limit: number;
    spent: number;
    remaining: number;
    percentage: number;
  } | null;
  monthly: {
    limit: number;
    spent: number;
    remaining: number;
    percentage: number;
  } | null;
}
```

### Prompt Management Endpoints

```typescript
// api/prompts.ts

/**
 * POST /api/ai/prompts
 * Create new prompt template
 */
interface CreatePromptRequest {
  name: string;
  description: string;
  template: string;
  variables: string[];
  config: {
    model: string;
    temperature?: number;
    maxTokens?: number;
  };
}

interface CreatePromptResponse {
  id: string;
  version: number;
  status: string;
}

/**
 * GET /api/ai/prompts/:id
 * Get prompt template
 */
interface GetPromptResponse {
  id: string;
  name: string;
  description: string;
  version: number;
  status: string;
  template: string;
  variables: string[];
  config: Record<string, any>;
  metadata: {
    author: string;
    createdAt: string;
    updatedAt: string;
    usageCount: number;
  };
}

/**
 * PUT /api/ai/prompts/:id
 * Update prompt template (creates new version)
 */
interface UpdatePromptRequest {
  template?: string;
  config?: Record<string, any>;
}

interface UpdatePromptResponse {
  id: string;
  version: number;
  changes: {
    template: string[] | null;
    config: Record<string, any> | null;
  };
}

/**
 * POST /api/ai/prompts/:id/rollback
 * Rollback to previous version
 */
interface RollbackPromptRequest {
  toVersion?: number;
}

/**
 * POST /api/ai/prompts/:id/test
 * Test prompt template
 */
interface TestPromptRequest {
  variables: Record<string, any>;
  testCases?: Array<{
    id: string;
    variables: Record<string, any>;
    expected: {
      includes?: string[];
      excludes?: string[];
      output?: string;
    };
  }>;
}

interface TestPromptResponse {
  rendered: string;
  testResults?: {
    totalCases: number;
    passed: number;
    failed: number;
    results: Array<{
      testCaseId: string;
      passed: boolean;
      response: string;
      evaluation: Record<string, number>;
    }>;
  };
}
```

### Experiment Endpoints

```typescript
// api/experiments.ts

/**
 * POST /api/ai/experiments
 * Create A/B test
 */
interface CreateExperimentRequest {
  name: string;
  description: string;
  templateId: string;
  variants: Array<{
    version: number;
    name: string;
  }>;
  config: {
    trafficSplit: number[];
    successMetric: 'rating' | 'satisfaction' | 'conversion';
    minSampleSize: number;
    duration?: number;  // milliseconds
  };
}

/**
 * GET /api/ai/experiments/:id
 * Get experiment results
 */
interface GetExperimentResponse {
  experimentId: string;
  name: string;
  status: string;
  variants: Array<{
    version: number;
    name: string;
    traffic: number;
    metrics: {
      exposures: number;
      successes: number;
      successRate: number;
      avgRating: number;
      avgLatency: number;
    };
  }>;
  results?: {
    winner: number;
    confidence: number;
    pValue: number;
    significance: string;
  };
}
```

---

## 12. Testing Scenarios

### Integration Tests

```typescript
// __tests__/integration/ai-ops.test.ts

describe('AI Operations Integration', () => {
  describe('Cost tracking flow', () => {
    it('should track costs and generate reports', async () => {
      // Make some AI requests
      await app.request('/api/ai/generate', {
        method: 'POST',
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          prompt: 'Test prompt'
        })
      });

      await app.request('/api/ai/generate', {
        method: 'POST',
        body: JSON.stringify({
          model: 'gpt-4',
          prompt: 'Test prompt'
        })
      });

      // Get cost report
      const report = await app.request('/api/ai/cost/report', {
        method: 'GET',
        query: { timeRange: '1h' }
      });

      expect(report.status).toBe(200);
      const data = await report.json();

      expect(data.totalCost).toBeGreaterThan(0);
      expect(data.breakdown).toHaveLength(2);
    });
  });

  describe('Prompt versioning', () => {
    it('should version prompts on update', async () => {
      // Create prompt
      const create = await app.request('/api/ai/prompts', {
        method: 'POST',
        body: JSON.stringify({
          name: 'test-prompt',
          description: 'Test',
          template: 'Hello {{name}}',
          variables: ['name'],
          config: { model: 'gpt-3.5-turbo' }
        })
      });

      const { id, version: v1 } = await create.json();

      // Update prompt
      const update = await app.request(`/api/ai/prompts/${id}`, {
        method: 'PUT',
        body: JSON.stringify({
          template: 'Hi {{name}}, welcome!'
        })
      });

      const { version: v2 } = await update.json();

      expect(v2).toBe(v1 + 1);

      // Rollback
      const rollback = await app.request(`/api/ai/prompts/${id}/rollback`, {
        method: 'POST'
      });

      const { version: v3 } = await rollback.json();
      expect(v3).toBe(v1);
    });
  });

  describe('Budget enforcement', () => {
    it('should block requests when budget exceeded', async () => {
      // Set low budget
      await app.request('/api/ai/cost/budget', {
        method: 'PUT',
        body: JSON.stringify({
          period: 'daily',
          limit: 0.01  // Very low
        })
      });

      // Try to make request
      const response = await app.request('/api/ai/generate', {
        method: 'POST',
        body: JSON.stringify({
          model: 'gpt-4',
          prompt: 'A'.repeat(1000)  // Expensive
        })
      });

      expect(response.status).toBe(429);
      expect(await response.json()).toMatchObject({
        error: expect.stringContaining('budget')
      });
    });
  });

  describe('Drift detection', () => {
    it('should detect model drift', async () => {
      const result = await app.request('/api/ai/monitoring/drift', {
        method: 'GET',
        query: { model: 'recommendation-engine' }
      });

      expect(result.status).toBe(200);
      const data = await result.json();

      expect(data).toHaveProperty('drifted');
      expect(data).toHaveProperty('driftScore');
      expect(data).toHaveProperty('recommendation');
    });
  });
});
```

---

## Summary

This document defines the AI Operations & Governance framework for the Travel Agency Agent platform:

**Key Components:**
- **Model Monitoring**: Performance tracking, drift detection, anomaly detection
- **Cost Management**: Usage tracking, budgeting, forecasting, optimization
- **Prompt Management**: Versioning, testing, A/B testing, rollback
- **Safety Rails**: Content moderation, output validation, PII redaction
- **Rate Limiting**: User and global limits, budget enforcement
- **Compliance**: Audit logging, retention policies, reporting
- **Incident Response**: Detection, investigation, postmortem

**Integration Points:**
- All AI/ML features monitored through this framework
- Cost tracking across all AI API calls
- Prompt versioning for LLM-based features
- Safety checks on all AI outputs

---

**Series Complete:** AI/ML Patterns (4 of 4 documents)

**Related Documents:**
- [AIML_01: LLM Integration Patterns](./AIML_01_LLM_INTEGRATION_PATTERNS.md)
- [AIML_02: Decision Intelligence](./AIML_02_DECISION_INTELLIGENCE.md)
- [AIML_03: NLP Patterns](./AIML_03_NLP_PATTERNS.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-04-25
**Status:** ✅ Complete
