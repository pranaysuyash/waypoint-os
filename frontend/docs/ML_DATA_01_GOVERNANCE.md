# ML Training Data & Privacy Engineering — Data Governance & Training Pipeline

> Research document for ML training data governance, customer data usage for model training, synthetic data generation, anonymization techniques, differential privacy, federated learning, and model privacy evaluation for the Waypoint OS platform.

---

## Key Questions

1. **How can we legally use customer data to train ML models?**
2. **What anonymization and synthetic data techniques protect privacy while preserving utility?**
3. **What is differential privacy and how does it apply to travel platform models?**
4. **How do we evaluate models for privacy leakage?**

---

## Research Areas

### Training Data Governance Framework

```typescript
interface TrainingDataGovernance {
  // Legal and ethical framework for using customer data in ML
  data_sources: {
    CUSTOMER_CONVERSATIONS: {
      source: "WhatsApp messages, emails, call transcripts with customers";
      pii_density: "HIGH — names, phone numbers, destinations, dates, family details";
      legal_basis: "Explicit consent required under DPDP Act for ML training use";
      consent_language: "We may use anonymized travel data to improve our recommendation engine";
      usage: "Train NLP models for intent detection, entity extraction, response generation";
      retention: "Anonymized data retained indefinitely; original PII purged per retention policy";
    };

    BOOKING_DATA: {
      source: "Trip bookings, itineraries, pricing, supplier selections";
      pii_density: "MEDIUM — destinations, dates, budgets, group size (linkable to person)";
      legal_basis: "Legitimate interest for service improvement (with opt-out)";
      usage: "Train recommendation models, pricing optimization, demand forecasting";
      anonymization: "Remove direct identifiers; aggregate for statistical models";
    };

    AGENT_BEHAVIOR: {
      source: "Agent actions, response times, proposal creation, booking outcomes";
      pii_density: "LOW — agent performance data (internal, not customer PII)";
      legal_basis: "Employment contract + business purpose";
      usage: "Train agent assist models, workflow optimization, quality scoring";
      note: "Agent data is internal and less restricted, but still needs access controls";
    };

    WEBSITE_INTERACTION: {
      source: "Page visits, search queries, form interactions, click patterns";
      pii_density: "LOW-MEDIUM — search queries may contain destination preferences";
      legal_basis: "Cookie consent + privacy policy";
      usage: "Train personalization models, search relevance, conversion prediction";
      anonymization: "Session-level aggregation, no individual tracking for ML";
    };
  };

  // Consent and data pipeline
  consent_pipeline: {
    CONSENT_COLLECTION: {
      timing: "At account creation or first booking";
      format: "Clear, granular opt-in for 'improving our services with your data'";
      granularity: {
        analytics_only: "Aggregate statistics — lowest sensitivity";
        model_training: "Anonymized data for ML model training";
        personalization: "Individual-level data for personalized recommendations";
      };
      withdrawal: "One-click withdrawal via WhatsApp or settings; stops future use immediately";
    };

    DATA_PREPARATION_STEPS: {
      step_1_consent_check: "Verify customer has opted into ML training use";
      step_2_pii_extraction: "Run PII detection engine to identify all PII in data";
      step_3_anonymization: "Replace PII with synthetic equivalents or aggregate";
      step_4_quality_check: "Verify anonymized data has k-anonymity >= 5";
      step_5_training_dataset: "Export to isolated training environment (no production access)";
      step_6_audit_log: "Log which data was used, anonymization method, consent reference";
    };
  };
}

// ── Training data governance dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  ML Training Data — Governance Overview                   │
// │                                                       │
// │  Data inventory for ML training:                      │
// │  Source                │ Records  │ Consent │ Status   │
// │  ─────────────────────────────────────────────────────── │
// │  Customer conversations│ 45,200  │ 72% ✅  │ Ready    │
// │  Booking data          │ 12,800  │ 89% ✅  │ Ready    │
// │  Agent behavior        │  8,400  │ N/A     │ Ready    │
// │  Website interaction   │ 62,100  │ 45% ⚠️  │ Partial  │
// │                                                       │
// │  Anonymization pipeline:                              │
// │  Pending: 8,200 records                                  │
// │  In progress: 2,400 records (NER + PII scrub)           │
// │  Completed: 18,600 records ✅                            │
// │  Failed QC: 340 records (insufficient k-anonymity)      │
// │                                                       │
// │  Training datasets:                                   │
// │  DS-001: Intent detection v3 · 22K samples · Freshness: 2d │
// │  DS-002: Entity extraction v2 · 15K samples · Freshness: 7d │
// │  DS-003: Price prediction v1 · 10K samples · Freshness: 14d│
// │  DS-004: Recommendation v2 · 8K samples · Freshness: 5d  │
// │                                                       │
// │  [Create Dataset] [Run Pipeline] [Consent Report]         │
// └─────────────────────────────────────────────────────┘
```

