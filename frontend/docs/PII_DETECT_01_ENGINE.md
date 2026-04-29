# PII Detection & Data Classification — Detection Engine

> Research document for automated PII detection, named entity recognition, ML-based PII classification, real-time data classification, and domain-specific document processing for the Waypoint OS platform.

---

## Key Questions

1. **How do we automatically detect PII in customer communications and documents?**
2. **What ML models and techniques identify personally identifiable information?**
3. **How do we classify data by sensitivity tier at ingestion?**
4. **How do domain-specific vision models (MedGemma-class) apply to travel document processing?**

---

## Research Areas

### PII Detection Architecture

```typescript
interface PIIDetectionEngine {
  // Multi-layer PII detection pipeline
  detection_layers: {
    LAYER_1_REGEX_PATTERNS: {
      description: "Pattern-matching for structured PII formats";
      detects: {
        PHONE_INDIA: {
          pattern: "/[+91[-\\s]?|0)?[6-9]\\d{9}/";
          confidence: "95% (low false positive for Indian mobile numbers)";
          examples: "+91 98765 43210, 9876543210";
        };

        PHONE_INTL: {
          pattern: "/\\+?[1-9]\\d{1,14}/";
          confidence: "85% (broader, more false positives)";
        };

        EMAIL: {
          pattern: "/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/";
          confidence: "98% (very reliable)";
        };

        PASSPORT_NUMBER: {
          pattern_indian: "/[A-Z][1-9]\\d\\s?\\d{4}[1-9]/";
          confidence: "90% (Indian passport format)";
        };

        AADHAAR_NUMBER: {
          pattern: "/\\b[2-9]\\d{3}\\s?\\d{4}\\s?\\d{4}\\b/";
          confidence: "88%";
          sensitivity: "CRITICAL — Aadhaar requires highest protection under DPDP Act";
        };

        PAN_NUMBER: {
          pattern: "/[A-Z]{5}[0-9]{4}[A-Z]/";
          confidence: "92%";
        };

        CREDIT_CARD: {
          pattern: "/\\b(?:\\d[ -]*?){13,19}\\b/ + Luhn check";
          confidence: "95% with Luhn validation";
        };

        DATE_OF_BIRTH: {
          pattern: "/\\b\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}\\b/";
          confidence: "70% (many false positives — dates are common in travel context)";
          context_required: "Must distinguish DOB from travel dates";
        };

        ADDRESS: {
          approach: "Multi-field heuristic, not single regex";
          signals: "Pin code + city name + street number pattern";
          confidence: "75%";
        };

        BANK_ACCOUNT: {
          pattern: "/\\b\\d{9,18}\\b/ with IFSC code proximity";
          confidence: "80% (requires context — travel itineraries have many numbers)";
        };
      };

      performance: "<1ms per field, suitable for real-time ingestion pipeline";
    };

    LAYER_2_NER_MODEL: {
      description: "Named Entity Recognition model for contextual PII detection";
      model_options: {
        SPACY_CUSTOM: {
          base: "spaCy en_core_web_lg + custom travel-domain NER";
          entities: ["PERSON", "PHONE", "EMAIL", "GPE", "LOC", "DATE", "MONEY", "PASSPORT", "AADHAAR"];
          training_data: "10K+ annotated travel conversations";
          accuracy: "92% F1 on travel-specific PII";
          latency: "20-50ms per message";
          cost: "Free (self-hosted)";
        };

        TRANSFORMER_BASED: {
          base: "Fine-tuned BERT/DistilBERT for PII NER";
          entities: "Same as above with better context understanding";
          accuracy: "96% F1 on travel-specific PII";
          latency: "100-300ms per message";
          cost: "Free (self-hosted GPU needed for training)";
        };

        API_BASED: {
          options: ["AWS Comprehend PII", "Google DLP API", "Microsoft Presidio"];
          accuracy: "90-95% F1 on general PII";
          latency: "200-500ms per message";
          cost: "₹1-3 per 100 records";
          limitation: "Less accurate on Indian-specific PII (Aadhaar, PAN, Indian addresses)";
        };

        PRESIDIO_OPEN_SOURCE: {
          description: "Microsoft Presidio — open-source PII anonymization";
          components: "PII recognizer engine + anonymizer engine";
          recognizers: "Built-in (email, phone, credit card) + custom (Aadhaar, PAN, Indian names)";
          advantage: "Self-hosted, extensible, no API costs";
          limitation: "Custom recognizers needed for Indian PII types";
        };
      };
    };

    LAYER_3_CONTEXT_ENGINE: {
      description: "Context-aware classification to reduce false positives";
      rules: {
        TRAVEL_DATE_VS_DOB: "If date appears near 'departure' or 'check-in' → travel date, not DOB";
        PRICE_VS_ACCOUNT: "If number appears near '₹' or 'per person' → price, not account number";
        DESTINATION_VS_ADDRESS: "If location appears in 'destination' field → travel destination, not home address";
        TRAVELER_NAME_VS_AGENT: "If name appears in 'customer' field → PII; in 'agent' field → internal data";
      };
      benefit: "Reduces false positives by 40-60% in travel-specific context";
    };
  };
}

// ── PII detection pipeline ──
// ┌─────────────────────────────────────────────────────┐
// │  PII Detection — Real-Time Scan                           │
// │                                                       │
// │  Input: WhatsApp message from customer               │
// │  "Hi, I'm Rahul Sharma, my number is 9876543210.      │
// │   Our group of 4 wants to go to Singapore.              │
// │   My wife Priya's passport is J8365471.                  │
// │   We'll pay by credit card 4111 1111 1111 1111"          │
// │                                                       │
// │  Detection Results:                                   │
// │  🔴 CRITICAL: Credit card number detected               │
// │     4111 1111 1111 1111 → [REDACTED]                    │
// │  🔴 CRITICAL: Passport number detected                   │
// │     J8365471 → [REDACTED]                                │
// │  🟡 HIGH: Indian mobile number detected                  │
// │     9876543210 → Store encrypted, display masked         │
// │  🟢 STANDARD: Personal name detected                     │
// │     Rahul Sharma, Priya → Store encrypted                 │
// │                                                       │
// │  Auto-actions:                                        │
// │  ✅ Credit card redacted from logs and display           │
// │  ✅ Passport number encrypted before storage              │
// │  ✅ Phone number encrypted, masked in UI (98***3210)     │
// │  ✅ Names stored encrypted, decrypted only for agent view │
// │                                                       │
// │  [Override] [View Full] [Report False Positive]          │
// └─────────────────────────────────────────────────────┘
```

