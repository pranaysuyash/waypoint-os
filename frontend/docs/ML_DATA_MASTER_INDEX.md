# ML Training Data & Privacy Engineering — Master Index

> Research on training data governance, anonymization techniques, synthetic data generation, differential privacy, federated learning, and model privacy evaluation for the Waypoint OS platform.

---

## Series Overview

This series covers the intersection of machine learning and privacy — from legally using customer data for model training (with proper consent and anonymization) to advanced techniques like differential privacy, federated learning across agencies, synthetic data generation, and model privacy evaluation. Travel platforms sit on rich behavioral data (booking patterns, destination preferences, price sensitivity) that can power better models, but only if used responsibly.

**Target Audience:** ML engineers, data scientists, privacy engineers, legal/compliance teams

**Key Insight:** Most travel platforms either (a) don't use customer data for ML at all (wasting a valuable asset) or (b) use it without proper governance (creating legal risk). The middle path is a structured pipeline: consent verification → PII removal → anonymization (k-anonymity ≥ 5) → synthetic data augmentation → differentially-private training → model privacy evaluation. This produces useful models while maintaining provable privacy guarantees.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [ML_DATA_01_GOVERNANCE.md](ML_DATA_01_GOVERNANCE.md) | Training data sources and legal basis, consent pipeline, anonymization techniques (k-anonymity, pseudonymization, data masking), synthetic data generation (statistical, LLM-based, template), differential privacy (DP-SGD), federated learning across agencies, model privacy evaluation (membership inference, attribute inference, model extraction) |

---

## Key Themes

### 1. Consent Is the Foundation
No customer data enters the ML pipeline without explicit, granular consent. The consent pipeline isn't a checkbox — it's the first step in every training data preparation workflow. Consent withdrawal immediately removes data from all future training.

### 2. Synthetic Over Real
For development, testing, demos, and supplementing training data, synthetic data is preferable to anonymized real data. It carries zero privacy risk and can be generated in unlimited quantities with controlled properties.

### 3. Differential Privacy as a Guarantee
Differential privacy provides mathematical guarantees that no individual's data can be inferred from model outputs. At ε=3.0, recommendation models lose only 2% accuracy while gaining provable privacy — an acceptable tradeoff.

### 4. Federated Learning for Collective Intelligence
50 travel agencies training models on their combined data (without sharing any data) produces better models than any single agency could. Federated learning enables this while keeping customer data within each agency's boundaries.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| PII Detection (PII_DETECT_*) | PII detection feeds anonymization pipeline |
| Privacy & Consent (PRIVACY_*) | Consent management for ML training use |
| AI/ML Patterns (AIML_*) | ML model architecture and governance |
| Data Governance (DATA_GOVERNANCE_*) | Data quality and lineage for training data |
| Recommendations Engine (RECOMMENDATIONS_ENGINE_*) | Models trained with privacy-preserving techniques |
| Pricing Engine (PRICING_ENGINE_*) | Pricing models using anonymized booking data |
| Security Architecture (SECURITY_*) | Encryption and access control for training data |

---

**Created:** 2026-04-30