### Anonymization & Synthetic Data

```typescript
interface AnonymizationAndSyntheticData {
  // Techniques for privacy-preserving data usage
  anonymization_techniques: {
    K_ANONYMITY: {
      description: "Every record is indistinguishable from at least k-1 other records";
      method: "Generalize quasi-identifiers (age range instead of DOB, city instead of address)";
      target: "k >= 5 for travel data (each combination appears at least 5 times)";
      limitation: "Doesn't protect against attribute inference if all k records share a sensitive value";
    };

    L_DIVERSITY: {
      description: "Each k-anonymous group has at least l distinct values for sensitive attributes";
      method: "Ensure destination diversity within each anonymization group";
      example: "If 5 customers share same age range + city, ensure they don't all book the same destination";
    };

    PSEUDONYMIZATION: {
      description: "Replace identifiers with consistent pseudonyms (reversible with key)";
      method: "HMAC-SHA256(customer_id + salt) → pseudonym";
      advantage: "Enables longitudinal analysis (track same customer over time) without real identity";
      key_management: "Pseudonym-to-real mapping stored separately with Tier 4 encryption";
    };

    DATA_MASKING: {
      description: "Replace real values with formatted fake values";
      examples: {
        names: "Rahul Sharma → Test User 42 (or realistic fake: Rajesh Kumar)";
        phones: "9876543210 → 98XXXXX210 (partial mask) or 9812345678 (fake)";
        emails: "rahul@gmail.com → test.user@example.com";
        destinations: "Keep real (not PII) — Singapore stays Singapore";
      };
      use_case: "Development/testing environments, demo data, documentation screenshots";
    };
  };

  synthetic_data_generation: {
    description: "Generate realistic but entirely fake data that preserves statistical properties";

    approaches: {
      STATISTICAL_SYNTHESIS: {
        method: "Learn joint distribution of fields → sample from learned distribution";
        tools: ["SDV (Synthetic Data Vault)", "Gretel.ai", " Mostly AI"];
        quality: "Preserves aggregate statistics (means, correlations, distributions)";
        privacy: "No real data in output — every record is synthetic";
        limitation: "Edge cases and rare patterns may not be well-represented";
      };

      LLM_BASED_SYNTHESIS: {
        method: "Use LLM to generate realistic travel conversations, itineraries, booking scenarios";
        advantage: "Produces naturalistic text with proper travel terminology";
        prompt_example: "Generate a realistic WhatsApp conversation between a travel agent and a customer planning a family trip to Singapore. Include budget discussion, date preferences, and hotel requirements.";
        quality_check: "Verify generated text doesn't inadvertently contain real PII from training data";
      };

      TRAVEL_DATA_TEMPLATES: {
        method: "Template-based generation with random parameterization";
        templates: {
          customer_profile: "Name: {INDIAN_NAME}, Phone: {FAKE_PHONE}, Budget: {RANDOM_RANGE}, Destination: {POPULAR_DEST}, Travelers: {RANDOM_2_TO_6}";
          whatsapp_conversation: "Agent: {GREETING} {CUSTOMER_NAME}, how can I help? / Customer: We want to visit {DEST} in {MONTH}...";
          booking_record: "{DEST} package, {NIGHTS} nights, {TRAVELERS} pax, ₹{PRICE}, {HOTEL_STAR}★ hotel, {STATUS}";
        };
        advantage: "Fully controlled, no privacy risk, deterministic when needed";
      };
    };

    use_cases: {
      development: "Developers work with synthetic data — zero real PII in dev environments";
      testing: "Automated tests run against synthetic data — no consent needed";
      demos: "Sales demos use realistic but fake customer data";
      training: "New agents learn on synthetic scenarios before real customers";
      model_training: "Supplement real anonymized data with synthetic data to increase volume";
    };
  };
}

// ── Synthetic data generator ──
// ┌─────────────────────────────────────────────────────┐
// │  Synthetic Data — Travel Scenario Generator               │
// │                                                       │
// │  Generate:                                            │
// │  [✓] Customer profiles · 500 records                     │
// │  [✓] WhatsApp conversations · 200 scenarios               │
// │  [✓] Booking records · 300 records                        │
// │  [ ] Agent-customer email threads · 100                   │
// │                                                       │
// │  Parameters:                                          │
// │  Destinations: [All popular ▾] or [Singapore, Bali, Dubai]│
// │  Customer type: [All ▾] or [Family, Couple, Solo, Group]  │
// │  Budget range: [₹30K - ₹5L]                               │
// │  Realism level: [High] (preserves real distributions)      │
// │                                                       │
// │  Privacy guarantees:                                  │
// │  ✅ Zero real PII (all names, phones, emails synthetic)   │
// │  ✅ Statistical properties preserved (destination mix,     │
// │     budget distribution, group size distribution)          │
// │  ✅ No linkable records (synthetic identities are unique)  │
// │  ✅ Passed privacy evaluation (ε < 1.0 differential privacy)│
// │                                                       │
// │  [Generate] [Export] [Quality Report]                      │
// └─────────────────────────────────────────────────────┘
```