### Data Classification Tiers

```typescript
interface DataClassificationTiers {
  // Sensitivity-based classification for all platform data
  tiers: {
    TIER_0_PUBLIC: {
      description: "Publicly available information, no protection needed";
      examples: ["Destination names", "Country information", "Currency rates", "Weather data"];
      storage: "Plain text, any medium";
      access: "No restrictions";
      retention: "Indefinite";
    };

    TIER_1_INTERNAL: {
      description: "Internal business data, not customer-specific";
      examples: ["Package templates", "Supplier rate sheets (non-contract)", "Destination guides", "Agent training materials"];
      storage: "Plain text, internal systems only";
      access: "Authenticated users only";
      retention: "Until superseded";
    };

    TIER_2_CONFIDENTIAL: {
      description: "Customer-related data that identifies preferences but not identity";
      examples: ["Trip preferences", "Destination interests", "Budget ranges (non-specific)", "Travel dates"];
      storage: "Encrypted at rest, access-logged";
      access: "Assigned agent + supervisor";
      retention: "3 years after last interaction";
      masking: "Partial masking in non-essential views";
    };

    TIER_3_SENSITIVE: {
      description: "Directly identifies or contacts a person";
      examples: ["Full name", "Phone number", "Email address", "Physical address", "Date of birth"];
      storage: "AES-256 encrypted, field-level encryption";
      access: "Assigned agent only, decryption logged";
      retention: "Active relationship + 1 year";
      masking: "Full masking by default (e.g., R**** S****, 98***3210)";
      dpdp_classification: "Personal Data";
    };

    TIER_4_HIGHLY_SENSITIVE: {
      description: "Government IDs, financial instruments, health data";
      examples: ["Passport number", "Aadhaar number", "PAN number", "Credit card number", "Bank account", "Health conditions", "Disability information"];
      storage: "AES-256 encrypted, key vault, never logged in plain text";
      access: "Agent view only, never exported, no API access in plain text";
      retention: "Trip duration + 30 days post-trip, then purged";
      masking: "Always masked except during booking process";
      dpdp_classification: "Sensitive Personal Data";
      legal_basis: "Explicit consent required under DPDP Act Section 7";
    };
  };

  // Automatic classification rules
  auto_classification: {
    AT_INGESTION: "Every data field classified at point of entry (WhatsApp, form, document)";
    FIELD_MAPPING: "Known fields auto-classified (phone field → Tier 3, passport field → Tier 4)";
    CONTENT_SCAN: "Free-text fields scanned by PII detection engine before classification";
    ESCALATION: "If detection confidence < 80%, flag for manual review (default to higher tier)";
    AUDIT_TRAIL: "Every classification decision logged with confidence score and model version";
  };
}

// ── Data classification dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Data Classification — System Overview                    │
// │                                                       │
// │  Classification Distribution:                         │
// │  Tier 0 (Public):       12,400 records · No protection  │
// │  Tier 1 (Internal):      8,200 records · Access control  │
// │  Tier 2 (Confidential): 15,600 records · Encrypted       │
// │  Tier 3 (Sensitive):     9,800 records · Field-encrypted │
// │  Tier 4 (Critical):      2,100 records · Vault + purge   │
// │                                                       │
// │  Recent detections (last 24h):                        │
// │  🔍 847 fields scanned → 312 PII detected                │
// │  🟢 Auto-classified: 298 (95.5%)                          │
// │  🟡 Low confidence → manual review: 11 (3.5%)            │
// │  🔴 Failed classification: 3 (0.9%) — escalated          │
// │                                                       │
// │  Encryption compliance:                               │
// │  ✅ All Tier 3+ fields encrypted at rest                 │
// │  ✅ All Tier 4 fields in key vault                       │
// │  ✅ Zero plain-text PII in logs (last 30 days)           │
// │  ⚠️ 12 Tier 4 records approaching retention expiry       │
// │                                                       │
// │  [Scan Now] [Compliance Report] [Purge Schedule]         │
// └─────────────────────────────────────────────────────┘
```

