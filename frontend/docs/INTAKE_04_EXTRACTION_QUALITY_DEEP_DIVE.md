# Intake Extraction Quality Deep Dive

> Measuring, improving, and maintaining data extraction quality

**Document:** INTAKE_04_EXTRACTION_QUALITY_DEEP_DIVE.md
**Series:** Intake / Packet Processing Deep Dive
**Status:** ✅ Complete
**Last Updated:** 2026-04-23
**Related:** [INTAKE_01_TECHNICAL_DEEP_DIVE.md](./INTAKE_01_TECHNICAL_DEEP_DIVE.md)

---

## Table of Contents

1. [Quality Framework](#quality-framework)
2. [Accuracy Metrics](#accuracy-metrics)
3. [Error Analysis](#error-analysis)
4. [Confidence Calibration](#confidence-calibration)
5. [Continuous Learning](#continuous-learning)
6. [Quality Assurance](#quality-assurance)
7. [Field-Specific Patterns](#field-specific-patterns)
8. [Improvement Strategies](#improvement-strategies)
9. [Implementation Reference](#implementation-reference)

---

## 1. Quality Framework

### The Quality Pyramid

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTRACTION QUALITY PYRAMID                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          ┌─────────────────┐                               │
│                          │   PERFECTION     │                               │
│                          │   100% Accuracy  │                               │
│                          │   Zero Errors    │                               │
│                          │                 │                               │
│                          └─────────────────┘                               │
│                                   │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        EXCELLENCE (Target)                         │   │
│  │  • 95%+ field-level accuracy                                        │   │
│  │  • <2% critical field errors                                        │   │
│  │  • Confidence well-calibrated (ECE < 0.05)                         │   │
│  │  • Errors detected and flagged                                      │   │
│  │  • Continuous improvement from feedback                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ACCEPTABLE (Minimum)                        │   │
│  │  • 85%+ field-level accuracy                                        │   │
│  │  • <5% critical field errors                                        │   │
│  │  • High-confidence fields >90% accurate                             │   │
│  │  • Medium/low confidence flagged                                   │   │
│  │  • Basic error detection                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                            UNACCEPTABLE                             │   │
│  │  • <85% field-level accuracy                                        │   │
│  │  • >5% critical field errors                                        │   │
│  │  • Poor confidence calibration                                     │   │
│  │  • Errors not detected                                             │   │
│  │  • No learning from corrections                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quality Dimensions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       QUALITY DIMENSIONS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DIMENSION 1: FIELD ACCURACY                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ What % of extracted fields are correct?                             │   │
│  │                                                                     │   │
│  │ Measured by:                                                        │   │
│  │ • Agent correction rate                                             │   │
│  │ • Customer confirmation (explicit)                                  │   │
│  │ • Outcome validation (did booking match?)                          │   │
│  │                                                                     │   │
│  │ Target: >90% for critical fields                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIMENSION 2: CONFIDENCE CALIBRATION                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Does confidence score reflect actual accuracy?                      │   │
│  │                                                                     │   │
│  │ Measured by:                                                        │   │
│  │ • Expected Calibration Error (ECE)                                  │   │
│  │ • Brier score                                                      │   │
│  │ • Reliability diagram                                               │   │
│  │                                                                     │   │
│  │ Target: ECE < 0.05                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIMENSION 3: COMPLETENESS                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ What % of extractable fields are captured?                         │   │
│  │                                                                     │   │
│  │ Measured by:                                                        │   │
│  │ • Field coverage (present vs absent)                                │   │
│  │ • Missing critical fields rate                                     │   │
│  │                                                                     │   │
│  │ Target: >95% of present fields extracted                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DIMENSION 4: CONSISTENCY                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Do similar inputs produce similar outputs?                           │   │
│  │                                                                     │   │
│  │ Measured by:                                                        │   │
│  │ • Variance in extraction for similar messages                        │   │
│  │ • Temporal stability (no drift over time)                           │   │
│  │                                                                     │   │
│  │ Target: <5% variance for similar inputs                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Accuracy Metrics

### Field-Level Accuracy Tracking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FIELD-LEVEL ACCURACY TRACKING                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRACKING METHOD:                                                         │
│  For each extracted field, track:                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Original extracted value                                         │   │
│  │ 2. Confidence score                                                │   │
│  │ 3. Agent correction (if any)                                       │   │
│  │ 4. Customer confirmation (if obtained)                              │   │
│  │ 5. Final validated value                                            │   │
│  │ 6. Correct? (binary)                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACCURACY CALCULATION:                                                     │
│  Accuracy = Correct Extractions / Total Extractions                       │
│                                                                             │
│  Example for Destination field:                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Total extractions: 1,000                                           │   │
│  │  Correct: 942                                                        │   │
│  │  Accuracy: 94.2%                                                     │   │
│  │                                                                     │   │
│  │  Breakdown by confidence band:                                      │   │
│  │  • Very High (>90%): 98.7% accuracy (500 samples)                   │   │
│  │  • High (70-90%): 94.1% accuracy (350 samples)                      │   │
│  │  • Medium (50-70%): 87.3% accuracy (120 samples)                     │   │
│  │  • Low (<50%): 68.9% accuracy (30 samples)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Accuracy by Field Type

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACCURACY BY FIELD TYPE (Benchmarks)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Field Type           │ Current │ Target │ Difficulty               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Destination          │  94.2%  │  95%   │ Medium                   │   │
│  │ Dates (specific)     │  89.7%  │  92%   │ Hard (formats vary)     │   │
│  │ Dates (month/year)   │  96.1%  │  97%   │ Easy                     │   │
│  │ Travelers (adults)   │  98.3%  │  99%   │ Easy (explicit)         │   │
│  │ Travelers (children)  │  85.2%  │  90%   │ Medium (often omitted)   │   │
│  │ Budget (explicit)     │  91.8%  │  93%   │ Medium                   │   │
│  │ Budget (implied)      │  78.4%  │  85%   │ Hard                    │   │
│  │ Trip Type             │  72.1%  │  80%   │ Hard (requires infer.)   │   │
│  │ Accommodation pref    │  65.3%  │  75%   │ Very Hard               │   │
│  │ Phone number          │  97.8%  │  99%   │ Easy (pattern match)     │   │
│  │ Email address         │  98.1%  │  99%   │ Easy (pattern match)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OVERALL ACCURACY:                                                          │
│  • Critical fields (dest, dates, travelers): 93.1%                        │
│  • Important fields (budget, contact): 94.7%                             │
│  • Nice-to-have fields (preferences): 68.9%                              │
│  • Weighted overall: 91.4%                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Accuracy Monitoring

```typescript
// Accuracy Monitoring Service
interface AccuracyMonitor {
  // Record extraction result
  recordExtraction(params: {
    inquiryId: string;
    field: string;
    extractedValue: any;
    confidence: number;
    method: 'llm' | 'rules' | 'hybrid';
  }): Promise<void>;

  // Record correction (agent or customer)
  recordCorrection(params: {
    inquiryId: string;
    field: string;
    originalValue: any;
    correctedValue: any;
    correctedBy: 'agent' | 'customer';
  }): Promise<void>;

  // Get accuracy metrics
  getAccuracyMetrics(params: {
    field?: string;
    period?: DateRange;
    confidenceBand?: string;
  }): Promise<AccuracyMetrics>;

  // Generate accuracy report
  generateReport(period: DateRange): Promise<AccuracyReport>;
}

interface AccuracyMetrics {
  overall: number;                   // 0-1
  byField: Record<string, FieldAccuracy>;
  byConfidenceBand: Record<string, ConfidenceBandAccuracy>;
  byMethod: Record<string, number>;   // llm vs rules vs hybrid
  trend: Array<{
    date: string;
    accuracy: number;
  }>;
}

interface FieldAccuracy {
  field: string;
  total: number;
  correct: number;
  accuracy: number;
  confidence: number;                 // Avg confidence for this field
  commonErrors: Array<{
    error: string;
    frequency: number;
    example: string;
  }>;
}

// Usage example
const monitor = new AccuracyMonitor();

// When extraction completes
await monitor.recordExtraction({
  inquiryId: 'inq_123',
  field: 'destination',
  extractedValue: 'Goa',
  confidence: 0.92,
  method: 'hybrid'
});

// When agent corrects
await monitor.recordCorrection({
  inquiryId: 'inq_123',
  field: 'destination',
  originalValue: 'Goa',
  correctedValue: 'North Goa',
  correctedBy: 'agent'
});

// Get current accuracy
const metrics = await monitor.getAccuracyMetrics({
  period: { start: new Date(Date.now() - 30*24*60*60*1000), end: new Date() }
});

console.log(`Destination accuracy: ${metrics.byField.destination.accuracy * 100}%`);
```

---

## 3. Error Analysis

### Error Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ERROR TAXONOMY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ERROR CATEGORY 1: MISSED EXTRACTION                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Definition: Field present in message but not extracted               │   │
│  │                                                                     │   │
│  │ Examples:                                                           │   │
│  │ • "Planning trip to [Goa]" → Destination not captured            │   │
│  │ • "Budget around 80k" → Budget: null                                │   │
│  │                                                                     │   │
│  │ Root Causes:                                                        │   │
│  │ • LLM missed the information                                       │   │
│  │ • Pattern didn't match                                             │   │
│  │ • Context lost in preprocessing                                    │   │
│  │                                                                     │   │
│  │ Prevention:                                                         │   │
│  │ • Improve prompts                                                  │   │
│  │ • Add more patterns                                               │   │
│  │ • Multi-pass extraction                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ERROR CATEGORY 2: INCORRECT EXTRACTION                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Definition: Field extracted but wrong value                        │   │
│  │                                                                     │   │
│  │ Examples:                                                           │   │
│  │ • "North Goa" → Extracted as "Goa" (lost specificity)            │   │
│  │ • "May 2025" → Extracted as "May 15" (invented date)             │   │
│  │ • "4 adults, 2 kids" → Extracted 6 adults                         │   │
│  │                                                                     │   │
│  │ Root Causes:                                                        │   │
│  │ • Over-generalization                                             │   │
│  │ • Hallucination (LLM invented value)                              │   │
│  │ • Ambiguity resolved incorrectly                                   │   │
│  │                                                                     │   │
│  │ Prevention:                                                         │   │
│  │ • Constrain extraction to explicit text                            │   │
│  │ • Flag low confidence for ambiguous cases                           │   │
│  │ • Cross-validate with rules                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ERROR CATEGORY 3: FALSE POSITIVE                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Definition: Field extracted but not actually present               │   │
│  │                                                                     │   │
│  │ Examples:                                                           │   │
│  │ • "Maybe next year" → Dates: 2026 (inferred)                      │   │
│  │ • "If budget allows" → Budget: high (speculative)                 │   │
│  │                                                                     │   │
│  │ Root Causes:                                                        │   │
│  │ • Over-eager inference                                            │   │
│  │ • Conditional statements treated as facts                         │   │
│  │                                                                     │   │
│  │ Prevention:                                                         │   │
│  │ • Extract only explicit information                                │   │
│  │ • Flag inferences separately                                       │   │
│  │ • Lower confidence for inferred values                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ERROR CATEGORY 4: FORMAT ERROR                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Definition: Value extracted but wrong format                        │   │
│  │                                                                     │   │
│  │ Examples:                                                           │   │
│  │ • "May 15-20" → Start: May 20, End: May 15 (swapped)             │   │
│  │ • "15.05.2025" → Date: Invalid format                              │   │
│  │ • "+91 98765 43210" → Phone: 9876543210 (lost country code)       │   │
│  │                                                                     │   │
│  │ Root Causes:                                                        │   │
│  │ • Date format confusion                                           │   │
│  │ • Indian vs international date format                              │   │
│  │ • Phone number normalization                                       │   │
│  │                                                                     │   │
│  │ Prevention:                                                         │   │
│  │ • Multi-format date parsing                                        │   │
│  │ • Validation during extraction                                     │   │
│  │ • Format-specific patterns                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Frequency Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ERROR FREQUENCY ANALYSIS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TOP ERRORS BY FREQUENCY (Last 30 days):                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Rank │ Error Type                   │ Count │ % of Total │ Priority │   │   │
│  ├──────┼─────────────────────────────┼───────┼────────────┼──────────┤   │   │
│  │  1   │ Missed year in date          │  234  │   18.2%    │   High   │   │   │
│  │  2   │ Date format confusion        │  189  │   14.7%    │   High   │   │   │
│  │  3   │ Budget implied as exact       │  156  │   12.1%    │  Medium  │   │   │
│  │  4   │ Destination specificity lost │  142  │   11.0%    │   Medium  │   │   │
│  │  5   │ Travelers count ambiguous     │  118  │    9.2%    │   High   │   │   │
│  │  6   │ Phone number truncation       │   89  │    6.9%    │   Low    │   │   │
│  │  7   │ Children omitted              │   78  │    6.1%    │   High   │   │   │
│  │  8   │ Hallucinated dates            │   67  │    5.2%    │   High   │   │   │
│  │  9   │ Destination misspelling       │   56  │    4.4%    │   Low    │   │
│  │ 10   │ Currency confusion            │   45  │    3.5%    │   Medium  │   │   │
│  │      │ TOTAL                        │ 1284  │  100.0%    │          │   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TRENDING ERRORS (Increasing frequency):                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Hallucinated dates: +45% in last 2 weeks ⚠️                       │   │
│  │ • Budget implied as exact: +32% in last month                        │   │
│  │ • Children omitted: +28% in peak season                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IMPROVING ERRORS (Decreasing frequency):                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Phone number truncation: -67% (after pattern update) ✓           │   │
│  │ • Destination misspelling: -45% (after fuzzy matching) ✓            │   │
│  │ • Date format confusion: -23% (after multi-format parser) ✓         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Error Pattern Analysis

```typescript
// Error Analysis Service
interface ErrorAnalysisService {
  // Analyze errors for a period
  analyzeErrors(period: DateRange): Promise<ErrorAnalysisReport>;

  // Get error patterns for a specific field
  getFieldErrorPatterns(field: string): Promise<FieldErrorPattern[]>;

  // Suggest improvements based on error patterns
  suggestImprovements(): Promise<ImprovementSuggestion[]>;
}

interface ErrorAnalysisReport {
  period: DateRange;
  totalExtractions: number;
  totalErrors: number;
  errorRate: number;

  // Errors by type
  byType: Record<ErrorType, number>;

  // Errors by field
  byField: Record<string, FieldErrorStats>;

  // Errors by confidence band
  byConfidenceBand: Record<string, ConfidenceBandErrors>;

  // Trending errors
  trending: {
    increasing: ErrorTrend[];
    decreasing: ErrorTrend[];
  };

  // Recommendations
  recommendations: ImprovementRecommendation[];
}

interface ErrorType {
  missed: 'Field present but not extracted';
  incorrect: 'Field extracted but wrong value';
  falsePositive: 'Field extracted but not present';
  format: 'Value extracted but wrong format';
}

interface FieldErrorStats {
  field: string;
  total: number;
  errors: number;
  errorRate: number;
  accuracy: number;

  // Breakdown by error type
  byType: Record<ErrorType, number>;

  // Common patterns
  patterns: Array<{
    pattern: string;
    frequency: number;
    examples: string[];
  }>;
}

// Example output
const errorAnalysis: ErrorAnalysisReport = {
  period: { start: '2025-03-01', end: '2025-03-31' },
  totalExtractions: 15000,
  totalErrors: 1284,
  errorRate: 0.086,  // 8.6%

  byType: {
    missed: 456,      // 35.5%
    incorrect: 512,   // 39.9%
    falsePositive: 189, // 14.7%
    format: 127       // 9.9%
  },

  byField: {
    destination: {
      field: 'destination',
      total: 15000,
      errors: 198,
      errorRate: 0.013,
      accuracy: 0.987,
      byType: { missed: 142, incorrect: 45, falsePositive: 8, format: 3 },
      patterns: [
        {
          pattern: 'Destination mentioned in passing',
          frequency: 67,
          examples: ['"Maybe visit Goa if time permits"']
        },
        {
          pattern: 'Multiple destinations, ambiguous primary',
          frequency: 45,
          examples: ['"Goa and Kerala trip"']
        }
      ]
    },
    dates: {
      field: 'dates',
      total: 15000,
      errors: 423,
      errorRate: 0.028,
      accuracy: 0.972,
      byType: { missed: 234, incorrect: 156, falsePositive: 22, format: 11 },
      patterns: [
        {
          pattern: 'Year not specified',
          frequency: 234,
          examples: ['"May 15-20"', '"second week of May"']
        },
        {
          pattern: 'Date format: DD.MM.YYYY (Indian)',
          frequency: 89,
          examples: ['"15.05.2025"', "20.05.25"]
        }
      ]
    }
  },

  recommendations: [
    {
      priority: 'high',
      type: 'prompt_improvement',
      field: 'dates',
      description: 'Add explicit year detection',
      expectedImpact: '-40% date errors',
      effort: 'medium'
    },
    {
      priority: 'high',
      type: 'pattern_addition',
      field: 'dates',
      description: 'Add DD.MM.YYYY date pattern',
      expectedImpact: '-35% format errors',
      effort: 'low'
    }
  ]
};
```

---

## 4. Confidence Calibration

### Calibration Assessment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONFIDENCE CALIBRATION ASSESSMENT                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RELIABILITY DIAGRAM:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Accuracy                                                             │   │
│  │ 100% ┼                                          ╱────────────       │   │
│  │  90% ┼                              ╱─────────                   │   │
│  │  80% ┼                    ╱───────────                           │   │
│  │  70% ┼         ╱────────────                                        │   │
│  │      └──────────────────────────────────────────── Confidence →    │   │
│  │       50%    60%    70%    80%    90%   100%                      │   │
│  │                                                                     │   │
│  │  IDEAL: Points on diagonal line (confidence = accuracy)            │   │
│  │  ACTUAL: Dots show calibration quality                             │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Current Model:                                                │   │   │
│  │  │   • 90-100% confidence → 94% accuracy (slightly overconfident)│   │   │
│  │  │   • 70-90% confidence → 87% accuracy (well calibrated)        │   │   │
│  │  │   • 50-70% confidence → 78% accuracy (slightly underconfident) │   │   │
│  │  │   • <50% confidence → 62% accuracy (overconfident)           │   │   │
│  │  │                                                             │   │   │
│  │  │ ECE (Expected Calibration Error): 0.042                      │   │   │
│  │  │ Target: < 0.05 ✓                                             │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CALIBRATION METRICS:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Metric        │ Value    │ Target   │ Status                     │   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ ECE           │ 0.042   │ < 0.05  │ ✓ Well calibrated          │   │   │
│  │ Brier Score   │ 0.089   │ < 0.10  │ ✓ Good                    │   │   │
│  │ Calibration   │ 0.96    │ > 0.90  │ ✓ Excellent                │   │   │
│  │   Slope                                                                    │   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Calibration Methods

```typescript
// Confidence Calibration Service
interface CalibrationService {
  // Calibrate confidence scores using Platt Scaling
  calibratePlattScaling(params: {
    field: string;
    predictions: Array<{ confidence: number; correct: boolean }>;
  }): Promise<PlattScalingModel>;

  // Apply calibration to new prediction
  applyCalibration(params: {
    field: string;
    rawConfidence: number;
  }): Promise<number>;

  // Get calibration metrics
  getCalibrationMetrics(field: string): Promise<CalibrationMetrics>;
}

// Platt Scaling implementation
class PlattCalibrator {
  /**
   * Train Platt Scaling model
   * Maps raw confidence to calibrated probability
   *
   * P(calibrated) = 1 / (1 + exp(A * raw_confidence + B))
   *
   * Parameters A and B learned from validation data
   */
  train(data: Array<{ confidence: number; correct: boolean }>): PlattScalingParams {
    // Optimize A and B using maximum likelihood
    const { A, B } = this.optimizePlattParams(data);

    return { A, B };
  }

  /**
   * Apply calibration
   */
  calibrate(rawConfidence: number, params: PlattScalingParams): number {
    const logistic = 1 / (1 + Math.exp(params.A * rawConfidence + params.B));
    return logistic;
  }

  private optimizePlattParams(data: Array<{ confidence: number; correct: boolean }>) {
    // Use Newton's method or similar optimization
    // This is a simplified version
    let A = 1, B = 0;
    const learningRate = 0.01;
    const iterations = 100;

    for (let i = 0; i < iterations; i++) {
      let gradientA = 0, gradientB = 0;

      for (const point of data) {
        const z = A * point.confidence + B;
        const p = 1 / (1 + Math.exp(-z));
        const y = point.correct ? 1 : 0;

        gradientA += (p - y) * point.confidence;
        gradientB += (p - y);
      }

      A -= learningRate * gradientA / data.length;
      B -= learningRate * gradientB / data.length;
    }

    return { A, B };
  }
}

// Usage example
const calibrator = new PlattCalibrator();

// Train on past week's data
const trainingData = await loadCalibrationTrainingData({
  field: 'destination',
  period: { start: new Date(Date.now() - 7*24*60*60*1000), end: new Date() }
});

const params = calibrator.train(trainingData);

// Apply to new prediction
const rawConfidence = 0.85;
const calibratedConfidence = calibrator.calibrate(rawConfidence, params);
// If model tends to be overconfident, calibrated will be lower
```

---

## 5. Continuous Learning

### Learning Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONTINUOUS LEARNING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. DATA COLLECTION                                               │   │
│  │     • Agent corrections                                            │   │
│  │     • Customer confirmations                                       │   │
│  │     • Booking outcomes                                            │   │
│  │     • Extraction results                                          │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                             │                                             │
│                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2. VALIDATION & CLEANING                                         │   │
│  │     • Remove duplicates                                           │   │
│  │     • Verify corrections are valid                                 │   │
│  │     • Flag ambiguous cases                                         │   │
│  │     • Balance dataset (avoid bias)                                 │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                             │                                             │
│                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  3. PATTERN ANALYSIS                                             │   │
│  │     • Identify error patterns                                      │   │
│  │     • Find common failure modes                                    │   │
│  │     • Detect drift over time                                       │   │
│  │     • Segment by difficulty                                         │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                             │                                             │
│                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  4. MODEL UPDATE                                                  │   │
│  │     • Update prompts based on errors                              │   │
│  │     • Add new patterns to rules                                   │   │
│  │     • Retrain calibration model                                    │   │
│  │     • A/B test improvements                                       │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                             │                                             │
│                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  5. DEPLOYMENT                                                   │   │
│  │     • Deploy updated prompts/patterns                             │   │
│  │     • Monitor accuracy improvement                                  │   │
│  │     • Roll back if degradation                                    │   │
│  │     │  Continue monitoring                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Learning from Corrections

```typescript
// Learning Service
interface LearningService {
  // Process agent correction
  processCorrection(correction: AgentCorrection): Promise<void>;

  // Generate training examples from corrections
  generateTrainingExamples(params: {
    field: string;
    period: DateRange;
  }): Promise<TrainingExample[]>;

  // Update extraction model
  updateModel(params: {
    field: string;
    examples: TrainingExample[];
  }): Promise<ModelUpdateResult>;
}

interface AgentCorrection {
  inquiryId: string;
  field: string;
  originalValue: any;
  correctedValue: any;
  originalConfidence: number;
  agentId: string;
  timestamp: Date;
  context: {
    originalMessage: string;
    extractionMethod: string;
  };
}

class LearningServiceImpl implements LearningService {
  async processCorrection(correction: AgentCorrection): Promise<void> {
    // 1. Store correction for analysis
    await this.correctionRepository.save(correction);

    // 2. Update immediate learning
    await this.updateImmediateLearning(correction);

    // 3. Check if batch retraining needed
    const correctionsCount = await this.correctionRepository.count({
      field: correction.field,
      since: new Date(Date.now() - 24*60*60*1000) // Last 24 hours
    });

    if (correctionsCount > 100) {
      await this.triggerRetraining(correction.field);
    }
  }

  private async updateImmediateLearning(correction: AgentCorrection): Promise<void> {
    // Add to pattern library for rule-based extraction
    if (this.isPatternable(correction)) {
      await this.patternLibrary.addPattern({
        field: correction.field,
        pattern: correction.context.originalMessage,
        value: correction.correctedValue,
        confidence: 1.0 // Agent correction = ground truth
      });
    }

    // Add to few-shot examples for LLM
    await this.fewShotLibrary.addExample({
      field: correction.field,
      input: correction.context.originalMessage,
      output: correction.correctedValue,
      correction: correction.originalValue // Show what NOT to do
    });
  }

  private async triggerRetraining(field: string): Promise<void> {
    // Collect recent corrections
    const corrections = await this.correctionRepository.find({
      field,
      since: new Date(Date.now() - 7*24*60*60*1000), // Last 7 days
      limit: 1000
    });

    // Generate training examples
    const examples = this.generateTrainingExamples(corrections);

    // Update prompts
    const updatedPrompt = await this.promptOptimizer.optimize({
      field,
      existingPrompt: await this.promptLibrary.get(field),
      examples
    });

    // Update pattern matching
    const updatedPatterns = await this.patternOptimizer.optimize({
      field,
      existingPatterns: await this.patternLibrary.get(field),
      corrections
    });

    // Deploy updates
    await this.deployUpdates({
      field,
      prompt: updatedPrompt,
      patterns: updatedPatterns
    });

    // Monitor for degradation
    await this.monitorAccuracy(field, 'post-update');
  }
}
```

---

## 6. Quality Assurance

### Human Review Queue

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       QUALITY ASSURANCE WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AUTOMATIC QA TRIGGERS:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Trigger to Review If:                                             │   │
│  │ • Low confidence (<50%) on critical field                          │   │
│  │ • Confidence mismatch (LLM and rules disagree significantly)        │   │
│  │ • New customer (first inquiry)                                    │   │
│  │ • High-value inquiry (budget > ₹100k)                             │   │
│  │ • Complex itinerary (multi-country, >10 travelers)                 │   │
│  │ • Unusual pattern (new destination, odd dates)                      │   │
│  │ • Recent model update (within 24 hours)                             │   │
│  │ • Random sample (5% for QA)                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  REVIEW QUEUE MANAGEMENT:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Queue Status                                                       │   │
│  │ ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ Pending Review: 47 inquiries                                  │    │   │
│  │  │ Average Age: 18 minutes                                       │    │   │
│  │  │                                                              │    │   │
│  │  │ By Priority:                                                 │    │   │
│  │  │   P0 (Critical): 3  → Review within 15 min                  │    │   │
│  │  │   P1 (High): 15      → Review within 1 hour                   │    │   │
│  │  │   P2 (Medium): 23    → Review within 4 hours                  │    │   │
│  │  │   P3 (Low): 6        → Review within 24 hours                 │    │   │
│  │  │                                                              │    │   │
│  │  │ By Reason:                                                   │    │   │
│  │  │   Low confidence: 28                                          │    │   │
│  │  │   New customer: 12                                            │    │   │
│  │  │   High value: 7                                               │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  [Claim Next] [View Queue] [Reassign] [Export Report]              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### QA Review Interface

```typescript
// QA Review Interface
interface QAReviewInterface {
  // Get next item for review
  getNextReview(params: {
    agentId?: string;
    priority?: Priority;
  }): Promise<QAReviewItem>;

  // Submit review decision
  submitReview(params: {
    inquiryId: string;
    decision: 'approve' | 'correct' | 'escalate';
    corrections?: FieldCorrection[];
    notes?: string;
  }): Promise<void>;
}

interface QAReviewItem {
  inquiryId: string;
  priority: Priority;
  reasonForReview: string;
  urgency: 'immediate' | 'normal' | 'low';

  extraction: {
    fields: TripFields;
    confidence: Record<string, number>;
    source: Record<string, 'llm' | 'rules' | 'hybrid'>;
  };

  originalMessage: string;
  channel: MessageChannel;
  customerInfo: CustomerInfo;

  suggestedActions: string[];
}

// QA Review Workflow
class QAReviewWorkflow {
  async reviewItem(item: QAReviewItem): Promise<ReviewDecision> {
    // Present item for review
    const decision = await this.presentForReview(item);

    // Record decision
    await this.recordDecision({
      inquiryId: item.inquiryId,
      decision,
      reviewerId: this.currentAgentId,
      timestamp: new Date()
    });

    // If corrections made, trigger learning
    if (decision.corrections && decision.corrections.length > 0) {
      await this.learningService.processCorrections(decision.corrections);
    }

    return decision;
  }

  private async presentForReview(item: QAReviewItem): Promise<ReviewDecision> {
    // This would integrate with the UI
    // Returns the agent's decision
    return {
      decision: 'approve', // or 'correct' or 'escalate'
      corrections: [],
      notes: ''
    };
  }
}
```

---

## 7. Field-Specific Patterns

### Destination Extraction Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DESTINATION EXTRACTION PATTERNS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COMMON PATTERNS (High Accuracy):                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pattern                      │ Example              │ Accuracy     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ "Trip to {dest}"              │ "Trip to Goa"        │ 98.2%       │   │
│  │ "Planning {dest} trip"        │ "Planning Kerala trip"│ 97.8%       │   │
│  │ "Visit {dest}"                 │ "Visit Thailand"     │ 96.5%       │   │
│  │ "{dest} in {month}"           │ "Goa in May"         │ 95.1%       │   │
│  │ "Going to {dest}"             │ "Going to Manali"     │ 94.3%       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHALLENGING PATTERNS (Lower Accuracy):                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pattern                      │ Example                │ Accuracy     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Multiple destinations        │ "Goa and Kerala"      │ 72.3%       │   │
│  │                            │ (Which is primary?)    │              │   │
│  │ Ambiguous reference          │ "Maybe visit Goa"     │ 58.1%       │   │
│  │ Implied destination          │ "Beach vacation"       │ 45.2%       │   │
│  │ Regional vs specific         │ "South India"           │ 38.7%       │   │
│  │ Nicknames/variants           │ "God's Own Country"    │ 82.1%       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IMPROVEMENT STRATEGIES:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Multiple destinations: Ask for clarification                      │   │
│  │ • Ambiguous: Flag as low confidence, request confirmation          │   │
│  │ • Regional: Map to popular destinations in region                   │   │
│  │ • Nicknames: Maintain nickname → destination mapping             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Date Extraction Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATE EXTRACTION PATTERNS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INDIAN DATE FORMATS (Common):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Format        │ Example          │ Notes                           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ DD.MM.YYYY    │ "15.05.2025"     │ Most common Indian format       │   │
│  │ DD-MM-YYYY    │ "15-05-2025"     │ Alternative                      │   │
│  │ DD/MM/YYYY    │ "15/05/2025"     │ Also used                       │   │
│  │ DD Month YYYY │ "15 May 2025"    │ Explicit                        │   │
│  │ Month DD, YYYY│ "May 15, 2025"   │ International format           │   │
│  │ YYYY-MM-DD    │ "2025-05-15"     │ ISO format                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IMPLIED DATE PATTERNS:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pattern                  │ Example            │ Inference          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ "{month} {day}"          │ "May 15"           │ Assume current year│   │
│  │ "{month} mid/early/late"│ "mid May"          │ Assume 15th of month│   │
│  │ "second week of {month}"  │ "second week May"   │ Assume 8th-14th     │   │
│  │ "{month} {year}"          │ "May 2025"         │ Date unspecified     │   │
│  │ "next {month}"            │ "next May"          │ May of next year    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ERROR PATTERNS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Error Type                   │ Frequency │ Fix                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Missing year                 │   234    │ Assume current year     │   │
│  │ Date format confusion        │   189    │ Try all formats          │   │
│  │ Start/end swapped            │    67    │ Validate start < end     │   │
│  │ Past dates (already passed)  │    23    │ Flag for confirmation    │   │
│  │ Holiday as date              │    12    │ Recognize holidays       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Budget Extraction Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BUDGET EXTRACTION PATTERNS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXPLICIT PATTERNS:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pattern                            │ Example           │ Accuracy   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ "Budget: {amount} {currency}"      │ "Budget: 80k INR" │ 97.8%     │   │
│  │ "{amount} budget"                 │ "80k budget"      │ 94.2%     │   │
│  │ "Maximum {amount}"                 │ "Maximum 1 lakh"   │ 91.5%     │   │
│  │ "Around {amount}"                  │ "Around 50k"      │ 78.3%     │   │
│  │ "{amount} per person"              │ "25k per person"  │ 93.1%     │   │
│  │ "Total budget {amount}"            │ "Total budget 2L"  │ 95.6%     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  IMPLIED PATTERNS (Lower confidence):                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Pattern                            │ Example           │ Accuracy   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ "Budget-friendly destination"       │ "Budget trip"     │ 45.2%     │   │
│  │ "Economical option"                 │ "Cheap option"    │ 42.1%     │   │
│  │ "Luxury experience"                 │ "Luxury trip"     │ 38.7%     │   │
│  │ "{amount} range"                    │ "50-60k range"    │ 89.3%     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CURRENCY DETECTION:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Currency Symbol │ Usage      │ Examples                │ Inference    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ ₹ / INR / Rs   │ Default    │ "₹80k", "80k INR"      │ INR          │   │
│  │ $ / USD         │ Explicit   │ "$2000 per person"      │ USD          │   │
│  │ "lakh" / "L"    │ Indian     │ "2 lakh", "2L"           │ INR (2,00,000)│   │
│  │ "k" / "K"       │ Contextual │ "80k"                  │ Based on dest │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Improvement Strategies

### Priority Improvement Areas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      IMPROVEMENT PRIORITY MATRIX                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Impact │        High Effort                                    │       │   │
│  ├────────┼─────────────────────────────────────────────────────────────┤   │
│  │ High   │ 1. Year detection (dates)                              │       │   │
│  │        │ 2. Multi-destination handling                        │       │   │
│  │        │ 3. Children detection                                  │       │   │
│  │        │ 4. Budget ambiguity resolution                       │       │   │
│  ├────────┼─────────────────────────────────────────────────────────────┤   │
│  │ Medium │ 5. Indian date format parser                          │       │   │
│  │        │ 6. Destination nickname mapping                       │       │   │
│  │        │ 7. Trip type inference                                │       │   │
│  ├────────┼─────────────────────────────────────────────────────────────┤   │
│  │ Low    │ 8. Preference extraction                             │       │   │
│  │        │ 9. Special requests parsing                           │       │   │
│  └────────┴─────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  QUICK WINS (High Impact, Low Effort):                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Add DD.MM.YYYY date pattern                                     │   │
│  │     Expected: -35% format errors, 1 day effort                     │   │
│  │                                                                     │   │
│  │ 2. Default current year when year missing                          │   │
│  │     Expected: -40% "missing year" errors, 2 hours effort            │   │
│  │                                                                     │   │
│  │ 3. Add "lakh" to number conversion                                 │   │
│  │     Expected: +25% budget accuracy for Indian format, 2 hours      │   │
│  │                                                                     │   │
│  │ 4. Validate start < end date                                      │   │
│  │     Expected: -60% swapped date errors, 4 hours effort               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A/B Testing Framework

```typescript
// A/B Testing for Extraction Improvements
interface ExtractionABTest {
  // Create test
  createTest(params: {
    name: string;
    description: string;
    field: string;
    control: ExtractionConfig;
    treatment: ExtractionConfig;
    sampleSize: number;
    minDuration: number; // days
  }): Promise<string>;

  // Record result
  recordResult(params: {
    testId: string;
    variant: 'control' | 'treatment';
    inquiryId: string;
    extractedValue: any;
    confidence: number;
  }): Promise<void>;

  // Record correction (ground truth)
  recordCorrection(params: {
    testId: string;
    inquiryId: string;
    correctValue: any;
  }): Promise<void>;

  // Get test results
  getResults(testId: string): Promise<ABTestResults>;

  // Complete test and choose winner
  completeTest(testId: string): Promise<TestConclusion>;
}

interface ABTestResults {
  testId: string;
  status: 'running' | 'completed';

  control: {
    samples: number;
    accuracy: number;
    avgConfidence: number;
    calibrationError: number;
  };

  treatment: {
    samples: number;
    accuracy: number;
    avgConfidence: number;
    calibrationError: number;
  };

  comparison: {
    accuracyDiff: number;            // treatment - control
    significance: number;            // p-value
    improvement: 'significant' | 'neutral' | 'regression';
  };

  recommendation: 'deploy_treatment' | 'continue_control' | 'inconclusive';
}

// Example A/B test
const dateExtractionTest = await abTest.createTest({
  name: 'indian-date-format-parser',
  description: 'Add DD.MM.YYYY pattern for Indian date format',
  field: 'dates',
  sampleSize: 1000,
  minDuration: 7,

  control: {
    dateFormats: ['YYYY-MM-DD', 'MM/DD/YYYY', 'DD Month YYYY']
  },

  treatment: {
    dateFormats: ['YYYY-MM-DD', 'MM/DD/YYYY', 'DD Month YYYY', 'DD.MM.YYYY']
  }
});

// After test completes
const results = await abTest.getResults(dateExtractionTest);
// {
//   control: { accuracy: 0.872 },
//   treatment: { accuracy: 0.918 },
//   comparison: {
//     accuracyDiff: 0.046,  // +4.6%
//     significance: 0.001,  // Highly significant
//     improvement: 'significant'
//   },
//   recommendation: 'deploy_treatment'
// }
```

---

## 9. Implementation Reference

### Quality Monitoring Dashboard

```typescript
// Quality Monitoring Dashboard API
interface QualityDashboard {
  // Get overall quality metrics
  getOverallQuality(period: DateRange): Promise<OverallQualityMetrics>;

  // Get field-level accuracy
  getFieldAccuracy(field: string, period: DateRange): Promise<FieldAccuracy>;

  // Get error breakdown
  getErrorBreakdown(period: DateRange): Promise<ErrorBreakdown>;

  // Get calibration metrics
  getCalibrationMetrics(field?: string): Promise<CalibrationMetrics>;

  // Get improvement suggestions
  getImprovementSuggestions(): Promise<ImprovementSuggestion[]>;
}

interface OverallQualityMetrics {
  period: DateRange;

  // Overall metrics
  overallAccuracy: number;
  overallCalibration: number;

  // Breakdown by field
  byField: Record<string, {
    accuracy: number;
    trend: 'improving' | 'stable' | 'declining';
    volume: number;
  }>;

  // Breakdown by confidence band
  byConfidenceBand: Record<string, {
    count: number;
    accuracy: number;
    wellCalibrated: boolean;
  }>;

  // Status indicators
  status: {
    overall: 'excellent' | 'good' | 'acceptable' | 'needs_improvement';
    alerts: QualityAlert[];
  };
}

// Monitoring service implementation
class QualityMonitoringService implements QualityDashboard {
  private accuracyStore: AccuracyStore;
  private calibrationService: CalibrationService;
  private alertService: AlertService;

  async getOverallQuality(period: DateRange): Promise<OverallQualityMetrics> {
    // Get accuracy metrics
    const accuracyByField = await this.accuracyStore.getByField(period);

    // Calculate overall accuracy (weighted by field importance)
    const overallAccuracy = this.calculateWeightedAccuracy(accuracyByField);

    // Get calibration metrics
    const calibrationMetrics = await this.calibrationService.getOverallMetrics(period);

    // Determine status
    const status = this.determineStatus(overallAccuracy, calibrationMetrics.ece);

    // Generate alerts if needed
    const alerts = await this.generateAlerts(accuracyByField, calibrationMetrics);

    return {
      period,
      overallAccuracy,
      overallCalibration: calibrationMetrics.ece,
      byField: this.mapFieldMetrics(accuracyByField),
      byConfidenceBand: await this.getByConfidenceBand(period),
      status: { overall: status, alerts }
    };
  }

  private determineStatus(accuracy: number, ece: number): QualityStatus {
    if (accuracy >= 0.90 && ece < 0.05) return 'excellent';
    if (accuracy >= 0.85 && ece < 0.08) return 'good';
    if (accuracy >= 0.80 && ece < 0.10) return 'acceptable';
    return 'needs_improvement';
  }

  private async generateAlerts(
    accuracyByField: Record<string, FieldAccuracy>,
    calibration: CalibrationMetrics
  ): Promise<QualityAlert[]> {
    const alerts: QualityAlert[] = [];

    // Check for field-level issues
    for (const [field, metrics] of Object.entries(accuracyByField)) {
      if (metrics.accuracy < 0.80) {
        alerts.push({
          severity: 'high',
          type: 'low_accuracy',
          field,
          message: `${field} accuracy below 80%: ${metrics.accuracy * 100}%`,
          action: 'Review extraction patterns for this field'
        });
      }

      if (metrics.trend === 'declining') {
        alerts.push({
          severity: 'medium',
          type: 'declining_trend',
          field,
          message: `${field} accuracy declining over time`,
          action: 'Investigate recent changes'
        });
      }
    }

    // Check calibration
    if (calibration.ece > 0.08) {
      alerts.push({
        severity: 'medium',
        type: 'poor_calibration',
        field: 'overall',
        message: `Confidence calibration poor: ECE = ${calibration.ece}`,
        action: 'Retrain calibration model'
      });
    }

    return alerts;
  }
}
```

### Real-Time Quality Feedback

```typescript
// Real-time quality feedback loop
class RealTimeQualityFeedback {
  async onExtractionComplete(result: ExtractionResult): Promise<void> {
    // Check quality indicators
    const qualityChecks = await this.performQualityChecks(result);

    // If quality issues detected, flag for review
    if (qualityChecks.requiresReview) {
      await this.flagForReview({
        inquiryId: result.inquiryId,
        reasons: qualityChecks.reasons,
        priority: this.calculatePriority(qualityChecks)
      });
    }

    // Log for monitoring
    await this.qualityMetrics.record({
      inquiryId: result.inquiryId,
      confidence: result.confidence.overall,
      perFieldConfidence: result.confidence.perField,
      fields: Object.keys(result.fields)
    });
  }

  async onCorrection(correction: AgentCorrection): Promise<void> {
    // Update quality metrics immediately
    await this.qualityMetrics.recordCorrection(correction);

    // Check if this indicates a systematic problem
    if (await this.isSystematicIssue(correction)) {
      await this.alertSystematicIssue(correction);
    }

    // Trigger learning if threshold reached
    const recentCorrections = await this.getRecentCorrections({
      field: correction.field,
      since: new Date(Date.now() - 24*60*60*1000)
    });

    if (recentCorrections.length > 50) {
      await this.triggerModelUpdate(correction.field);
    }
  }

  private async performQualityChecks(result: ExtractionResult): Promise<QualityChecks> {
    const checks: QualityChecks = {
      requiresReview: false,
      reasons: [],
      score: 100
    };

    // Check 1: Low overall confidence
    if (result.confidence.overall < 0.6) {
      checks.requiresReview = true;
      checks.reasons.push('low_overall_confidence');
      checks.score -= 30;
    }

    // Check 2: Low confidence on critical field
    const criticalFields = ['destination', 'startDate', 'endDate', 'travelersAdults'];
    for (const field of criticalFields) {
      const fieldConf = result.confidence.perField[field];
      if (fieldConf && fieldConf.score < 0.7) {
        checks.requiresReview = true;
        checks.reasons.push(`low_confidence_${field}`);
        checks.score -= 15;
      }
    }

    // Check 3: Confidence mismatch
    if (result.confidence.sourceAgreement < 0.5) {
      checks.requiresReview = true;
      checks.reasons.push('source_disagreement');
      checks.score -= 20;
    }

    // Check 4: Missing critical field
    for (const field of criticalFields) {
      if (!result.fields[field] || result.fields[field] === null) {
        checks.requiresReview = true;
        checks.reasons.push(`missing_${field}`);
        checks.score -= 25;
      }
    }

    return checks;
  }
}
```

---

## Summary

Extraction quality is maintained through:

1. **Quality Framework**: 4-tier pyramid (Perfection → Excellence → Acceptable → Unacceptable)
2. **Accuracy Metrics**: Field-level tracking, confidence band analysis, real-time monitoring
3. **Error Analysis**: 4-category taxonomy (Missed, Incorrect, False Positive, Format)
4. **Confidence Calibration**: Platt Scaling, reliability diagrams, ECE monitoring
5. **Continuous Learning**: Pipeline from corrections → patterns → model updates
6. **Quality Assurance**: Human review queue, automatic triggers, A/B testing
7. **Field-Specific Patterns**: Destination, date, budget extraction patterns
8. **Improvement Strategies**: Priority matrix, quick wins, systematic improvements

**Target Metrics**:
- Overall accuracy: >90%
- Critical field accuracy: >95%
- Confidence calibration: ECE < 0.05
- Error rate: <8%

---

**Next Document:** INTAKE_05_TRIAGE_STRATEGIES_DEEP_DIVE.md — Routing, prioritization, and agent assignment strategies