### Differential Privacy & Federated Learning

```typescript
interface DifferentialPrivacyAndFederated {
  // Advanced privacy-preserving ML techniques
  differential_privacy: {
    concept: {
      description: "Mathematical guarantee that model output doesn't reveal whether any individual's data was in the training set";
      epsilon: "Privacy budget (ε) — lower = more private but less accurate";
      target_epsilon: "ε < 1.0 for strong privacy; ε < 10 for practical privacy";
      tradeoff: "Lower ε → more noise → less model accuracy → need more training data";
    };

    implementation: {
      DP_SGD: {
        description: "Differentially Private Stochastic Gradient Descent";
        mechanism: "Clip gradients + add calibrated noise during training";
        frameworks: ["Opacus (PyTorch)", "TensorFlow Privacy"];
        impact: "2-5% accuracy reduction at ε=1.0; <1% at ε=10";
        use_case: "Training recommendation models on customer booking data";
      };

      DP_QUERY: {
        description: "Differentially private database queries for analytics";
        mechanism: "Add Laplace or Gaussian noise to query results";
        use_case: "Aggregate analytics (e.g., 'average Singapore trip cost') without revealing individual bookings";
      };
    };

    practical_application: {
      recommendation_model: "Train with DP-SGD at ε=3.0 → 97% utility with strong privacy guarantee";
      analytics_dashboard: "All aggregate queries through DP layer → no individual inference possible";
      trend_reports: "Destination trend data with DP → accurate trends without individual tracking";
    };
  };

  federated_learning: {
    concept: {
      description: "Train models across multiple agencies without sharing raw data";
      approach: "Each agency trains local model → shares only model updates (gradients) → server aggregates";
      privacy_benefit: "Customer data never leaves the agency's infrastructure";
    };

    architecture: {
      FEDERATED_AVERAGE: {
        step_1: "Server sends base model to each participating agency";
        step_2: "Each agency trains on its own data for N epochs";
        step_3: "Agencies send model weight updates (not data) to server";
        step_4: "Server averages weight updates across agencies";
        step_5: "Repeat until model converges";
      };

      SECURE_AGGREGATION: {
        description: "Even model updates are encrypted so server can't see individual agency's contribution";
        method: "Additive secret sharing — server sees only the sum of all updates";
        benefit: "Server learns the aggregated model but nothing about any single agency's data";
      };
    };

    use_cases: {
      cross_agency_recommendation: "Better destination recommendations trained across 50 agencies' data without any agency seeing another's customers";
      fraud_detection: "Fraud patterns detected across agencies — one agency's fraud informs others without sharing customer details";
      pricing_intelligence: "Market pricing models trained on aggregated data from multiple agencies";
    };

    challenges: {
      communication_cost: "Model updates are large (MB to GB); need efficient compression";
      heterogeneity: "Agencies have different data distributions (some specialize in honeymoon, others in corporate)";
      incentives: "Why should agencies share model updates? Need mutual benefit framework";
      coordination: "Who runs the aggregation server? Platform provider or neutral third party?";
    };
  };
}

// ── Privacy-preserving ML dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Privacy-Preserving ML — Model Registry                   │
// │                                                       │
// │  Active Models:                                       │
// │  ┌──────────────────────────────────────────────────┐ │
// │  │ Destination Recommender v3                          │ │
// │  │ Training: 22K anonymized bookings + 8K synthetic    │ │
// │  │ Privacy: DP-SGD ε=3.0 ✅ · k-anon ≥ 5 ✅            │ │
// │  │ Accuracy: 87% (vs. 89% without DP — acceptable)    │ │
// │  │ Last trained: Apr 28, 2026                          │ │
// │  │ Privacy audit: Passed (no individual leakage) ✅     │ │
// │  └──────────────────────────────────────────────────┘ │
// │  ┌──────────────────────────────────────────────────┐ │
// │  │ Price Optimizer v2                                  │ │
// │  │ Training: 12K anonymized bookings                   │ │
// │  │ Privacy: Aggregate only (no individual data) ✅     │ │
// │  │ Accuracy: 94% margin prediction                     │ │
// │  │ Last trained: Apr 25, 2026                          │ │
// │  └──────────────────────────────────────────────────┘ │
// │                                                       │
// │  Privacy Budget Usage (this quarter):                 │
// │  Total ε allocated: 10.0                               │
// │  ε used: 4.2 (recommender) + 1.8 (pricing) = 6.0      │
// │  ε remaining: 4.0 (enough for 1 more training cycle)   │
// │  [Manage Budget] [Request Increase]                       │
// │                                                       │
// │  [Train New Model] [Privacy Audit] [Export Report]        │
// └─────────────────────────────────────────────────────┘
```

