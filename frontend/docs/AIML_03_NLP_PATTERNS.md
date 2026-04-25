# AIML_03: Natural Language Processing Patterns

> Entity extraction, sentiment analysis, intent classification, and document processing for travel intelligence

---

## Document Overview

**Series:** AI/ML Patterns
**Document:** 3 of 4
**Focus:** Natural Language Processing
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Named Entity Recognition](#named-entity-recognition)
4. [Intent Classification](#intent-classification)
5. [Sentiment Analysis](#sentiment-analysis)
6. [Query Understanding](#query-understanding)
7. [Document Summarization](#document-summarization)
8. [Translation and Localization](#translation-and-localization)
9. [Response Generation](#response-generation)
10. [API Specification](#api-specification)
11. [Testing Scenarios](#testing-scenarios)
12. [Metrics Definitions](#metrics-definitions)

---

## 1. Introduction

### NLP in Travel Context

Natural Language Processing enables the Travel Agency Agent to understand and process unstructured text from various sources:

- **Customer Inquiries** - WhatsApp, email, web form messages
- **Trip Documents** - Itineraries, booking confirmations, tickets
- **Reviews** - Hotel, activity, and destination feedback
- **Communication** - Agent notes, customer interactions
- **Supplier Data** - Hotel descriptions, activity details

### Key Capabilities

| Capability | Use Case | Value |
|------------|----------|-------|
| **NER** | Extract dates, destinations, budget from messages | Auto-populate trip fields |
| **Intent Classification** | Understand customer request type | Route to right workflow |
| **Sentiment Analysis** | Detect customer mood | Prioritize unhappy customers |
| **Summarization** | Condense long conversations | Quick agent overview |
| **Translation** | Multi-language support | Global customer base |

---

## 2. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                           NLP Pipeline Layer                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Entity      │  │ Intent      │  │ Sentiment   │  │ Document │  │
│  │ Extractor   │  │ Classifier  │  │ Analyzer   │  │ Processor│  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬─────┘  │
│         │                │                │               │         │
│  ┌──────▼────────────────▼────────────────▼───────────────▼─────┐  │
│  │                    Text Preprocessing                       │  │
│  └──────┬──────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │              Model Registry & Embedding Cache                │  │
│  └──────┬──────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │              Feature Store & Training Pipeline               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **NER** | spaCy, Hugging Face transformers |
| **Intent Classification** | scikit-learn, fine-tuned BERT |
| **Sentiment** | VADER, RoBERTa sentiment |
| **Embeddings** | sentence-transformers, OpenAI embeddings |
| **Translation** | Google Translate API, DeepL |
| **Summarization** | BART, T5, GPT-based |

---

## 3. Named Entity Recognition

### Travel Entity Schema

```typescript
// nlp/entities/schema.ts

export enum TravelEntityType {
  // Date/Time
  DATE = 'date',
  DATE_RANGE = 'date_range',
  DURATION = 'duration',

  // Location
  DESTINATION = 'destination',
  ORIGIN = 'origin',
  COUNTRY = 'country',
  CITY = 'city',
  AIRPORT = 'airport',
  HOTEL = 'hotel',
  ATTRACTION = 'attraction',

  // People
  TRAVELER_COUNT = 'traveler_count',
  ADULTS = 'adults',
  CHILDREN = 'children',
  INFANTS = 'infants',
  AGES = 'ages',

  // Money
  BUDGET = 'budget',
  PRICE = 'price',
  CURRENCY = 'currency',

  // Trip Details
  TRIP_TYPE = 'trip_type',
  ACCOMMODATION_TYPE = 'accommodation_type',
  ROOM_TYPE = 'room_type',
  MEAL_PLAN = 'meal_plan',
  ACTIVITY = 'activity',
  INTEREST = 'interest',

  // Contact
  PHONE = 'phone',
  EMAIL = 'email',
  NAME = 'person_name'
}

export interface ExtractedEntity {
  type: TravelEntityType;
  value: any;
  text: string;
  startIndex: number;
  endIndex: number;
  confidence: number;
  normalized?: any;  // Normalized value (e.g., ISO date)
  metadata?: Record<string, any>;
}

export interface EntityExtractionResult {
  entities: ExtractedEntity[];
  confidence: number;
  processingTime: number;
  modelVersion: string;
}
```

### Entity Extractor

```typescript
// nlp/entities/extractor.ts

/**
 * Travel-specific entity extraction using spaCy and custom patterns
 */
export class TravelEntityExtractor {
  private nlp: any;  // spaCy NLP model
  private patterns: EntityPattern[];
  private embeddingModel: EmbeddingModel;

  constructor(config: EntityExtractorConfig) {
    this.nlp = spacy.load(config.modelName || 'en_core_web_lg');
    this.patterns = this.loadTravelPatterns();
    this.embeddingModel = new EmbeddingModel(config.embeddingModel);
  }

  /**
   * Extract entities from text
   */
  async extract(text: string): Promise<EntityExtractionResult> {
    const startTime = Date.now();

    // Run spaCy NER
    const doc = this.nlp(text);
    const entities: ExtractedEntity[] = [];

    // Extract standard entities
    for (const ent of doc.ents) {
      const mappedType = this.mapSpacyLabel(ent.label_);
      if (mappedType) {
        entities.push({
          type: mappedType,
          value: this.normalizeValue(ent.text, mappedType),
          text: ent.text,
          startIndex: ent.start_char,
          endIndex: ent.end_char,
          confidence: this.calculateConfidence(ent)
        });
      }
    }

    // Extract travel-specific patterns
    const patternMatches = this.extractPatterns(text);
    entities.push(...patternMatches);

    // Extract using semantic similarity for activities/interests
    const semanticMatches = await this.extractSemanticEntities(text);
    entities.push(...semanticMatches);

    // Merge overlapping entities (keep higher confidence)
    const merged = this.mergeOverlappingEntities(entities);

    return {
      entities: merged,
      confidence: this.calculateOverallConfidence(merged),
      processingTime: Date.now() - startTime,
      modelVersion: this.getModelVersion()
    };
  }

  /**
   * Load travel-specific regex patterns
   */
  private loadTravelPatterns(): EntityPattern[] {
    return [
      // Date ranges
      {
        type: TravelEntityType.DATE_RANGE,
        patterns: [
          /(?:from|between)?\s?(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\s?(?:to|until|through|-)\s?(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})/i,
          /(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?:to\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*/i,
          /(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:to|-)\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?/i
        ]
      },

      // Durations
      {
        type: TravelEntityType.DURATION,
        patterns: [
          /(\d+)\s*(?:days?|nights?)/i,
          /(\d+)\s*(?:weeks?)/i,
          /a\s+(week|day|night)/i,
          /(?:for|of)\s+(\d+)\s*days?/i
        ]
      },

      // Traveler counts
      {
        type: TravelEntityType.TRAVELER_COUNT,
        patterns: [
          /(\d+)\s*(?:people|persons|travelers?|guests?|pax)/i,
          /(\d+)\s+adults?(?:\s*,\s*(\d+)\s+kids?)?/i,
          /family\s+of\s+(\d+)/i,
          /couple/i,
          /solo\s+traveler?/i,
          /just\s+me/i
        ]
      },

      // Budget
      {
        type: TravelEntityType.BUDGET,
        patterns: [
          /budget\s*(?:is|:|of)?\s*(?:up\s+to|about|around)?\s*[$€£₹]?\s*([¥$€£₹]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/i,
          /(?:willing\s+to\s+spend|can\s+spend|maximum|max)\s*(?:up\s+to)??\s*[$€£₹]?\s*([$€£₹]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/i,
          /[$€£₹]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:budget|rupees?|dollars?|pounds?|euros?)/i
        ]
      },

      // Accommodation types
      {
        type: TravelEntityType.ACCOMMODATION_TYPE,
        patterns: [
          /\b(hotel|resort|villa|apartment|condo|hostel|guest\s+house|homestay|boutique\s+hotel|luxury\s+hotel|budget\s+hotel)\b/i
        ]
      },

      // Trip types
      {
        type: TravelEntityType.TRIP_TYPE,
        patterns: [
          /\b(honeymoon|anniversary|romantic|family\s+vacation|family\s+trip|solo\s+trip|group\s+trip|corporate|business|leisure|adventure|beach|cultural|pilgrimage|weekend\s+getaway|holiday|vacation)\b/i
        ]
      },

      // Activities/Interests
      {
        type: TravelEntityType.ACTIVITY,
        patterns: [
          /\b(sightseeing|trekking|hiking|scuba\s+diving|snorkeling|surfing|skiing|snowboarding|wildlife\s+safari|desert\s+safari|boat\s+ride|cruise|kayaking|parasailing|zip-lining|bungee\s+jumping|rock\s+climbing|camping|backpacking|city\s+tour|food\s+tour|wine\s+tasting|museum\s+visit|shopping|nightlife|clubbing|spa|wellness|yoga|meditation|photography|fishing|golf|water\s+sports|kids?\s+activities)\b/i
        ]
      }
    ];
  }

  /**
   * Extract entities using regex patterns
   */
  private extractPatterns(text: string): ExtractedEntity[] {
    const entities: ExtractedEntity[] = [];

    for (const pattern of this.patterns) {
      for (const regex of pattern.patterns) {
        regex.lastIndex = 0;  // Reset regex state

        let match;
        while ((match = regex.exec(text)) !== null) {
          const value = this.extractPatternValue(match, pattern.type);
          if (value !== null) {
            entities.push({
              type: pattern.type,
              value,
              text: match[0],
              startIndex: match.index,
              endIndex: match.index + match[0].length,
              confidence: 0.85
            });
          }
        }
      }
    }

    return entities;
  }

  /**
   * Extract entities using semantic similarity
   */
  private async extractSemanticEntities(
    text: string
  ): Promise<ExtractedEntity[]> {
    const entities: ExtractedEntity[] = [];

    // Get embedding for text
    const textEmbedding = await this.embeddingModel.embed(text);

    // Check against known entity embeddings
    const knownEntities = await this.getKnownEntityEmbeddings();

    for (const [entityText, entityData] of knownEntities) {
      const similarity = this.cosineSimilarity(
        textEmbedding,
        entityData.embedding
      );

      if (similarity > 0.75) {
        entities.push({
          type: entityData.type,
          value: entityData.value,
          text: entityText,
          startIndex: text.toLowerCase().indexOf(entityText.toLowerCase()),
          endIndex: text.toLowerCase().indexOf(entityText.toLowerCase()) + entityText.length,
          confidence: similarity
        });
      }
    }

    return entities;
  }

  /**
   * Normalize entity values
   */
  private normalizeValue(text: string, type: TravelEntityType): any {
    switch (type) {
      case TravelEntityType.DATE:
        return this.parseDate(text);

      case TravelEntityType.DATE_RANGE:
        return this.parseDateRange(text);

      case TravelEntityType.DURATION:
        return this.parseDuration(text);

      case TravelEntityType.BUDGET:
      case TravelEntityType.PRICE:
        return this.parseCurrency(text);

      case TravelEntityType.TRAVELER_COUNT:
        return this.parseTravelerCount(text);

      case TravelEntityType.DESTINATION:
      case TravelEntityType.CITY:
        return this.normalizeLocation(text);

      default:
        return text.trim();
    }
  }

  /**
   * Parse date from text
   */
  private parseDate(text: string): Date | null {
    // Try common formats
    const formats = [
      /\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b/,
      /\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b/i,
      /\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b/i
    ];

    for (const format of formats) {
      const match = text.match(format);
      if (match) {
        return new Date(match[0]);
      }
    }

    // Use date parser library as fallback
    return chrono.parseDate(text);
  }

  /**
   * Parse budget/price text
   */
  private parseCurrency(text: string): number {
    // Remove currency symbols and commas
    const cleaned = text
      .replace(/[$€£₹¥]/g, '')
      .replace(/,/g, '')
      .trim();

    const value = parseFloat(cleaned);
    return isNaN(value) ? 0 : value;
  }

  /**
   * Parse traveler count from text
   */
  private parseTravelerCount(text: string): { adults: number; children: number } {
    const lower = text.toLowerCase();

    // Special cases
    if (lower.includes('couple') || lower.includes('2 people')) {
      return { adults: 2, children: 0 };
    }
    if (lower.includes('solo') || lower.includes('just me') || lower.includes('1 person')) {
      return { adults: 1, children: 0 };
    }

    // Extract numbers
    const adultsMatch = lower.match(/(\d+)\s*adults?/);
    const kidsMatch = lower.match(/(\d+)\s*(?:kids?|children)/);
    const peopleMatch = lower.match(/(\d+)\s*(?:people|persons|pax|guests|travelers)/);

    const adults = adultsMatch ? parseInt(adultsMatch[1]) :
                   peopleMatch ? parseInt(peopleMatch[1]) : 0;
    const children = kidsMatch ? parseInt(kidsMatch[1]) : 0;

    return { adults, children };
  }
}
```

### Context-Aware Entity Resolution

```typescript
// nlp/entities/resolver.ts

/**
 * Resolve ambiguous entities using context
 */
export class EntityResolver {
  private locationService: LocationService;
  private embeddingModel: EmbeddingModel;

  /**
   * Resolve ambiguous location mentions
   */
  async resolveLocation(
    text: string,
    context: ExtractionContext
  ): Promise<ResolvedLocation | null> {
    // Extract location candidates
    const candidates = await this.locationService.search(text);

    if (candidates.length === 0) return null;
    if (candidates.length === 1) return candidates[0];

    // Disambiguate using context
    const scored = await this.scoreCandidates(candidates, context);

    return scored[0];
  }

  /**
   * Score location candidates based on context
   */
  private async scoreCandidates(
    candidates: Location[],
    context: ExtractionContext
  ): Promise<Array<{ location: Location; score: number }>> {
    const scores: Array<{ location: Location; score: number }> = [];

    for (const candidate of candidates) {
      let score = 0;

      // Popularity boost
      score += candidate.popularity * 0.2;

      // Context similarity
      if (context.previousDestinations) {
        const embedding = await this.embeddingModel.embed(candidate.name);
        for (const prev of context.previousDestinations) {
          const prevEmbedding = await this.embeddingModel.embed(prev);
          const similarity = this.cosineSimilarity(embedding, prevEmbedding);
          score += similarity * 0.3;
        }
      }

      // Budget alignment
      if (context.budget) {
        const budgetMatch = this.calculateBudgetMatch(candidate, context.budget);
        score += budgetMatch * 0.2;
      }

      // Seasonality
      if (context.travelDates) {
        const seasonalScore = this.getSeasonalScore(candidate, context.travelDates);
        score += seasonalScore * 0.3;
      }

      scores.push({ location: candidate, score });
    }

    return scores.sort((a, b) => b.score - a.score);
  }

  /**
   * Resolve date expressions relative to reference date
   */
  resolveDateExpression(
    text: string,
    referenceDate: Date = new Date()
  ): Date | DateRange | null {
    const lower = text.toLowerCase();

    // Relative dates
    if (lower.includes('next month')) {
      const nextMonth = new Date(referenceDate);
      nextMonth.setMonth(nextMonth.getMonth() + 1);
      return nextMonth;
    }

    if (lower.includes('this month')) {
      return new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1);
    }

    if (lower.includes('next week')) {
      const nextWeek = new Date(referenceDate);
      nextWeek.setDate(nextWeek.getDate() + 7);
      return nextWeek;
    }

    if (lower.includes('this weekend')) {
      const saturday = new Date(referenceDate);
      saturday.setDate(referenceDate.getDate() + (6 - referenceDate.getDay()));
      return saturday;
    }

    // Month names
    if (lower.includes('december') && !lower.includes(/\d{4}/)) {
      const year = referenceDate.getMonth() > 11
        ? referenceDate.getFullYear() + 1
        : referenceDate.getFullYear();
      return new Date(year, 11, 1);
    }

    // "In X days/weeks/months"
    const inMatch = lower.match(/in\s+(\d+)\s+(day|week|month)s?/);
    if (inMatch) {
      const amount = parseInt(inMatch[1]);
      const unit = inMatch[2];

      const result = new Date(referenceDate);
      if (unit === 'day') result.setDate(result.getDate() + amount);
      else if (unit === 'week') result.setDate(result.getDate() + amount * 7);
      else if (unit === 'month') result.setMonth(result.getMonth() + amount);

      return result;
    }

    return null;
  }
}
```

---

## 4. Intent Classification

### Intent Schema

```typescript
// nlp/intents/schema.ts

export enum TravelIntent {
  // Booking intents
  NEW_TRIP_INQUIRY = 'new_trip_inquiry',
  BOOKING_REQUEST = 'booking_request',
  QUOTE_REQUEST = 'quote_request',
  AVAILABILITY_CHECK = 'availability_check',

  // Information intents
  DESTINATION_INFO = 'destination_info',
  ACTIVITY_INFO = 'activity_info',
  PRICING_INFO = 'pricing_info',
  DOCUMENT_REQUEST = 'document_request',

  // Modification intents
  MODIFICATION_REQUEST = 'modification_request',
  CANCELLATION_REQUEST = 'cancellation_request',
  DATE_CHANGE = 'date_change',

  // Support intents
  COMPLAINT = 'complaint',
  FEEDBACK = 'feedback',
  QUESTION = 'question',
  URGENT_ISSUE = 'urgent_issue',

  // Generic
  GREETING = 'greeting',
  GOODBYE = 'goodbye',
  ACKNOWLEDGMENT = 'acknowledgment',
  UNKNOWN = 'unknown'
}

export interface IntentClassificationResult {
  intent: TravelIntent;
  confidence: number;
  subIntent?: string;
  entities: ExtractedEntity[];
  sentiment: SentimentResult;
  urgency: 'low' | 'medium' | 'high';
  suggestedActions: string[];
}
```

### Intent Classifier

```typescript
// nlp/intents/classifier.ts

/**
 * Multi-modal intent classifier using ensemble approach
 */
export class IntentClassifier {
  private keywordModel: KeywordIntentModel;
  private embeddingModel: EmbeddingIntentModel;
  private llmModel: LLMIntentModel;
  private fallbackModel: RuleBasedModel;

  /**
   * Classify intent using ensemble
   */
  async classify(
    text: string,
    context: ClassificationContext
  ): Promise<IntentClassificationResult> {
    // Get predictions from all models
    const predictions = await Promise.all([
      this.keywordModel.predict(text, context),
      this.embeddingModel.predict(text, context),
      this.fallbackModel.predict(text, context)
    ]);

    // Weighted ensemble
    const weights = {
      keyword: 0.2,
      embedding: 0.6,
      fallback: 0.2
    };

    const intentScores = new Map<TravelIntent, number>();

    for (const prediction of predictions) {
      for (const [intent, score] of Object.entries(prediction.scores)) {
        const current = intentScores.get(intent as TravelIntent) || 0;
        intentScores.set(
          intent as TravelIntent,
          current + score * weights[prediction.model]
        );
      }
    }

    // Get top intent
    const sorted = Array.from(intentScores.entries())
      .sort((a, b) => b[1] - a[1]);

    const [intent, confidence] = sorted[0];

    // Extract entities
    const entities = await this.extractEntities(text, context);

    // Analyze sentiment
    const sentiment = await this.analyzeSentiment(text);

    // Determine urgency
    const urgency = this.determineUrgency(text, intent, sentiment);

    // Generate suggested actions
    const suggestedActions = this.generateActions(intent, entities);

    return {
      intent: intent as TravelIntent,
      confidence,
      subIntent: this.getSubIntent(text, intent as TravelIntent),
      entities,
      sentiment,
      urgency,
      suggestedActions
    };
  }

  /**
   * Keyword-based intent model (fast, low accuracy)
   */
  class KeywordIntentModel {
    private intentKeywords: Map<TravelIntent, string[]>;

    constructor() {
      this.intentKeywords = new Map([
        [TravelIntent.NEW_TRIP_INQUIRY, [
          'plan a trip', 'want to go', 'looking for', 'interested in',
          'trip to', 'visit', 'going to', 'planning a vacation'
        ]],
        [TravelIntent.BOOKING_REQUEST, [
          'book', 'reserve', 'confirm', 'booking', 'reservation',
          'want to book', 'make a reservation'
        ]],
        [TravelIntent.QUOTE_REQUEST, [
          'quote', 'price', 'cost', 'how much', 'estimate',
          'pricing', 'rates', 'get a quote'
        ]],
        [TravelIntent.AVAILABILITY_CHECK, [
          'available', 'is there space', 'vacancy', 'open dates',
          'check availability', 'any rooms'
        ]],
        [TravelIntent.MODIFICATION_REQUEST, [
          'change', 'modify', 'update', 'alter', 'different dates',
          'want to change', 'modify booking'
        ]],
        [TravelIntent.CANCELLATION_REQUEST, [
          'cancel', 'cancellation', 'need to cancel', 'calling off'
        ]],
        [TravelIntent.COMPLAINT, [
          'disappointed', 'unhappy', 'terrible', 'awful', 'worst',
          'issue', 'problem', 'not satisfied', 'complain'
        ]],
        [TravelIntent.URGENT_ISSUE, [
          'urgent', 'emergency', 'asap', 'immediately', 'right now',
          'help needed', 'stuck', 'stranded'
        ]],
        [TravelIntent.GREETING, [
          'hi', 'hello', 'hey', 'good morning', 'good afternoon'
        ]],
        [TravelIntent.GOODBYE, [
          'bye', 'goodbye', 'thanks', 'thank you', 'see you'
        ]]
      ]);
    }

    predict(text: string): Promise<IntentPrediction> {
      const lower = text.toLowerCase();
      const scores: Record<string, number> = {};

      for (const [intent, keywords] of this.intentKeywords) {
        let score = 0;
        for (const keyword of keywords) {
          if (lower.includes(keyword)) {
            score += 1;
          }
        }
        scores[intent] = Math.min(score / 3, 1);  // Normalize
      }

      return Promise.resolve({
        model: 'keyword',
        scores
      });
    }
  }

  /**
   * Embedding-based intent model (accurate, medium speed)
   */
  class EmbeddingIntentModel {
    private intentEmbeddings: Map<TravelIntent, number[]>;
    private embeddingModel: EmbeddingModel;

    async train(examples: Map<TravelIntent, string[]>): Promise<void> {
      this.intentEmbeddings = new Map();

      for (const [intent, texts] of examples) {
        const embeddings = await Promise.all(
          texts.map(t => this.embeddingModel.embed(t))
        );

        // Average embedding for this intent
        const avgEmbedding = this.averageEmbeddings(embeddings);
        this.intentEmbeddings.set(intent, avgEmbedding);
      }
    }

    async predict(text: string): Promise<IntentPrediction> {
      const textEmbedding = await this.embeddingModel.embed(text);
      const scores: Record<string, number> = {};

      for (const [intent, intentEmbedding] of this.intentEmbeddings) {
        const similarity = this.cosineSimilarity(textEmbedding, intentEmbedding);
        scores[intent] = similarity;
      }

      // Apply softmax
      const softmaxScores = this.softmax(scores);

      return {
        model: 'embedding',
        scores: softmaxScores
      };
    }
  }
}
```

---

## 5. Sentiment Analysis

### Sentiment Analyzer

```typescript
// nlp/sentiment/analyzer.ts

export interface SentimentResult {
  sentiment: 'positive' | 'neutral' | 'negative';
  score: number;  // -1 to 1
  confidence: number;
  emotions: {
    joy: number;
    sadness: number;
    anger: number;
    fear: number;
    surprise: number;
    disgust: number;
  };
  aspects: AspectSentiment[];
}

export interface AspectSentiment {
  aspect: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  score: number;
  mentions: string[];
}

/**
 * Multi-level sentiment analysis
 */
export class SentimentAnalyzer {
  private vader: VaderAnalyzer;
  private emotionModel: EmotionClassifier;
  private aspectModel: AspectSentimentModel;

  /**
   * Analyze sentiment of text
   */
  async analyze(text: string): Promise<SentimentResult> {
    // VADER for base sentiment (fast, rule-based)
    const vaderResult = this.vader.analyze(text);

    // Fine-tuned model for nuanced sentiment
    const modelResult = await this.analyzeWithModel(text);

    // Combine results
    const sentiment = this.combineSentiments(vaderResult, modelResult);

    // Analyze emotions
    const emotions = await this.analyzeEmotions(text);

    // Aspect-based sentiment for reviews
    const aspects = await this.analyzeAspects(text);

    return {
      sentiment: sentiment.score > 0.1 ? 'positive' :
                 sentiment.score < -0.1 ? 'negative' : 'neutral',
      score: sentiment.score,
      confidence: sentiment.confidence,
      emotions,
      aspects
    };
  }

  /**
   * Analyze emotions using transformer model
   */
  private async analyzeEmotions(text: string): Promise<SentimentResult['emotions']> {
    const result = await this.emotionModel.predict(text);

    return {
      joy: result.joy || 0,
      sadness: result.sadness || 0,
      anger: result.anger || 0,
      fear: result.fear || 0,
      surprise: result.surprise || 0,
      disgust: result.disgust || 0
    };
  }

  /**
   * Aspect-based sentiment analysis
   */
  private async analyzeAspects(text: string): Promise<AspectSentiment[]> {
    const aspects: AspectSentiment[] = [];

    // Define aspects relevant to travel
    const aspectKeywords = {
      accommodation: ['hotel', 'room', 'resort', 'accommodation', 'bed', 'bathroom'],
      service: ['staff', 'service', 'hospitality', 'management', 'support'],
      location: ['location', 'area', 'neighborhood', 'beach', 'city center'],
      food: ['food', 'restaurant', 'dining', 'breakfast', 'meal', 'cuisine'],
      activities: ['activity', 'excursion', 'tour', 'sightseeing', 'adventure'],
      value: ['price', 'cost', 'value', 'expensive', 'cheap', 'worth'],
      cleanliness: ['clean', 'dirty', 'hygiene', 'sanitary', 'tidy'],
      comfort: ['comfortable', 'comfort', 'bed quality', 'amenities']
    };

    for (const [aspect, keywords] of Object.entries(aspectKeywords)) {
      const sentences = this.extractSentencesAbout(text, keywords);

      if (sentences.length > 0) {
        const aspectScores = sentences.map(s =>
          this.vader.analyze(s).compound
        );

        const avgScore = aspectScores.reduce((a, b) => a + b, 0) / aspectScores.length;

        aspects.push({
          aspect,
          sentiment: avgScore > 0.1 ? 'positive' : avgScore < -0.1 ? 'negative' : 'neutral',
          score: avgScore,
          mentions: sentences
        });
      }
    }

    return aspects;
  }

  /**
   * Extract sentences containing aspect keywords
   */
  private extractSentencesAbout(text: string, keywords: string[]): string[] {
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    return sentences.filter(s =>
      keywords.some(k => s.toLowerCase().includes(k))
    );
  }
}

/**
 * Customer satisfaction tracking
 */
export class SatisfactionTracker {
  private sentimentAnalyzer: SentimentAnalyzer;

  /**
   * Track customer satisfaction over time
   */
  async trackCustomerSatisfaction(
    customerId: string
  ): Promise<CustomerSatisfactionReport> {
    const communications = await this.getCustomerCommunications(customerId);

    const sentimentOverTime: Array<{ date: Date; score: number }> = [];
    const totalSentiments = { positive: 0, neutral: 0, negative: 0 };
    const aspectScores: Map<string, number[]> = new Map();

    for (const comm of communications) {
      const sentiment = await this.sentimentAnalyzer.analyze(comm.text);

      sentimentOverTime.push({
        date: comm.timestamp,
        score: sentiment.score
      });

      totalSentiments[sentiment.sentiment]++;

      // Track aspect sentiments
      for (const aspect of sentiment.aspects) {
        if (!aspectScores.has(aspect.aspect)) {
          aspectScores.set(aspect.aspect, []);
        }
        aspectScores.get(aspect.aspect)!.push(aspect.score);
      }
    }

    // Calculate trends
    const trend = this.calculateTrend(sentimentOverTime);
    const riskLevel = this.assessRisk(totalSentiments, trend);

    return {
      customerId,
      overallSentiment: this.calculateOverall(totalSentiments),
      trend,
      riskLevel,
      sentimentOverTime,
      aspectBreakdown: this.summarizeAspects(aspectScores),
      totalCommunications: communications.length
    };
  }

  private calculateTrend(
    history: Array<{ date: Date; score: number }>
  ): 'improving' | 'stable' | 'declining' {
    if (history.length < 3) return 'stable';

    const recent = history.slice(-5);
    const older = history.slice(0, -5);

    const recentAvg = recent.reduce((s, h) => s + h.score, 0) / recent.length;
    const olderAvg = older.reduce((s, h) => s + h.score, 0) / older.length;

    const diff = recentAvg - olderAvg;

    if (diff > 0.2) return 'improving';
    if (diff < -0.2) return 'declining';
    return 'stable';
  }

  private assessRisk(
    sentiments: { positive: number; neutral: number; negative: number },
    trend: string
  ): 'low' | 'medium' | 'high' | 'critical' {
    const total = sentiments.positive + sentiments.neutral + sentiments.negative;
    const negativeRatio = sentiments.negative / total;

    if (negativeRatio > 0.5 || (negativeRatio > 0.3 && trend === 'declining')) {
      return 'critical';
    }
    if (negativeRatio > 0.3 || trend === 'declining') {
      return 'high';
    }
    if (negativeRatio > 0.15) {
      return 'medium';
    }
    return 'low';
  }
}
```

---

## 6. Query Understanding

### Semantic Search

```typescript
// nlp/search/semantic.ts

/**
 * Semantic search for travel content
 */
export class SemanticSearchEngine {
  private embeddingModel: EmbeddingModel;
  private vectorStore: VectorStore;
  private reranker: QueryReranker;

  /**
   * Search for relevant destinations, activities, etc.
   */
  async search(
    query: string,
    options: SearchOptions
  ): Promise<SearchResult[]> {
    // Generate query embedding
    const queryEmbedding = await this.embeddingModel.embed(query);

    // Initial vector search
    let candidates = await this.vectorStore.search({
      embedding: queryEmbedding,
      filter: this.buildFilter(options),
      limit: options.limit * 3  // Get more for reranking
    });

    // Rerank based on query relevance
    candidates = await this.reranker.rerank(query, candidates);

    // Apply business rules
    candidates = this.applyBusinessRules(candidates, options);

    return candidates.slice(0, options.limit);
  }

  /**
   * Build filter for vector search
   */
  private buildFilter(options: SearchOptions): VectorFilter {
    const filters: VectorFilter = {};

    if (options.destinationType) {
      filters.type = options.destinationType;
    }

    if (options.budget) {
      filters.avgCost = { $lte: options.budget.max };
    }

    if (options.travelDates) {
      const season = this.getSeason(options.travelDates.start);
      filters.bestSeasons = { $in: [season] };
    }

    if (options.travelerProfile) {
      if (options.travelerProfile.children > 0) {
        filters.familyFriendly = true;
      }
    }

    return filters;
  }

  /**
   * Apply business rules to search results
   */
  private applyBusinessRules(
    results: SearchResult[],
    options: SearchOptions
  ): SearchResult[] {
    // Boost recently booked destinations
    for (const result of results) {
      if (result.recentBookings > 10) {
        result.score *= 1.1;
      }

      // Boost based on availability
      if (result.availability === 'high') {
        result.score *= 1.05;
      } else if (result.availability === 'low') {
        result.score *= 0.8;
      }

      // Boost based on seasonality
      if (options.travelDates) {
        const seasonality = this.getSeasonalityScore(
          result.id,
          options.travelDates.start
        );
        result.score *= (1 + seasonality * 0.2);
      }
    }

    // Re-sort after boosting
    return results.sort((a, b) => b.score - a.score);
  }
}
```

### Query Parser

```typescript
// nlp/search/parser.ts

export interface ParsedQuery {
  type: 'simple' | 'complex' | 'conversational';
  intents: ParsedIntent[];
  constraints: QueryConstraint[];
  filters: QueryFilter[];
  sortBy?: string;
  limit?: number;
}

export interface QueryConstraint {
  type: 'date' | 'budget' | 'duration' | 'travelers' | 'location';
  operator: '=' | '<=' | '>=' | '>' | '<' | 'between';
  value: any;
}

/**
 * Parse natural language query into structured search
 */
export class QueryParser {
  private entityExtractor: TravelEntityExtractor;

  async parse(query: string): Promise<ParsedQuery> {
    // Extract entities
    const entities = await this.entityExtractor.extract(query);

    // Determine query type
    const type = this.determineQueryType(query, entities);

    // Extract constraints
    const constraints = this.extractConstraints(entities);

    // Extract filters
    const filters = this.extractFilters(query, entities);

    // Detect sort preference
    const sortBy = this.detectSortPreference(query);

    // Detect limit
    const limit = this.detectLimit(query);

    return {
      type,
      intents: this.extractIntents(query),
      constraints,
      filters,
      sortBy,
      limit
    };
  }

  private extractConstraints(entities: ExtractedEntity[]): QueryConstraint[] {
    const constraints: QueryConstraint[] = [];

    for (const entity of entities) {
      switch (entity.type) {
        case TravelEntityType.DATE_RANGE:
          constraints.push({
            type: 'date',
            operator: 'between',
            value: entity.normalized
          });
          break;

        case TravelEntityType.BUDGET:
          constraints.push({
            type: 'budget',
            operator: '<=',
            value: entity.value
          });
          break;

        case TravelEntityType.DURATION:
          constraints.push({
            type: 'duration',
            operator: '=',
            value: entity.value
          });
          break;

        case TravelEntityType.TRAVELER_COUNT:
          constraints.push({
            type: 'travelers',
            operator: '=',
            value: entity.value
          });
          break;
      }
    }

    return constraints;
  }

  private extractFilters(query: string, entities: ExtractedEntity[]): QueryFilter[] {
    const filters: QueryFilter[] = [];
    const lower = query.toLowerCase();

    // Trip type filters
    const tripTypes = [
      'honeymoon', 'family vacation', 'solo trip', 'group trip',
      'adventure', 'beach', 'cultural', 'pilgrimage'
    ];

    for (const type of tripTypes) {
      if (lower.includes(type)) {
        filters.push({ field: 'tripType', value: type });
      }
    }

    // Activity filters
    for (const entity of entities) {
      if (entity.type === TravelEntityType.ACTIVITY) {
        filters.push({ field: 'activities', value: entity.value });
      }
    }

    // Accommodation type filters
    for (const entity of entities) {
      if (entity.type === TravelEntityType.ACCOMMODATION_TYPE) {
        filters.push({ field: 'accommodationType', value: entity.value });
      }
    }

    return filters;
  }
}
```

---

## 7. Document Summarization

### Trip Conversation Summarizer

```typescript
// nlp/summarization/conversation.ts

/**
 * Summarize trip conversation history
 */
export class ConversationSummarizer {
  private summarizationModel: SummarizationModel;

  /**
   * Generate summary of conversation
   */
  async summarize(conversation: ConversationMessage[]): Promise<ConversationSummary> {
    // Extract key information
    const keyInfo = this.extractKeyInfo(conversation);

    // Generate narrative summary
    const narrative = await this.generateNarrative(conversation);

    // Extract decisions made
    const decisions = this.extractDecisions(conversation);

    // Extract pending items
    const pending = this.extractPendingItems(conversation);

    return {
      tripId: keyInfo.tripId,
      customerName: keyInfo.customerName,
      narrative,
      keyPoints: this.extractKeyPoints(conversation),
      decisions,
      pending,
      nextSteps: this.extractNextSteps(conversation),
      sentiment: this.analyzeOverallSentiment(conversation),
      summary: this.createBriefSummary(keyInfo, decisions, pending)
    };
  }

  /**
   * Generate narrative summary using LLM
   */
  private async generateNarrative(
    conversation: ConversationMessage[]
  ): Promise<string> {
    const messages = conversation
      .map(m => `${m.sender}: ${m.text}`)
      .join('\n');

    const prompt = `Summarize the following trip planning conversation:

${messages}

Focus on:
- Customer preferences and requirements
- Destinations and options discussed
- Decisions made
- Any concerns or objections raised
- Next steps

Summary:`;

    return await this.summarizationModel.summarize(prompt);
  }

  /**
   * Extract key information from conversation
   */
  private extractKeyInfo(conversation: ConversationMessage[]): KeyInfo {
    const info: KeyInfo = {
      tripId: null,
      customerName: null,
      destinations: [],
      dates: null,
      budget: null,
      travelers: null,
      preferences: []
    };

    for (const msg of conversation) {
      // Extract entities from each message
      // (using entity extractor)
    }

    return info;
  }
}

/**
 * Document summarizer for itineraries, quotes, etc.
 */
export class DocumentSummarizer {
  /**
   * Summarize trip itinerary
   */
  async summarizeItinerary(itinerary: TripItinerary): Promise<ItinerarySummary> {
    return {
      destination: itinerary.destination.name,
      duration: `${itinerary.duration.days} days, ${itinerary.duration.nights} nights`,
      dates: `${itinerary.startDate} to ${itinerary.endDate}`,
      highlights: itinerary.days
        .flatMap(d => d.activities)
        .filter(a => a.highlight)
        .map(a => a.name),
      accommodations: itinerary.accommodations.map(a => ({
        name: a.name,
        location: a.location,
        nights: a.nights
      })),
      totalCost: itinerary.totalCost,
      includes: itinerary.inclusions,
      excludes: itinerary.exclusions
    };
  }

  /**
   * Summarize quote document
   */
  async summarizeQuote(quote: TripQuote): Promise<QuoteSummary> {
    return {
      destination: quote.destination.name,
      validity: `Valid until ${quote.validUntil}`,
      price: {
        amount: quote.totalPrice,
        currency: quote.currency,
        perPerson: quote.totalPrice / quote.travelers.total
      },
      inclusions: quote.inclusions,
      exclusions: quote.exclusions,
      terms: quote.terms.slice(0, 3),  // Key terms only
      contact: quote.agentContact
    };
  }
}
```

---

## 8. Translation and Localization

### Translation Service

```typescript
// nlp/translation/service.ts

/**
 * Multi-language translation service
 */
export class TranslationService {
  private translator: Translator;
  private cache: TranslationCache;

  /**
   * Translate text to target language
   */
  async translate(
    text: string,
    targetLanguage: string,
    sourceLanguage?: string
  ): Promise<TranslationResult> {
    // Check cache
    const cacheKey = this.getCacheKey(text, targetLanguage, sourceLanguage);
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;

    // Detect language if not specified
    const detected = sourceLanguage || await this.detectLanguage(text);

    // Skip if already in target language
    if (detected === targetLanguage) {
      return {
        originalText: text,
        translatedText: text,
        sourceLanguage: detected,
        targetLanguage,
        confidence: 1
      };
    }

    // Translate
    const translated = await this.translator.translate(text, targetLanguage, detected);

    const result: TranslationResult = {
      originalText: text,
      translatedText: translated.text,
      sourceLanguage: detected,
      targetLanguage,
      confidence: translated.confidence
    };

    // Cache result
    await this.cache.set(cacheKey, result);

    return result;
  }

  /**
   * Translate with context preservation
   */
  async translateWithContext(
    text: string,
    context: TranslationContext
  ): Promise<TranslationResult> {
    // Add context markers for entities
    const markedText = this.addContextMarkers(text, context.entities);

    // Translate
    const result = await this.translate(
      markedText,
      context.targetLanguage,
      context.sourceLanguage
    );

    // Remove markers and preserve entity values
    result.translatedText = this.removeMarkers(result.translatedText, context.entities);

    return result;
  }

  /**
   * Batch translate for efficiency
   */
  async batchTranslate(
    items: Array<{ text: string; targetLanguage: string }>,
    sourceLanguage?: string
  ): Promise<TranslationResult[]> {
    // Group by target language for batch API calls
    const grouped = new Map<string, string[]>();

    for (const item of items) {
      if (!grouped.has(item.targetLanguage)) {
        grouped.set(item.targetLanguage, []);
      }
      grouped.get(item.targetLanguage)!.push(item.text);
    }

    const results: TranslationResult[] = [];
    const resultIndex = new Map<string, TranslationResult>();

    for (const [targetLang, texts] of grouped) {
      const batchResults = await this.translator.batchTranslate(
        texts,
        targetLang,
        sourceLanguage
      );

      for (let i = 0; i < texts.length; i++) {
        resultIndex.set(`${targetLang}:${texts[i]}`, batchResults[i]);
      }
    }

    // Return in original order
    for (const item of items) {
      results.push(resultIndex.get(`${item.targetLanguage}:${item.text}`)!);
    }

    return results;
  }

  /**
   * Detect language of text
   */
  private async detectLanguage(text: string): Promise<string> {
    return await this.translator.detect(text);
  }
}
```

### Localization

```typescript
// nlp/translation/localization.ts

/**
 * Localization service for dates, currencies, etc.
 */
export class LocalizationService {
  /**
   * Format date according to locale
   */
  formatDate(date: Date, locale: string, format?: 'short' | 'medium' | 'long'): string {
    const formatter = new Intl.DateTimeFormat(locale, {
      dateStyle: format || 'medium'
    });
    return formatter.format(date);
  }

  /**
   * Format currency according to locale
   */
  formatCurrency(amount: number, currency: string, locale: string): string {
    const formatter = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency
    });
    return formatter.format(amount);
  }

  /**
   * Format number according to locale
   */
  formatNumber(number: number, locale: string, options?: Intl.NumberFormatOptions): string {
    const formatter = new Intl.NumberFormat(locale, options);
    return formatter.format(number);
  }

  /**
   * Get localized destination name
   */
  getDestinationName(destinationId: string, locale: string): string {
    const names = {
      en: { paris: 'Paris', tokyo: 'Tokyo', bali: 'Bali' },
      es: { paris: 'París', tokyo: 'Tokio', bali: 'Bali' },
      fr: { paris: 'Paris', tokyo: 'Tokyo', bali: 'Bali' },
      de: { paris: 'Paris', tokyo: 'Tokio', bali: 'Bali' },
      zh: { paris: '巴黎', tokyo: '东京', bali: '巴厘岛' },
      ja: { paris: 'パリ', tokyo: '東京', bali: 'バリ' },
      ar: { paris: 'باريس', tokyo: 'طوكيو', bali: 'بالي' }
    };

    return names[locale]?.[destinationId] || names['en'][destinationId] || destinationId;
  }

  /**
   * Translate activity names
   */
  getActivityName(activityId: string, locale: string): string {
    // Similar to destination names
    const translations = this.loadActivityTranslations();
    return translations[locale]?.[activityId] || translations['en'][activityId] || activityId;
  }
}
```

---

## 9. Response Generation

### Template-Based Response

```typescript
// nlp/response/template.ts

/**
 * Generate responses using templates
 */
export class TemplateResponseGenerator {
  private templates: Map<string, ResponseTemplate[]>;

  /**
   * Generate response based on intent and entities
   */
  async generate(
    intent: TravelIntent,
    entities: ExtractedEntity[],
    context: ResponseContext
  ): Promise<string> {
    const templates = this.getTemplates(intent);

    // Select best template based on context
    const template = this.selectTemplate(templates, entities, context);

    // Fill template with entity values
    const response = this.fillTemplate(template, entities, context);

    return response;
  }

  /**
   * Fill template with values
   */
  private fillTemplate(
    template: ResponseTemplate,
    entities: ExtractedEntity[],
    context: ResponseContext
  ): string {
    let response = template.text;

    // Replace entity placeholders
    for (const entity of entities) {
      const placeholder = `{{${entity.type}}}`;
      response = response.replace(new RegExp(placeholder, 'g'), entity.text);
    }

    // Replace context placeholders
    response = response.replace(/{{customer_name}}/g, context.customerName || 'there');
    response = response.replace(/{{agent_name}}/g, context.agentName || 'our team');
    response = response.replace(/{{agency_name}}/g, context.agencyName || 'we');

    return response;
  }

  /**
   * Select best template for context
   */
  private selectTemplate(
    templates: ResponseTemplate[],
    entities: ExtractedEntity[],
    context: ResponseContext
  ): ResponseTemplate {
    // Score templates based on entity coverage
    const scored = templates.map(template => {
      let score = 0;

      // Check if required entities are present
      for (const required of template.requiredEntities || []) {
        if (entities.some(e => e.type === required)) {
          score += 10;
        } else {
          score -= 20;
        }
      }

      // Contextual factors
      if (template.sentiment === 'positive' && context.sentiment === 'positive') {
        score += 5;
      }

      if (template.isUrgent && context.urgency === 'high') {
        score += 10;
      }

      return { template, score };
    });

    scored.sort((a, b) => b.score - a.score);

    return scored[0]?.template || templates[0];
  }
}

/**
 * Response templates
 */
const responseTemplates: ResponseTemplate[] = [
  {
    intent: TravelIntent.NEW_TRIP_INQUIRY,
    text: "Hi {{customer_name}}! I'd love to help you plan your trip to {{destination}}. When are you looking to travel, and how many people will be going?",
    requiredEntities: [TravelEntityType.DESTINATION],
    sentiment: 'neutral',
    isUrgent: false
  },
  {
    intent: TravelIntent.NEW_TRIP_INQUIRY,
    text: "Hello! I see you're interested in visiting {{destination}}. That's a wonderful choice! To give you the best options, could you tell me your preferred travel dates and budget?",
    requiredEntities: [TravelEntityType.DESTINATION],
    sentiment: 'positive',
    isUrgent: false
  },
  {
    intent: TravelIntent.QUOTE_REQUEST,
    text: "I'll be happy to provide a quote for your trip to {{destination}}. Based on {{duration}} for {{traveler_count}} people, the estimated cost would be around {{budget}}. Would you like me to send you a detailed breakdown?",
    requiredEntities: [TravelEntityType.DESTINATION, TravelEntityType.DURATION],
    sentiment: 'neutral',
    isUrgent: false
  },
  {
    intent: TravelIntent.COMPLAINT,
    text: "I'm truly sorry to hear about your experience, {{customer_name}}. This is not the level of service we aim to provide. I'd like to make this right - could you please share more details so I can address this immediately?",
    requiredEntities: [],
    sentiment: 'negative',
    isUrgent: true
  }
];
```

### LLM-Based Response

```typescript
// nlp/response/llm.ts

/**
 * Generate contextual responses using LLM
 */
export class LLMResponseGenerator {
  private llmClient: LLMClient;

  /**
   * Generate contextual response
   */
  async generate(request: ResponseGenerationRequest): Promise<string> {
    const prompt = this.buildPrompt(request);

    const response = await this.llmClient.complete({
      prompt,
      maxTokens: 200,
      temperature: 0.7,
      stopSequences: ['\n\n', 'Agent:']
    });

    return response.text.trim();
  }

  /**
   * Build prompt for response generation
   */
  private buildPrompt(request: ResponseGenerationRequest): string {
    const { context, lastMessage, intent, entities } = request;

    let prompt = `You are a helpful travel agent assistant. Generate a natural, friendly response to the customer.

`;

    // Add context
    if (context.customerName) {
      prompt += `Customer: ${context.customerName}\n`;
    }

    if (context.tripDetails) {
      prompt += `Trip: ${context.tripDetails.destination}, ${context.tripDetails.dates}\n`;
    }

    // Add conversation history summary
    if (context.conversationSummary) {
      prompt += `Conversation so far: ${context.conversationSummary}\n`;
    }

    // Add last message
    prompt += `\nCustomer message: "${lastMessage}"\n`;

    // Add detected intent
    prompt += `\nIntent: ${intent}\n`;

    // Add extracted entities
    if (entities.length > 0) {
      prompt += `Key information: ${entities.map(e => `${e.type}=${e.value}`).join(', ')}\n`;
    }

    // Add instructions
    prompt += `
Generate a response that:
1. Acknowledges what the customer said
2. Asks relevant follow-up questions based on missing information
3. Is conversational and friendly
4. Is concise (1-2 sentences)
5. Matches the customer's tone

Response:`;

    return prompt;
  }

  /**
   * Generate response with options
   */
  async generateWithOptions(
    request: ResponseGenerationRequest,
    options: ResponseOption[]
  ): Promise<GeneratedResponseWithOptions> {
    const mainResponse = await this.generate(request);

    // Generate quick reply options
    const quickReplies = this.generateQuickReplies(request, options);

    return {
      response: mainResponse,
      quickReplies,
      suggestedActions: this.suggestActions(request.intent, request.entities)
    };
  }

  private generateQuickReplies(
    request: ResponseGenerationRequest,
    options: ResponseOption[]
  ): string[] {
    // Context-aware quick replies
    const missingInfo = this.identifyMissingInfo(request);

    const replies: string[] = [];

    for (const info of missingInfo) {
      switch (info) {
        case 'dates':
          replies.push('This month', 'Next month', 'Flexible dates');
          break;
        case 'budget':
          replies.push('Budget-friendly', 'Mid-range', 'Luxury');
          break;
        case 'duration':
          replies.push('Weekend trip', '5-7 days', '10+ days');
          break;
        case 'travelers':
          replies.push('Solo', 'Couple', 'Family', 'Group');
          break;
      }
    }

    return replies.slice(0, 4);
  }

  private identifyMissingInfo(request: ResponseGenerationRequest): string[] {
    const entities = new Set(request.entities.map(e => e.type));
    const missing: string[] = [];

    if (!entities.has(TravelEntityType.DATE_RANGE) && !entities.has(TravelEntityType.DATE)) {
      missing.push('dates');
    }

    if (!entities.has(TravelEntityType.BUDGET)) {
      missing.push('budget');
    }

    if (!entities.has(TravelEntityType.DURATION)) {
      missing.push('duration');
    }

    if (!entities.has(TravelEntityType.TRAVELER_COUNT)) {
      missing.push('travelers');
    }

    return missing;
  }
}
```

---

## 10. API Specification

### NLP Processing Endpoints

```typescript
// api/nlp.ts

/**
 * POST /api/nlp/extract
 * Extract entities from text
 */
interface ExtractEntitiesRequest {
  text: string;
  context?: {
    customerId?: string;
    tripId?: string;
    referenceDate?: string;
  };
}

interface ExtractEntitiesResponse {
  entities: Array<{
    type: string;
    value: any;
    text: string;
    confidence: number;
    normalized?: any;
  }>;
  confidence: number;
  processingTime: number;
}

/**
 * POST /api/nlp/classify
 * Classify intent of message
 */
interface ClassifyIntentRequest {
  text: string;
  context?: {
    conversationHistory?: Array<{ role: string; text: string }>;
    customerId?: string;
  };
}

interface ClassifyIntentResponse {
  intent: string;
  confidence: number;
  subIntent?: string;
  sentiment: {
    sentiment: 'positive' | 'neutral' | 'negative';
    score: number;
  };
  urgency: 'low' | 'medium' | 'high';
  suggestedActions: string[];
}

/**
 * POST /api/nlp/analyze
 * Full NLP analysis (entities + intent + sentiment)
 */
interface AnalyzeTextRequest {
  text: string;
  context?: {
    customerId?: string;
    tripId?: string;
    conversationHistory?: Array<{ role: string; text: string }>;
  };
}

interface AnalyzeTextResponse {
  entities: ExtractEntitiesResponse['entities'];
  intent: ClassifyIntentResponse['intent'];
  intentConfidence: number;
  sentiment: ClassifyIntentResponse['sentiment'];
  urgency: ClassifyIntentResponse['urgency'];
  suggestedResponse?: string;
  suggestedActions: string[];
}

/**
 * POST /api/nlp/summarize
 * Summarize conversation or document
 */
interface SummarizeRequest {
  type: 'conversation' | 'itinerary' | 'quote';
  content: any;  // Varies by type
  options?: {
    length?: 'brief' | 'detailed';
    include?: string[];
  };
}

interface SummarizeResponse {
  summary: string;
  keyPoints: string[];
  decisions?: Array<{ decision: string; timestamp: string }>;
  pendingItems?: string[];
  nextSteps?: string[];
}

/**
 * POST /api/nlp/translate
 * Translate text
 */
interface TranslateRequest {
  text: string;
  targetLanguage: string;
  sourceLanguage?: string;
  preserveEntities?: boolean;
}

interface TranslateResponse {
  originalText: string;
  translatedText: string;
  sourceLanguage: string;
  targetLanguage: string;
  confidence: number;
}

/**
 * POST /api/nlp/search
 * Semantic search
 */
interface SemanticSearchRequest {
  query: string;
  type: 'destination' | 'activity' | 'accommodation' | 'all';
  filters?: {
    destinationType?: string[];
    budget?: { min: number; max: number };
    dates?: { start: string; end: string };
    travelers?: { adults: number; children: number };
  };
  limit?: number;
}

interface SemanticSearchResponse {
  results: Array<{
    id: string;
    type: string;
    name: string;
    score: number;
    highlights: string[];
    metadata?: Record<string, any>;
  }>;
  total: number;
}
```

---

## 11. Testing Scenarios

### Unit Tests

```typescript
// __tests__/nlp/entity-extraction.test.ts

describe('TravelEntityExtractor', () => {
  let extractor: TravelEntityExtractor;

  beforeEach(() => {
    extractor = new TravelEntityExtractor();
  });

  describe('extract', () => {
    it('should extract destination from text', async () => {
      const text = 'I want to visit Paris next month';
      const result = await extractor.extract(text);

      const destination = result.entities.find(
        e => e.type === TravelEntityType.DESTINATION
      );

      expect(destination).toBeDefined();
      expect(destination?.value).toBe('Paris');
    });

    it('should extract date range', async () => {
      const text = 'Planning a trip from June 15 to June 20, 2026';
      const result = await extractor.extract(text);

      const dateRange = result.entities.find(
        e => e.type === TravelEntityType.DATE_RANGE
      );

      expect(dateRange).toBeDefined();
      expect(dateRange?.value.start).toEqual(new Date('2026-06-15'));
      expect(dateRange?.value.end).toEqual(new Date('2026-06-20'));
    });

    it('should extract budget', async () => {
      const text = 'My budget is around $5000';
      const result = await extractor.extract(text);

      const budget = result.entities.find(
        e => e.type === TravelEntityType.BUDGET
      );

      expect(budget).toBeDefined();
      expect(budget?.value).toBe(5000);
    });

    it('should extract traveler count', async () => {
      const text = '2 adults and 1 child';
      const result = await extractor.extract(text);

      const travelers = result.entities.find(
        e => e.type === TravelEntityType.TRAVELER_COUNT
      );

      expect(travelers).toBeDefined();
      expect(travelers?.value).toEqual({ adults: 2, children: 1 });
    });

    it('should extract trip type', async () => {
      const text = 'Planning a honeymoon trip';
      const result = await extractor.extract(text);

      const tripType = result.entities.find(
        e => e.type === TravelEntityType.TRIP_TYPE
      );

      expect(tripType).toBeDefined();
      expect(tripType?.value).toBe('honeymoon');
    });
  });
});

describe('IntentClassifier', () => {
  let classifier: IntentClassifier;

  beforeEach(() => {
    classifier = new IntentClassifier();
  });

  describe('classify', () => {
    it('should classify booking request', async () => {
      const text = 'I want to book a trip to Bali';
      const result = await classifier.classify(text, {});

      expect(result.intent).toBe(TravelIntent.BOOKING_REQUEST);
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    it('should classify complaint', async () => {
      const text = 'I am very disappointed with the service';
      const result = await classifier.classify(text, {});

      expect(result.intent).toBe(TravelIntent.COMPLAINT);
      expect(result.sentiment.sentiment).toBe('negative');
    });

    it('should classify urgent issue', async () => {
      const text = 'Emergency! I am stuck at the airport and need help immediately';
      const result = await classifier.classify(text, {});

      expect(result.intent).toBe(TravelIntent.URGENT_ISSUE);
      expect(result.urgency).toBe('high');
    });
  });
});
```

### Integration Tests

```typescript
// __tests__/integration/nlp-pipeline.test.ts

describe('NLP Pipeline Integration', () => {
  describe('End-to-end message processing', () => {
    it('should process customer inquiry and extract trip details', async () => {
      const message = 'Hi, I want to plan a family trip to Bali for 2 adults and 2 kids in December. Our budget is around $8000.';

      const result = await app.request('/api/nlp/analyze', {
        method: 'POST',
        body: JSON.stringify({ text: message })
      });

      expect(result.status).toBe(200);
      const data = await result.json();

      expect(data.intent).toBe('new_trip_inquiry');
      expect(data.entities).toContainEqual(
        expect.objectContaining({ type: 'destination', value: 'Bali' })
      );
      expect(data.entities).toContainEqual(
        expect.objectContaining({ type: 'traveler_count', value: { adults: 2, children: 2 } })
      );
      expect(data.entities).toContainEqual(
        expect.objectContaining({ type: 'budget', value: 8000 })
      );
    });
  });

  describe('Conversation summarization', () => {
    it('should summarize multi-turn conversation', async () => {
      const conversation = [
        { role: 'customer', text: 'I want to visit Paris' },
        { role: 'agent', text: 'Great choice! When would you like to travel?' },
        { role: 'customer', text: 'In July, for about a week' },
        { role: 'agent', text: 'How many people will be traveling?' },
        { role: 'customer', text: 'Just me and my spouse' },
        { role: 'agent', text: 'And what\'s your budget range?' },
        { role: 'customer', text: 'Around $5000' }
      ];

      const result = await app.request('/api/nlp/summarize', {
        method: 'POST',
        body: JSON.stringify({
          type: 'conversation',
          content: { messages: conversation }
        })
      });

      expect(result.status).toBe(200);
      const data = await result.json();

      expect(data.summary).toContain('Paris');
      expect(data.summary).toContain('July');
      expect(data.keyPoints).toHaveLength.greaterThan(0);
      expect(data.pendingItems).not.toContain('dates');
      expect(data.pendingItems).not.toContain('travelers');
    });
  });
});
```

---

## 12. Metrics Definitions

### NLP Performance Metrics

```typescript
// metrics/nlp-metrics.ts

export interface NLPModelMetrics {
  // Entity extraction
  entityPrecision: number;
  entityRecall: number;
  entityF1: number;
  entityAccuracy: number;  // Exact match accuracy

  // Intent classification
  intentAccuracy: number;
  intentConfusionMatrix: ConfusionMatrix;
  topKAccuracy: Map<number, number>;

  // Sentiment analysis
  sentimentAccuracy: number;
  sentimentF1: number;

  // Summarization
  rouge1: number;  // ROUGE-1 F1
  rouge2: number;  // ROUGE-2 F1
  rougeL: number;  // ROUGE-L F1
  bertScore: number;

  // Translation
  bleuScore: number;
  meteorScore: number;

  // Performance
  averageLatency: number;
  throughput: number;  // requests per second
}

/**
 * Track entity extraction quality
 */
export function calculateEntityMetrics(
  predictions: ExtractedEntity[][],
  groundTruth: ExtractedEntity[][]
): NLPModelMetrics {
  let totalTruePositives = 0;
  let totalFalsePositives = 0;
  let totalFalseNegatives = 0;

  for (let i = 0; i < predictions.length; i++) {
    const pred = predictions[i];
    const truth = groundTruth[i];

    // Match entities
    const matched = new Set<number>();
    const usedTruth = new Set<number>();

    for (let p = 0; p < pred.length; p++) {
      for (let t = 0; t < truth.length; t++) {
        if (usedTruth.has(t)) continue;

        if (pred[p].type === truth[t].type &&
            pred[p].text.toLowerCase() === truth[t].text.toLowerCase()) {
          totalTruePositives++;
          matched.add(p);
          usedTruth.add(t);
          break;
        }
      }
    }

    totalFalsePositives += pred.length - matched.size;
    totalFalseNegatives += truth.length - usedTruth.size;
  }

  const precision = totalTruePositives / (totalTruePositives + totalFalsePositives);
  const recall = totalTruePositives / (totalTruePositives + totalFalseNegatives);
  const f1 = 2 * (precision * recall) / (precision + recall);

  return {
    entityPrecision: precision,
    entityRecall: recall,
    entityF1: f1,
    entityAccuracy: totalTruePositives / (totalTruePositives + totalFalsePositives + totalFalseNegatives)
  };
}
```

### Business Metrics

```typescript
// metrics/nlp-business-metrics.ts

export interface NLPBusinessMetrics {
  // Extraction impact
  extractionAccuracyByField: Map<string, number>;
  extractionConfidenceDistribution: Map<string, number>;
  manualCorrectionRate: number;

  // Intent classification impact
  correctRoutingRate: number;
  misroutingCost: number;
  firstContactResolution: number;

  // Sentiment impact
  sentimentAlertAccuracy: number;
  escalatedIssuesDetected: number;
  customerSatisfactionCorrelation: number;

  // Translation impact
  translatedConversationSatisfaction: number;
  translationErrorRate: number;
}

/**
 * Track business impact of NLP
 */
export class NLPBusinessTracker {
  /**
   * Track extraction accuracy vs manual corrections
   */
  async trackExtractionQuality(
    extractedEntities: ExtractedEntity[],
    manualCorrections: FieldCorrection[]
  ): Promise<void> {
    for (const correction of manualCorrections) {
      const extracted = extractedEntities.find(
        e => e.type === correction.fieldType
      );

      const wasCorrect = extracted && extracted.value === correction.correctValue;

      await this.metricsStore.record({
        metric: 'entity_extraction_accuracy',
        tags: {
          fieldType: correction.fieldType,
          wasCorrect: wasCorrect.toString()
        },
        value: 1
      });
    }
  }

  /**
   * Track intent classification business impact
   */
  async trackIntentBusinessImpact(
    predictedIntent: TravelIntent,
    actualIntent: TravelIntent,
    outcome: {
      resolved: boolean;
      timeToResolution: number;
      customerSatisfaction: number;
    }
  ): Promise<void> {
    // Track if misrouting occurred
    if (predictedIntent !== actualIntent) {
      await this.metricsStore.record({
        metric: 'intent_misrouting',
        tags: {
          predicted: predictedIntent,
          actual: actualIntent
        },
        value: 1
      });

      // Track cost of misrouting
      await this.metricsStore.record({
        metric: 'misrouting_cost',
        tags: { predicted: predictedIntent, actual: actualIntent },
        value: outcome.timeToResolution
      });
    }

    // Track first contact resolution
    await this.metricsStore.record({
      metric: 'first_contact_resolution',
      tags: {
        intent: actualIntent,
        resolved: outcome.resolved.toString()
      },
      value: outcome.resolved ? 1 : 0
    });
  }
}
```

---

## Summary

This document defines the Natural Language Processing patterns for the Travel Agency Agent platform:

**Key Components:**
- **Named Entity Recognition**: Travel-specific entity extraction with context resolution
- **Intent Classification**: Multi-modal ensemble for accurate intent detection
- **Sentiment Analysis**: Emotion detection and aspect-based sentiment
- **Query Understanding**: Semantic search and natural language query parsing
- **Document Summarization**: Conversation and document summarization
- **Translation**: Multi-language support with context preservation
- **Response Generation**: Template and LLM-based response generation

**Integration Points:**
- Entity extraction feeds into trip packet creation
- Intent classification routes to appropriate workflows
- Sentiment analysis triggers escalation workflows
- Summarization aids agent handoff

**Next:** [AIML_04: AI Operations & Governance](./AIML_04_AI_OPS_GOVERNANCE.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-04-25
**Status:** ✅ Complete