### Domain-Specific Vision Models (MedGemma-Class)

```typescript
interface DomainVisionModels {
  // Specialized vision models for travel document processing
  model_categories: {
    DOCUMENT_UNDERSTANDING: {
      description: "Extract structured data from travel documents (passports, visas, tickets, hotel confirmations)";
      model_architectures: {
        LAYOUT_LM: {
          description: "Document AI model that understands layout + text";
          variants: ["LayoutLMv3", "Donut", "Nougat"];
          capability: "Extract fields from structured documents (passports, tickets)";
          accuracy: "95%+ on passport extraction, 90%+ on hotel confirmations";
          fine_tuning: "Fine-tune on Indian passport + visa templates";
        };

        VISION_TRANSFORMER: {
          description: "General vision model adapted for document understanding";
          examples: ["CLIP + OCR pipeline", "Florence-2", "MedGemma-style domain adaptation"];
          medgemma_parallel: {
            concept: "MedGemma adapts Gemma for medical imaging; similarly, we adapt vision models for travel document understanding";
            domain_data: "Travel documents (passports, visas, tickets, boarding passes, hotel vouchers, insurance certificates)";
            training_approach: "Base vision model + travel document fine-tuning + OCR correction layer";
            outputs: "Structured JSON with field-level confidence scores";
          };
        };

        MULTIMODAL_LLM: {
          description: "LLM with vision capabilities for document understanding";
          examples: ["GPT-4V / Claude Vision / Gemini Pro Vision for document parsing"];
          advantage: "Handles unstructured, damaged, or non-standard documents";
          approach: "Send document image → Model extracts fields → Validate against known patterns";
          cost: "₹0.5-2 per document";
          use_case: "Complex documents where structured extraction fails";
        };
      };
    };

    DOCUMENT_VERIFICATION: {
      description: "Detect forged or altered travel documents";
      techniques: {
        TAMPER_DETECTION: {
          description: "Detect photo substitution, text alteration, or document manipulation";
          signals: ["Inconsistent font rendering", "Pixel-level tampering artifacts", "Metadata mismatches", "Hologram absence"];
          accuracy: "85-90% on known forgery patterns";
        };

        AUTHENTICITY_SCORING: {
          description: "Score document authenticity 0-100";
          factors: ["MRZ checksum validation", "Photo-document consistency", "Template matching against known valid formats", "Security feature detection"];
          threshold: "< 70 → flag for manual review; < 40 → likely fraudulent";
        };
      };
    };

    OPPOSITE_USAGE__REDACTION: {
      description: "Use vision models to REDACT PII from documents rather than extract it";
      use_cases: {
        STATEMENT_REDACTION: "Remove PII from bank statements before sharing with suppliers";
        DOCUMENT_SANITIZATION: "Strip PII from documents used for training or testing";
        COMPLIANCE_EXPORT: "Produce PII-free exports for regulatory reporting";
        DEMO_DATA: "Generate realistic but PII-free demo data from real documents";
      };

      approach: {
        step_1: "Vision model identifies all PII-containing regions in document image";
        step_2: "Replace identified regions with realistic but fake data (not just black bars)";
        step_3: "Maintain document structure and formatting for realism";
        step_4: "Output sanitized document that looks real but contains zero real PII";
      };

      advantage_over_black_bars: "Sanitized documents can be used for demos, training, and screenshots without looking obviously redacted";
    };
  };
}
```

---

## Open Problems

1. **Travel context false positives** — Travel conversations are full of dates (departure, return, check-in), numbers (prices, confirmation codes), and names (hotels, airlines, destinations). Standard PII detectors over-flag these. Need travel-specific context engine.

2. **Indian PII coverage** — Most off-the-shelf PII detectors handle US/EU formats well (SSN, GDPR-defined PII) but miss Indian-specific formats (Aadhaar, PAN, Indian passport numbers, IFSC codes). Custom recognizers are essential.

3. **Real-time vs. accuracy tradeoff** — Regex-based detection is fast (<1ms) but misses contextual PII. NER models are accurate (96%) but slow (200ms+). Need layered approach: regex for real-time ingestion, NER for batch processing.

4. **Vision model cost** — Running document understanding models per document costs ₹0.5-2 with APIs, or requires GPU infrastructure self-hosted. For an agency processing 50-100 documents/day, this is ₹1-3L/year in API costs.

---

## Next Steps

- [ ] Implement regex-based PII detector for Indian-specific formats (Aadhaar, PAN, passport)
- [ ] Integrate Presidio with custom Indian PII recognizers
- [ ] Build data classification engine with automatic tier assignment
- [ ] Evaluate document understanding models for passport/visa extraction
- [ ] Design PII redaction pipeline for document sanitization