### Model Privacy Evaluation

```typescript
interface ModelPrivacyEvaluation {
  // Testing models for privacy leakage
  attack_types: {
    MEMBERSHIP_INFERENCE: {
      description: "Attacker determines if a specific individual's data was in the training set";
      test: "Train shadow models → query target model → distinguish member from non-member";
      acceptable_rate: "Attack accuracy < 55% (barely better than random guessing)";
      mitigation: "Differential privacy, regularization, reduce model overfitting";
    };

    ATTRIBUTE_INFERENCE: {
      description: "Attacker infers sensitive attributes from non-sensitive inputs";
      example: "Given destination and budget (non-sensitive), infer income level (sensitive)";
      test: "Train attack model to predict sensitive attribute from model outputs";
      mitigation: "Limit model outputs, add noise to predictions, reduce feature correlation";
    };

    MODEL_EXTRACTION: {
      description: "Attacker reconstructs training data by querying the model repeatedly";
      test: "Generate diverse inputs → collect outputs → train surrogate model → compare";
      mitigation: "Rate limiting on model API, output perturbation, differential privacy";
    };

    DATA_POISONING: {
      description: "Malicious data injected into training set to manipulate model behavior";
      example: "Fake booking data to bias pricing model toward certain suppliers";
      mitigation: "Training data validation, anomaly detection, provenance tracking";
    };
  };

  evaluation_framework: {
    PRE_TRAINING: {
      data_audit: "Verify all training data has consent and is properly anonymized";
      k_anonymity_check: "Ensure k >= 5 for all quasi-identifier groups";
      bias_check: "Test for demographic bias in training data distribution";
    };

    POST_TRAINING: {
      membership_inference_test: "Run membership inference attack; accuracy must be < 55%";
      attribute_inference_test: "Test for sensitive attribute leakage; AUC must be < 0.6";
      model_extraction_resistance: "Measure how many queries needed to extract useful data";
      utility_test: "Verify model accuracy hasn't degraded below acceptable threshold";
    };

    ONGOING: {
      continuous_monitoring: "Monitor model outputs for unexpected patterns suggesting leakage";
      retraining_audits: "Privacy evaluation on every model retraining cycle";
      incident_response: "If privacy breach detected → revoke model, investigate, notify";
    };
  };
}
```

---

## Open Problems

1. **Consent granularity** — Asking customers to consent to "ML training" is vague. But asking for consent per model type (recommendations, pricing, fraud) creates consent fatigue. Need a balanced approach.

2. **Synthetic data fidelity** — Synthetic travel data must preserve the statistical properties that make it useful for training (destination correlations with budget, seasonal patterns) while being clearly fake. Getting this balance right is non-trivial.

3. **Federated learning incentives** — Why would competing travel agencies share model updates? The benefit (better models) is collective, but the cost (compute, bandwidth, potential competitive insight leakage) is individual.

4. **Privacy budget management** — Differential privacy has a finite budget (ε). Every query and training cycle consumes budget. Once exhausted, no more queries are possible without resetting. Need careful budget planning across the quarter.

---

## Next Steps

- [ ] Build training data governance pipeline with consent verification
- [ ] Implement synthetic data generator for travel scenarios
- [ ] Integrate differential privacy (DP-SGD) into model training pipeline
- [ ] Design model privacy evaluation framework with automated testing
- [ ] Create privacy-preserving analytics layer for aggregate reporting
