# AIML_02: Decision Intelligence

> Recommendation engines, prediction models, and optimization algorithms for intelligent decision-making

---

## Document Overview

**Series:** AI/ML Patterns
**Document:** 2 of 4
**Focus:** Decision Intelligence Systems
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Recommendation Engine](#recommendation-engine)
4. [Prediction Models](#prediction-models)
5. [Customer Segmentation](#customer-segmentation)
6. [Dynamic Pricing](#dynamic-pricing)
7. [A/B Testing Framework](#ab-testing-framework)
8. [Optimization Algorithms](#optimization-algorithms)
9. [Model Training Pipeline](#model-training-pipeline)
10. [API Specification](#api-specification)
11. [Testing Scenarios](#testing-scenarios)
12. [Metrics Definitions](#metrics-definitions)

---

## 1. Introduction

### What is Decision Intelligence?

Decision Intelligence combines data science, machine learning, and business logic to make automated recommendations and predictions. In the travel agency context, this includes:

- **Trip suitability scoring** - Matching trips to customer preferences
- **Price prediction** - Forecasting future price trends
- **Recommendation engines** - Suggesting destinations, hotels, activities
- **Customer segmentation** - Grouping customers by behavior/value
- **Dynamic pricing** - Optimizing margins and conversion
- **Churn prediction** - Identifying at-risk customers

### Business Value

| Capability | Impact |
|------------|--------|
| **Suitability Scoring** | Higher conversion, better customer satisfaction |
| **Price Prediction** | Improved booking timing, margin optimization |
| **Personalization** | Increased loyalty, higher repeat rates |
| **Churn Prevention** | Retention revenue, reduced acquisition cost |
| **Dynamic Pricing** | Margin optimization 5-15% |

---

## 2. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Decision Intelligence Layer                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Recommend   │  │ Predict     │  │ Segment     │  │ Dynamic  │  │
│  │ Engine      │  │ Models      │  │ Models      │  │ Pricing  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬─────┘  │
│         │                │                │               │         │
│  ┌──────▼────────────────▼────────────────▼───────────────▼─────┐  │
│  │                 Feature Store & Model Registry              │  │
│  └──────┬──────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │              Training Pipeline & Experiment Tracking          │  │
│  └──────┬──────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │              Data Warehouse & Analytics                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **ML Framework** | scikit-learn, XGBoost, LightGBM |
| **Deep Learning** | PyTorch (for complex models) |
| **Feature Store** | Feast (Google) or custom |
| **Model Registry** | MLflow |
| **Experiment Tracking** | Weights & Biases |
| **Serving** | FastAPI with ONNX runtime |
| **Batch Inference** | Airflow + Docker |

---

## 3. Recommendation Engine

### Types of Recommendations

```typescript
// recommendation/types.ts

export enum RecommendationType {
  DESTINATION = 'destination',      // Where to go
  ACCOMMODATION = 'accommodation',  // Where to stay
  ACTIVITY = 'activity',           // What to do
  TRIP_PACKAGE = 'trip_package',   // Pre-built packages
  UPSSELL = 'upsell',              // Additional services
}

export interface RecommendationRequest {
  customerId: string;
  type: RecommendationType;
  context: RecommendationContext;
  limit?: number;
  excludeIds?: string[];
}

export interface RecommendationContext {
  tripId?: string;
  destination?: string;
  dates?: { start: Date; end: Date };
  budget?: BudgetRange;
  travelers: TravelerProfile;
  preferences?: CustomerPreferences;
}

export interface RecommendationResult {
  items: RecommendedItem[];
  metadata: {
    algorithm: string;
    confidence: number;
    diversity_score: number;
    freshness_score: number;
  };
}

export interface RecommendedItem {
  entityId: string;
  type: RecommendationType;
  score: number;
  confidence: number;
  reasoning: string[];
  price?: PriceEstimate;
  availability?: AvailabilityInfo;
}
```

### Collaborative Filtering

```typescript
// recommendation/algorithms/collaborative.ts

/**
 * User-based collaborative filtering
 * Finds similar users and recommends their liked items
 */
export class UserBasedCollaborativeFiltering {
  private similarityMatrix: Map<string, Map<string, number>>;
  private userItemMatrix: Map<string, Map<string, number>>;

  /**
   * Compute user similarity using cosine similarity
   */
  private computeUserSimilarity(user1: string, user2: string): number {
    const items1 = this.userItemMatrix.get(user1) || new Map();
    const items2 = this.userItemMatrix.get(user2) || new Map();

    // Find common items
    const commonItems: string[] = [];
    for (const item of items1.keys()) {
      if (items2.has(item)) {
        commonItems.push(item);
      }
    }

    if (commonItems.length === 0) return 0;

    // Cosine similarity
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (const item of commonItems) {
      const rating1 = items1.get(item)!;
      const rating2 = items2.get(item)!;
      dotProduct += rating1 * rating2;
      norm1 += rating1 * rating1;
      norm2 += rating2 * rating2;
    }

    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }

  /**
   * Get recommendations for a user
   */
  async recommend(
    userId: string,
    options: { limit: number; minSimilarity: number }
  ): Promise<RecommendedItem[]> {
    const similarUsers = this.findSimilarUsers(userId, options.minSimilarity);
    const recommendations = new Map<string, { score: number; count: number }>();

    // Aggregate recommendations from similar users
    for (const [similarUser, similarity] of similarUsers) {
      const theirItems = this.userItemMatrix.get(similarUser) || new Map();
      const userItems = this.userItemMatrix.get(userId) || new Map();

      for (const [itemId, rating] of theirItems) {
        // Skip items the user already interacted with
        if (userItems.has(itemId)) continue;

        const current = recommendations.get(itemId) || { score: 0, count: 0 };
        recommendations.set(itemId, {
          score: current.score + similarity * rating,
          count: current.count + 1
        });
      }
    }

    // Normalize by count and sort
    return Array.from(recommendations.entries())
      .map(([itemId, data]) => ({
        entityId: itemId,
        type: RecommendationType.DESTINATION,
        score: data.score / data.count,
        confidence: Math.min(data.count / similarUsers.length, 1),
        reasoning: [
          `${data.count} similar travelers enjoyed this`,
          `Based on your travel history patterns`
        ]
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, options.limit);
  }
}

/**
 * Item-based collaborative filtering
 * Finds similar items to what the user liked
 */
export class ItemBasedCollaborativeFiltering {
  private itemSimilarityMatrix: Map<string, Map<string, number>>;

  async recommend(
    userId: string,
    userLikedItems: string[],
    options: { limit: number }
  ): Promise<RecommendedItem[]> {
    const scores = new Map<string, number>();

    // For each item the user liked, find similar items
    for (const likedItem of userLikedItems) {
      const similarItems = this.itemSimilarityMatrix.get(likedItem) || new Map();

      for (const [itemId, similarity] of similarItems) {
        // Skip items the user already knows
        if (userLikedItems.includes(itemId)) continue;

        const current = scores.get(itemId) || 0;
        scores.set(itemId, current + similarity);
      }
    }

    return Array.from(scores.entries())
      .map(([itemId, score]) => ({
        entityId: itemId,
        type: RecommendationType.DESTINATION,
        score,
        confidence: Math.min(score / userLikedItems.length, 1),
        reasoning: ['Similar to places you enjoyed']
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, options.limit);
  }
}
```

### Content-Based Filtering

```typescript
// recommendation/algorithms/content-based.ts

export interface DestinationFeatures {
  entityId: string;
  category: string[];          // beach, mountain, city, cultural
  activities: string[];        // hiking, nightlife, shopping
  climate: string;             // tropical, temperate, cold
  budgetLevel: number;         // 1-5, from budget to luxury
  seasonality: string[];       // best months to visit
  vibe: string[];              // romantic, family, adventure
  accessibility: number;       // ease of travel 1-5
}

export class ContentBasedRecommender {
  private destinationFeatures: Map<string, DestinationFeatures>;
  private userProfile: Map<string, UserProfile>;

  /**
   * Compute feature similarity using weighted cosine similarity
   */
  private computeFeatureSimilarity(
    features1: Record<string, number>,
    features2: Record<string, number>,
    weights: Record<string, number>
  ): number {
    const allFeatures = new Set([
      ...Object.keys(features1),
      ...Object.keys(features2)
    ]);

    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (const feature of allFeatures) {
      const val1 = features1[feature] || 0;
      const val2 = features2[feature] || 0;
      const weight = weights[feature] || 1;

      dotProduct += weight * val1 * val2;
      norm1 += weight * val1 * val1;
      norm2 += weight * val2 * val2;
    }

    if (norm1 === 0 || norm2 === 0) return 0;
    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }

  /**
   * Build user profile from past trips
   */
  private buildUserProfile(userId: string): UserProfile {
    const userTrips = this.getUserTrips(userId);
    const profile: UserProfile = {
      preferredCategories: new Map<string, number>(),
      preferredActivities: new Map<string, number>(),
      avgBudgetLevel: 0,
      preferredClimate: new Map<string, number>(),
      preferredVibe: new Map<string, number>()
    };

    for (const trip of userTrips) {
      const features = this.destinationFeatures.get(trip.destinationId);
      if (!features) continue;

      // Aggregate preferences from ratings
      const rating = trip.rating || 3;

      for (const category of features.category) {
        const current = profile.preferredCategories.get(category) || 0;
        profile.preferredCategories.set(category, current + rating);
      }

      for (const activity of features.activities) {
        const current = profile.preferredActivities.get(activity) || 0;
        profile.preferredActivities.set(activity, current + rating);
      }

      profile.avgBudgetLevel =
        (profile.avgBudgetLevel + features.budgetLevel) / 2;
    }

    return profile;
  }

  /**
   * Get content-based recommendations
   */
  async recommend(
    userId: string,
    options: { limit: number; excludeIds: string[] }
  ): Promise<RecommendedItem[]> {
    const profile = this.buildUserProfile(userId);
    const candidateDestinations = this.getCandidateDestinations(options.excludeIds);

    const scores = candidateDestinations.map(destination => {
      const features = this.destinationFeatures.get(destination.id)!;

      // Convert profile to feature vector
      const profileFeatures: Record<string, number> = {};
      for (const [cat, score] of profile.preferredCategories) {
        profileFeatures[`cat_${cat}`] = score;
      }
      for (const [act, score] of profile.preferredActivities) {
        profileFeatures[`act_${act}`] = score;
      }
      profileFeatures['budget'] = profile.avgBudgetLevel;

      // Convert destination to feature vector
      const destFeatures: Record<string, number> = {};
      for (const cat of features.category) {
        destFeatures[`cat_${cat}`] = 1;
      }
      for (const act of features.activities) {
        destFeatures[`act_${act}`] = 1;
      }
      destFeatures['budget'] = features.budgetLevel;

      // Weighted similarity
      const weights = {
        budget: 0.5,  // Budget mismatch is less important
        default: 1
      };

      const similarity = this.computeFeatureSimilarity(
        profileFeatures,
        destFeatures,
        weights
      );

      return {
        entityId: destination.id,
        type: RecommendationType.DESTINATION,
        score: similarity,
        confidence: 0.8,
        reasoning: this.generateReasoning(features, profile)
      };
    });

    return scores
      .filter(s => s.score > 0.3)
      .sort((a, b) => b.score - a.score)
      .slice(0, options.limit);
  }

  private generateReasoning(
    features: DestinationFeatures,
    profile: UserProfile
  ): string[] {
    const reasons: string[] = [];

    // Check category matches
    for (const category of features.category) {
      if (profile.preferredCategories.get(category)! > 5) {
        reasons.push(`Matches your interest in ${category} destinations`);
        break;
      }
    }

    // Check activity matches
    const matchedActivities: string[] = [];
    for (const activity of features.activities) {
      if (profile.preferredActivities.get(activity)! > 5) {
        matchedActivities.push(activity);
      }
    }
    if (matchedActivities.length > 0) {
      reasons.push(`Offers ${matchedActivities.join(', ')} activities you enjoy`);
    }

    // Check budget alignment
    if (Math.abs(features.budgetLevel - profile.avgBudgetLevel) <= 1) {
      reasons.push('Fits your typical budget range');
    }

    return reasons;
  }
}
```

### Hybrid Recommendation Engine

```typescript
// recommendation/engine.ts

export class HybridRecommendationEngine {
  private collaborative: UserBasedCollaborativeFiltering;
  private itemBased: ItemBasedCollaborativeFiltering;
  private contentBased: ContentBasedRecommender;
  private popularityRecommender: PopularityRecommender;

  /**
   * Combine multiple algorithms with learned weights
   */
  async recommend(
    request: RecommendationRequest
  ): Promise<RecommendationResult> {
    const algorithms: Array<{
      name: string;
      weight: number;
      results: RecommendedItem[];
    }> = [];

    // Get results from each algorithm
    const userHistory = await this.getUserHistory(request.customerId);
    const hasHistory = userHistory.length > 0;

    if (hasHistory) {
      algorithms.push({
        name: 'collaborative',
        weight: 0.4,
        results: await this.collaborative.recommend(request.customerId, {
          limit: request.limit || 10,
          minSimilarity: 0.3
        })
      });

      algorithms.push({
        name: 'item_based',
        weight: 0.25,
        results: await this.itemBased.recommend(
          request.customerId,
          userHistory.map(h => h.destinationId),
          { limit: request.limit || 10 }
        )
      });

      algorithms.push({
        name: 'content',
        weight: 0.25,
        results: await this.contentBased.recommend(request.customerId, {
          limit: request.limit || 10,
          excludeIds: request.excludeIds
        })
      });
    }

    // Add popularity for cold start or diversity
    algorithms.push({
      name: 'popularity',
      weight: hasHistory ? 0.1 : 1.0,
      results: await this.popularityRecommender.recommend({
        limit: request.limit || 10,
        context: request.context
      })
    });

    // Combine scores
    const combinedScores = this.combineScores(algorithms);

    // Apply diversity and freshness
    const diversified = this.applyDiversification(combinedScores, {
      diversityThreshold: 0.3,
      freshnessBoost: 0.1
    });

    return {
      items: diversified.slice(0, request.limit || 10),
      metadata: {
        algorithm: 'hybrid',
        confidence: this.computeOverallConfidence(algorithms),
        diversity_score: this.computeDiversityScore(diversified),
        freshness_score: this.computeFreshnessScore(diversified)
      }
    };
  }

  private combineScores(
    algorithms: Array<{ name: string; weight: number; results: RecommendedItem[] }>
  ): RecommendedItem[] {
    const itemScores = new Map<string, {
      totalScore: number;
      totalWeight: number;
      sources: string[];
      reasoning: Set<string>;
    }>();

    for (const algo of algorithms) {
      for (const item of algo.results) {
        const current = itemScores.get(item.entityId) || {
          totalScore: 0,
          totalWeight: 0,
          sources: [],
          reasoning: new Set()
        };

        itemScores.set(item.entityId, {
          totalScore: current.totalScore + item.score * algo.weight,
          totalWeight: current.totalWeight + algo.weight,
          sources: [...current.sources, algo.name],
          reasoning: new Set([...current.reasoning, ...item.reasoning])
        });
      }
    }

    return Array.from(itemScores.entries())
      .map(([entityId, data]) => ({
        entityId,
        type: RecommendationType.DESTINATION,
        score: data.totalScore / data.totalWeight,
        confidence: Math.min(data.totalWeight, 1),
        reasoning: Array.from(data.reasoning)
      }))
      .sort((a, b) => b.score - a.score);
  }

  /**
   * Maximal Marginal Relevance (MMR) for diversification
   */
  private applyDiversification(
    items: RecommendedItem[],
    options: { diversityThreshold: number; freshnessBoost: number }
  ): RecommendedItem[] {
    const selected: RecommendedItem[] = [];
    const remaining = [...items];

    // Select highest scored item first
    selected.push(remaining.shift()!);

    while (remaining.length > 0 && selected.length < items.length) {
      let bestIndex = 0;
      let bestScore = -Infinity;

      for (let i = 0; i < remaining.length; i++) {
        const item = remaining[i];

        // Relevance score
        const relevance = item.score;

        // Diversity penalty (similarity to already selected)
        const similarity = this.maxSimilarityToSelected(item, selected);
        const diversity = 1 - similarity;

        // Freshness boost
        const freshness = this.getFreshnessScore(item.entityId);

        // MMR score
        const mmrScore =
          (1 - options.diversityThreshold) * relevance +
          options.diversityThreshold * diversity +
          options.freshnessBoost * freshness;

        if (mmrScore > bestScore) {
          bestScore = mmrScore;
          bestIndex = i;
        }
      }

      selected.push(remaining.splice(bestIndex, 1)[0]);
    }

    return selected;
  }

  private maxSimilarityToSelected(
    item: RecommendedItem,
    selected: RecommendedItem[]
  ): number {
    // Simplified: use category similarity
    let maxSim = 0;
    for (const s of selected) {
      const sim = this.computeItemSimilarity(item.entityId, s.entityId);
      maxSim = Math.max(maxSim, sim);
    }
    return maxSim;
  }
}
```

---

## 4. Prediction Models

### Price Prediction Model

```typescript
// prediction/price-predictor.ts

export interface PricePredictionRequest {
  destinationId: string;
  accommodationId?: string;
  departureDate: Date;
  duration: number;
  roomType?: string;
  occupancy: number;
  includeFlight?: boolean;
}

export interface PricePrediction {
  predictedPrice: PriceEstimate;
  confidence: number;
  trend: 'rising' | 'stable' | 'falling';
  recommendation: 'book_now' | 'wait' | 'neutral';
  reasoning: string[];
  historicalPrices: HistoricalPricePoint[];
  forecast: PriceForecast[];
}

export interface HistoricalPricePoint {
  date: Date;
  price: number;
  source: 'actual' | 'estimated';
}

export interface PriceForecast {
  date: Date;
  predictedPrice: number;
  confidenceInterval: [number, number];
}

/**
 * Price prediction using XGBoost
 */
export class PricePredictor {
  private model: XGBoostModel;
  private featureStore: FeatureStore;

  /**
   * Extract features for price prediction
   */
  private extractFeatures(request: PricePredictionRequest): Record<string, number> {
    const departureDate = new Date(request.departureDate);
    const today = new Date();
    const daysUntilDeparture = Math.floor(
      (departureDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    );

    return {
      // Temporal features
      days_until_departure: daysUntilDeparture,
      month: departureDate.getMonth(),
      day_of_week: departureDate.getDay(),
      is_weekend: departureDate.getDay() >= 5 ? 1 : 0,
      is_holiday_season: this.isHolidaySeason(departureDate) ? 1 : 0,

      // Duration features
      duration: request.duration,
      duration_squared: request.duration * request.duration,

      // Occupancy
      occupancy: request.occupancy,
      occupancy_per_room: request.occupancy / this.getRoomCount(request.occupancy),

      // Seasonality
      season: this.getSeason(departureDate),
      is_peak_season: this.isPeakSeason(request.destinationId, departureDate) ? 1 : 0,
      is_off_peak: this.isOffPeak(request.destinationId, departureDate) ? 1 : 0,

      // Demand indicators
      demand_score: this.getDemandScore(request.destinationId, departureDate),
      competition_score: this.getCompetitionScore(request.destinationId),

      // Historical price trend
      price_trend_7d: this.getPriceTrend(request.destinationId, 7),
      price_trend_30d: this.getPriceTrend(request.destinationId, 30),

      // Destination characteristics
      destination_popularity: this.getDestinationPopularity(request.destinationId),
      destination_luxury_index: this.getLuxuryIndex(request.destinationId)
    };
  }

  /**
   * Generate price prediction with forecast
   */
  async predict(request: PricePredictionRequest): Promise<PricePrediction> {
    const features = this.extractFeatures(request);

    // Get base prediction
    const predictedPrice = await this.model.predict(features);

    // Get confidence from model (if available) or estimate
    const confidence = await this.estimateConfidence(features);

    // Determine trend
    const trend = await this.determineTrend(request.destinationId, request.departureDate);

    // Generate recommendation
    const recommendation = this.generateRecommendation(predictedPrice, trend, confidence);

    // Get historical prices
    const historicalPrices = await this.getHistoricalPrices(
      request.destinationId,
      request.departureDate
    );

    // Generate forecast
    const forecast = await this.generateForecast(request);

    return {
      predictedPrice: {
        amount: predictedPrice,
        currency: 'USD',
        breakdown: this.getPriceBreakdown(predictedPrice, request)
      },
      confidence,
      trend,
      recommendation,
      reasoning: this.generateReasoning(trend, confidence, features),
      historicalPrices,
      forecast
    };
  }

  private generateRecommendation(
    predictedPrice: number,
    trend: string,
    confidence: number
  ): 'book_now' | 'wait' | 'neutral' {
    if (confidence < 0.6) return 'neutral';

    if (trend === 'rising' && confidence > 0.7) {
      return 'book_now';
    } else if (trend === 'falling' && confidence > 0.7) {
      return 'wait';
    }
    return 'neutral';
  }

  private async generateForecast(
    request: PricePredictionRequest
  ): Promise<PriceForecast[]> {
    const forecast: PriceForecast[] = [];
    const startDate = new Date(request.departureDate);

    // Forecast for next 30 days
    for (let i = 0; i < 30; i += 3) {
      const forecastDate = new Date(startDate);
      forecastDate.setDate(startDate.getDate() + i);

      const features = this.extractFeatures({
        ...request,
        departureDate: forecastDate
      });

      const predictedPrice = await this.model.predict(features);
      const stdError = await this.estimateStandardError(features);

      forecast.push({
        date: forecastDate,
        predictedPrice,
        confidenceInterval: [
          predictedPrice - 1.96 * stdError,
          predictedPrice + 1.96 * stdError
        ]
      });
    }

    return forecast;
  }
}
```

### Suitability Scoring Model

```typescript
// prediction/suitability-scorer.ts

export interface SuitabilityRequest {
  customerId: string;
  tripDetails: TripDetails;
  customerPreferences?: CustomerPreferences;
}

export interface TripDetails {
  destinationId: string;
  accommodationId?: string;
  startDate: Date;
  endDate: Date;
  activities: string[];
  budget: BudgetRange;
  travelers: TravelerProfile[];
}

export interface SuitabilityScore {
  overallScore: number;  // 0-100
  confidence: number;
  breakdown: ScoreBreakdown;
  concerns: SuitabilityConcern[];
  recommendations: string[];
  alternatives?: AlternativeSuggestion[];
}

export interface ScoreBreakdown {
  budgetMatch: number;
  destinationMatch: number;
  timingMatch: number;
  activityMatch: number;
  accommodationMatch: number;
  travelerMatch: number;
}

export interface SuitabilityConcern {
  severity: 'low' | 'medium' | 'high';
  category: string;
  description: string;
  mitigation?: string;
}

/**
 * Multi-factor suitability scoring
 */
export class SuitabilityScorer {
  private customerModel: CustomerProfileModel;
  private destinationModel: DestinationModel;
  private pricingModel: PricingModel;

  async score(request: SuitabilityRequest): Promise<SuitabilityScore> {
    // Get customer profile
    const customerProfile = await this.customerModel.getProfile(request.customerId);

    // Get destination characteristics
    const destination = await this.destinationModel.getDestination(
      request.tripDetails.destinationId
    );

    // Score each dimension
    const budgetScore = this.scoreBudget(
      request.tripDetails.budget,
      customerProfile,
      destination
    );

    const destinationScore = this.scoreDestination(
      destination,
      customerProfile.preferences
    );

    const timingScore = this.scoreTiming(
      request.tripDetails.startDate,
      request.tripDetails.endDate,
      customerProfile
    );

    const activityScore = this.scoreActivities(
      request.tripDetails.activities,
      customerProfile.preferences
    );

    const accommodationScore = await this.scoreAccommodation(
      request.tripDetails.accommodationId,
      customerProfile
    );

    const travelerScore = this.scoreTravelers(
      request.tripDetails.travelers,
      destination
    );

    // Weighted combination
    const weights = this.getWeights(customerProfile.segment);
    const overallScore =
      budgetScore * weights.budget +
      destinationScore * weights.destination +
      timingScore * weights.timing +
      activityScore * weights.activity +
      accommodationScore * weights.accommodation +
      travelerScore * weights.traveler;

    return {
      overallScore: Math.round(overallScore * 100),
      confidence: this.computeConfidence(customerProfile.dataQuality),
      breakdown: {
        budgetMatch: Math.round(budgetScore * 100),
        destinationMatch: Math.round(destinationScore * 100),
        timingMatch: Math.round(timingScore * 100),
        activityMatch: Math.round(activityScore * 100),
        accommodationMatch: Math.round(accommodationScore * 100),
        travelerMatch: Math.round(travelerScore * 100)
      },
      concerns: this.identifyConcerns({
        budgetScore,
        destinationScore,
        timingScore,
        activityScore,
        accommodationScore,
        travelerScore
      }),
      recommendations: this.generateRecommendations(request, customerProfile),
      alternatives: this.findAlternatives(request, customerProfile)
    };
  }

  private scoreBudget(
    tripBudget: BudgetRange,
    customer: CustomerProfile,
    destination: Destination
  ): number {
    // Estimate trip cost
    const estimatedCost = this.pricingModel.estimateCost({
      destination,
      duration: this.calculateDuration(tripBudget),
      travelers: customer.travelerProfile
    });

    // Compare with budget
    const budgetMidpoint = (tripBudget.min + tripBudget.max) / 2;

    if (estimatedCost > tripBudget.max) {
      // Over budget - score drops proportionally
      const overage = (estimatedCost - tripBudget.max) / tripBudget.max;
      return Math.max(0, 1 - overage * 2);
    } else if (estimatedCost < tripBudget.min) {
      // Under budget - could suggest upgrades
      const surplus = (tripBudget.min - estimatedCost) / tripBudget.min;
      return 1 - surplus * 0.3;  // Small penalty for being too far under
    } else {
      // Within budget
      return 1;
    }
  }

  private scoreDestination(
    destination: Destination,
    preferences: CustomerPreferences
  ): number {
    let score = 0;
    let totalWeight = 0;

    // Category preference
    for (const [category, preference] of Object.entries(preferences.categories)) {
      if (destination.categories.includes(category)) {
        score += preference;
      }
      totalWeight += 5;  // Max preference value
    }

    // Vibe preference
    for (const [vibe, preference] of Object.entries(preferences.vibes)) {
      if (destination.vibes.includes(vibe)) {
        score += preference;
      }
      totalWeight += 5;
    }

    // Climate preference
    if (preferences.climate?.includes(destination.climate)) {
      score += 10;
    }
    totalWeight += 10;

    return totalWeight > 0 ? score / totalWeight : 0.5;
  }

  private identifyConcerns(scores: {
    budgetScore: number;
    destinationScore: number;
    timingScore: number;
    activityScore: number;
    accommodationScore: number;
    travelerScore: number;
  }): SuitabilityConcern[] {
    const concerns: SuitabilityConcern[] = [];

    if (scores.budgetScore < 0.5) {
      concerns.push({
        severity: scores.budgetScore < 0.3 ? 'high' : 'medium',
        category: 'budget',
        description: 'This trip may exceed your budget',
        mitigation: 'Consider adjusting travel dates or accommodation level'
      });
    }

    if (scores.timingScore < 0.5) {
      concerns.push({
        severity: 'medium',
        category: 'timing',
        description: 'Weather may not be ideal during this period',
        mitigation: 'Consider shifting dates by a few weeks'
      });
    }

    if (scores.travelerScore < 0.5) {
      concerns.push({
        severity: 'high',
        category: 'travelers',
        description: 'This destination may not suit all travelers in your group',
        mitigation: 'Review accessibility and activity requirements'
      });
    }

    return concerns;
  }
}
```

### Churn Prediction Model

```typescript
// prediction/churn-predictor.ts

export interface ChurnPredictionResult {
  churnProbability: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  keyFactors: ChurnFactor[];
  recommendedActions: string[];
  predictedLifespan: number;  // months until expected churn
}

export interface ChurnFactor {
  factor: string;
  impact: number;
  description: string;
}

/**
 * Customer churn prediction using survival analysis
 */
export class ChurnPredictor {
  private survivalModel: CoxProportionalHazardsModel;
  private featureStore: FeatureStore;

  async predict(customerId: string): Promise<ChurnPredictionResult> {
    // Get customer features
    const features = await this.extractChurnFeatures(customerId);

    // Predict churn probability in next 3 months
    const churnProbability = await this.survivalModel.predictChurnProbability(
      features,
      90  // days
    );

    // Get SHAP values for explainability
    const shapValues = await this.survivalModel.getSHAPValues(features);

    // Identify key factors
    const keyFactors = this.identifyKeyFactors(shapValues, features);

    // Generate recommended actions
    const recommendedActions = this.generateRecommendedActions(keyFactors);

    // Predict customer lifespan
    const predictedLifespan = await this.survivalModel.predictSurvivalTime(features);

    return {
      churnProbability,
      riskLevel: this.categorizeRisk(churnProbability),
      keyFactors,
      recommendedActions,
      predictedLifespan: Math.round(predictedLifespan / 30)  // convert to months
    };
  }

  private async extractChurnFeatures(customerId: string): Promise<ChurnFeatures> {
    const customer = await this.featureStore.getCustomer(customerId);
    const bookings = await this.featureStore.getCustomerBookings(customerId);
    const interactions = await this.featureStore.getCustomerInteractions(customerId);

    // Recency features
    const lastBookingDate = bookings[0]?.createdAt || new Date(0);
    const daysSinceLastBooking = this.daysSince(lastBookingDate);
    const lastInteractionDate = interactions[0]?.timestamp || new Date(0);
    const daysSinceLastInteraction = this.daysSince(lastInteractionDate);

    // Frequency features
    const bookingsLast12m = this.countBookingsInPeriod(bookings, 365);
    const bookingsLast6m = this.countBookingsInPeriod(bookings, 180);
    const avgDaysBetweenBookings = this.calculateAvgDaysBetweenBookings(bookings);

    // Monetary features
    const totalSpent = bookings.reduce((sum, b) => sum + b.totalAmount, 0);
    const avgBookingValue = totalSpent / bookings.length;
    const spendingTrend = this.calculateSpendingTrend(bookings);

    // Engagement features
    const emailOpenRate = this.calculateEmailOpenRate(interactions);
    const responseRate = this.calculateResponseRate(interactions);
    const supportTickets = this.countSupportTickets(interactions);

    // Satisfaction features
    const avgRating = this.calculateAverageRating(bookings);
    const negativeReviews = this.countNegativeReviews(bookings);

    return {
      // Recency
      days_since_last_booking: daysSinceLastBooking,
      days_since_last_interaction: daysSinceLastInteraction,

      // Frequency
      bookings_last_12m: bookingsLast12m,
      bookings_last_6m: bookingsLast6m,
      avg_days_between_bookings: avgDaysBetweenBookings,

      // Monetary
      total_spent: totalSpent,
      avg_booking_value: avgBookingValue,
      spending_trend: spendingTrend,

      // Engagement
      email_open_rate: emailOpenRate,
      response_rate: responseRate,
      support_tickets: supportTickets,

      // Satisfaction
      avg_rating: avgRating,
      negative_reviews: negativeReviews,

      // Tenure
      customer_tenure_days: this.daysSince(customer.createdAt),

      // Demographics
      customer_segment: customer.segment,
      is_business: customer.isBusiness ? 1 : 0
    };
  }

  private categorizeRisk(probability: number): 'low' | 'medium' | 'high' | 'critical' {
    if (probability < 0.2) return 'low';
    if (probability < 0.4) return 'medium';
    if (probability < 0.6) return 'high';
    return 'critical';
  }

  private generateRecommendedActions(factors: ChurnFactor[]): string[] {
    const actions: string[] = [];

    for (const factor of factors.filter(f => f.impact > 0.1)) {
      switch (factor.factor) {
        case 'days_since_last_booking':
          actions.push('Send personalized re-engagement offer');
          actions.push('Schedule agent outreach call');
          break;
        case 'low_email_open_rate':
          actions.push('Review email content and timing');
          actions.push('Try alternative communication channels');
          break;
        case 'declining_spend':
          actions.push('Offer exclusive discount or upgrade');
          actions.push('Share personalized trip recommendations');
          break;
        case 'negative_reviews':
          actions.push('Address service concerns directly');
          actions.push('Offer service recovery package');
          break;
        case 'low_engagement':
          actions.push('Send personalized destination inspiration');
          actions.push('Invite to exclusive event or webinar');
          break;
      }
    }

    return actions;
  }
}
```

---

## 5. Customer Segmentation

### Segmentation Models

```typescript
// segmentation/customer-segmenter.ts

export enum SegmentType {
  RFM = 'rfm',                    // Recency, Frequency, Monetary
  BEHAVIORAL = 'behavioral',       // Based on travel behaviors
  DEMOGRAPHIC = 'demographic',     // Age, location, family
  LIFESTAGE = 'lifestage',         // Life stage based
  VALUE_BASED = 'value_based',     // Customer lifetime value
  PERSONA = 'persona'              // Travel persona based
}

export interface CustomerSegment {
  segmentId: string;
  name: string;
  type: SegmentType;
  size: number;
  percentage: number;
  characteristics: SegmentCharacteristics;
  typicalBehaviors: string[];
  recommendedStrategies: string[];
}

export interface SegmentCharacteristics {
  avgBookingValue: number;
  avgBookingsPerYear: number;
  avgTripDuration: number;
  preferredDestinations: string[];
  preferredTravelMonths: number[];
  commonAttributes: Record<string, any>;
}

/**
 * RFM Segmentation (Recency, Frequency, Monetary)
 */
export class RFMSegmenter {
  private rfmScores: Map<string, { r: number; f: number; m: number }>;

  /**
   * Calculate RFM scores for all customers
   */
  async calculateRFM(customers: string[]): Promise<void> {
    for (const customerId of customers) {
      const bookings = await this.getCustomerBookings(customerId);

      // Recency: Days since last booking (higher = better)
      const lastBooking = bookings[0];
      const recencyDays = lastBooking
        ? this.daysSince(lastBooking.createdAt)
        : 9999;

      // Frequency: Number of bookings in last 12 months
      const frequency = this.countBookingsInPeriod(bookings, 365);

      // Monetary: Total spend in last 12 months
      const monetary = this.calculateMonetary(bookings, 365);

      // Score each dimension (1-5, 5 is best)
      const rScore = this.scoreRecency(recencyDays);
      const fScore = this.scoreFrequency(frequency);
      const mScore = this.scoreMonetary(monetary);

      this.rfmScores.set(customerId, { r: rScore, f: fScore, m: mScore });
    }
  }

  /**
   * Assign segments based on RFM scores
   */
  assignSegments(customerId: string): CustomerSegment[] {
    const rfm = this.rfmScores.get(customerId);
    if (!rfm) return [];

    const segments: CustomerSegment[] = [];

    // Champions: Recent, frequent, high spenders
    if (rfm.r >= 4 && rfm.f >= 4 && rfm.m >= 4) {
      segments.push({
        segmentId: 'champions',
        name: 'Champions',
        type: SegmentType.RFM,
        size: 0,
        percentage: 0,
        characteristics: this.getChampionCharacteristics(),
        typicalBehaviors: [
          'Books multiple trips per year',
          'High average spend',
          'Very engaged with communications',
          'Refers new customers'
        ],
        recommendedStrategies: [
          'Offer exclusive experiences',
          'Provide early access to deals',
          'Create loyalty program',
          'Ask for referrals'
        ]
      });
    }

    // Loyal Customers: Good frequency and monetary, moderate recency
    if (rfm.f >= 4 && rfm.m >= 3 && rfm.r >= 3) {
      segments.push({
        segmentId: 'loyal',
        name: 'Loyal Customers',
        type: SegmentType.RFM,
        size: 0,
        percentage: 0,
        characteristics: this.getLoyalCharacteristics(),
        typicalBehaviors: [
          'Consistent booking pattern',
          'Prefers specific destinations',
          'Responsive to promotions'
        ],
        recommendedStrategies: [
          'Personalized recommendations',
          'Loyalty rewards',
          'Cross-sell related services'
        ]
      });
    }

    // At Risk: Previously good, but recent activity dropped
    if (rfm.r <= 2 && rfm.f >= 3 && rfm.m >= 3) {
      segments.push({
        segmentId: 'at_risk',
        name: 'At Risk',
        type: SegmentType.RFM,
        size: 0,
        percentage: 0,
        characteristics: this.getAtRiskCharacteristics(),
        typicalBehaviors: [
          'Previously frequent booker',
          'Haven\'t booked in 6+ months',
          'May be using competitors'
        ],
        recommendedStrategies: [
          'Re-engagement campaign',
          'Special offers',
          'Personalized outreach',
          'Feedback survey'
        ]
      });
    }

    // Hibernating: Past customers, low recent activity
    if (rfm.r <= 2 && rfm.f <= 2) {
      segments.push({
        segmentId: 'hibernating',
        name: 'Hibernating',
        type: SegmentType.RFM,
        size: 0,
        percentage: 0,
        characteristics: this.getHibernatingCharacteristics(),
        typicalBehaviors: [
          'Infrequent booker',
          'Long time since last trip',
          'Low engagement'
        ],
        recommendedStrategies: [
          'Limited-time offers',
          'Destination inspiration',
          'Low-friction re-engagement'
        ]
      });
    }

    // New Customers: Recent first-time bookers
    if (rfm.r >= 4 && rfm.f <= 2) {
      segments.push({
        segmentId: 'new',
        name: 'New Customers',
        type: SegmentType.RFM,
        size: 0,
        percentage: 0,
        characteristics: this.getNewCustomerCharacteristics(),
        typicalBehaviors: [
          'First or second booking',
          'Still building relationship',
          'High potential'
        ],
        recommendedStrategies: [
          'Onboarding sequence',
          'First-trip satisfaction check',
          'Incentivize second booking',
          'Build preference profile'
        ]
      });
    }

    return segments;
  }

  private scoreRecency(days: number): number {
    if (days <= 30) return 5;
    if (days <= 60) return 4;
    if (days <= 90) return 3;
    if (days <= 180) return 2;
    return 1;
  }

  private scoreFrequency(count: number): number {
    if (count >= 4) return 5;
    if (count >= 3) return 4;
    if (count >= 2) return 3;
    if (count >= 1) return 2;
    return 1;
  }

  private scoreMonetary(amount: number): number {
    // Percentile-based scoring
    const percentiles = this.getMonetaryPercentiles();
    if (amount >= percentiles.p80) return 5;
    if (amount >= percentiles.p60) return 4;
    if (amount >= percentiles.p40) return 3;
    if (amount >= percentiles.p20) return 2;
    return 1;
  }
}

/**
 * K-Means Clustering for behavioral segmentation
 */
export class BehavioralSegmenter {
  private kmeans: KMeansModel;

  /**
   * Train behavioral segmentation model
   */
  async train(customers: string[]): Promise<void> {
    const features: number[][] = [];

    for (const customerId of customers) {
      const behavior = await this.extractBehavioralFeatures(customerId);
      features.push(Object.values(behavior));
    }

    // Normalize features
    const normalized = this.normalizeFeatures(features);

    // Train K-Means with optimal K (determined by elbow method)
    const optimalK = await this.findOptimalK(normalized);
    this.kmeans = new KMeansModel({ k: optimalK });
    await this.kmeans.train(normalized);
  }

  /**
   * Extract behavioral features for segmentation
   */
  private async extractBehavioralFeatures(
    customerId: string
  ): Promise<Record<string, number>> {
    const bookings = await this.getCustomerBookings(customerId);
    const interactions = await this.getCustomerInteractions(customerId);

    return {
      // Booking patterns
      avg_booking_window: this.avgBookingWindow(bookings),
      avg_trip_duration: this.avgTripDuration(bookings),
      international_ratio: this.internationalRatio(bookings),
      last_minute_ratio: this.lastMinuteRatio(bookings),

      // Destination preferences
      beach_preference: this.destinationCategoryPreference(bookings, 'beach'),
      city_preference: this.destinationCategoryPreference(bookings, 'city'),
      adventure_preference: this.destinationCategoryPreference(bookings, 'adventure'),
      cultural_preference: this.destinationCategoryPreference(bookings, 'cultural'),

      // Travel style
      luxury_ratio: this.luxuryRatio(bookings),
      budget_ratio: this.budgetRatio(bookings),
      solo_travel_ratio: this.soloTravelRatio(bookings),
      family_travel_ratio: this.familyTravelRatio(bookings),

      // Engagement
      email_engagement: this.emailEngagementScore(interactions),
      mobile_app_usage: this.mobileAppUsageScore(interactions),
      communication_preference: this.communicationPreference(interactions)  // 0-1
    };
  }

  /**
   * Assign behavioral segment to customer
   */
  async assignSegment(customerId: string): Promise<CustomerSegment> {
    const features = await this.extractBehavioralFeatures(customerId);
    const cluster = await this.kmeans.predict(Object.values(features));

    return this.getClusterSegment(cluster);
  }

  private getClusterSegment(clusterId: number): CustomerSegment {
    // Pre-defined segment interpretations
    const segments: Record<number, CustomerSegment> = {
      0: {
        segmentId: 'luxury_seeker',
        name: 'Luxury Seekers',
        type: SegmentType.BEHAVIORAL,
        size: 0,
        percentage: 0,
        characteristics: {
          avgBookingValue: 5000,
          avgBookingsPerYear: 2,
          avgTripDuration: 10,
          preferredDestinations: ['Maldives', 'Santorini', 'Bora Bora'],
          preferredTravelMonths: [6, 7, 12, 1],
          commonAttributes: { luxury_ratio: 0.9 }
        },
        typicalBehaviors: [
          'Books premium accommodations',
          'Values experiences over savings',
          'Prefers all-inclusive packages'
        ],
        recommendedStrategies: [
          'Offer luxury upgrades',
          'Exclusive experiences',
          'White-glove service'
        ]
      },
      1: {
        segmentId: 'budget_explorer',
        name: 'Budget Explorers',
        type: SegmentType.BEHAVIORAL,
        size: 0,
        percentage: 0,
        characteristics: {
          avgBookingValue: 1500,
          avgBookingsPerYear: 3,
          avgTripDuration: 7,
          preferredDestinations: ['Thailand', 'Vietnam', 'Portugal'],
          preferredTravelMonths: [4, 5, 9, 10],
          commonAttributes: { budget_ratio: 0.8 }
        },
        typicalBehaviors: [
          'Seeks value deals',
          'Flexible with dates',
          'Uses early-bird discounts'
        ],
        recommendedStrategies: [
          'Promote off-season deals',
          'Last-minute offers',
          'Group tour options'
        ]
      },
      // ... more segments
    };

    return segments[clusterId] || segments[0];
  }
}
```

---

## 6. Dynamic Pricing

### Pricing Optimization

```typescript
// pricing/dynamic-pricing.ts

export interface PricingDecision {
  recommendedPrice: PriceQuote;
  basePrice: PriceQuote;
  adjustment: PriceAdjustment;
  confidence: number;
  expectedConversion: number;
  expectedRevenue: number;
  reasoning: PricingReasoning[];
}

export interface PriceAdjustment {
  amount: number;
  percentage: number;
  factors: AdjustmentFactor[];
}

export interface AdjustmentFactor {
  factor: string;
  impact: number;  // percentage points
  direction: 'up' | 'down';
}

export interface PricingReasoning {
  category: string;
  description: string;
  impact: string;
}

/**
 * Dynamic pricing using demand prediction and elasticity
 */
export class DynamicPricingEngine {
  private demandModel: DemandPredictionModel;
  private elasticityModel: PriceElasticityModel;
  private competitorModel: CompetitorPricingModel;

  /**
   * Calculate optimal price for a trip
   */
  async calculatePrice(
    tripRequest: TripPricingRequest
  ): Promise<PricingDecision> {
    // Get base cost
    const basePrice = await this.calculateBasePrice(tripRequest);

    // Get demand forecast
    const demandForecast = await this.demandModel.predict({
      destinationId: tripRequest.destinationId,
      startDate: tripRequest.startDate,
      duration: tripRequest.duration
    });

    // Get price elasticity
    const elasticity = await this.elasticityModel.getElasticity({
      destinationId: tripRequest.destinationId,
      customerSegment: tripRequest.customerSegment,
      pricePoint: basePrice.amount
    });

    // Get competitor prices
    const competitorPrices = await this.competitorModel.getCompetitorPrices(
      tripRequest
    );

    // Calculate optimal price
    const optimalPrice = this.optimizePrice({
      basePrice,
      demandForecast,
      elasticity,
      competitorPrices,
      constraints: {
        minMargin: tripRequest.minMargin || 0.15,
        maxPrice: basePrice.amount * 1.5,
        targetConversion: tripRequest.targetConversion || 0.1
      }
    });

    // Calculate adjustment breakdown
    const adjustment = this.calculateAdjustment(
      basePrice.amount,
      optimalPrice,
      demandForecast,
      competitorPrices
    );

    // Predict conversion and revenue
    const expectedConversion = this.predictConversion(
      optimalPrice,
      elasticity,
      demandForecast
    );

    const expectedRevenue = optimalPrice * expectedConversion;

    return {
      recommendedPrice: {
        amount: optimalPrice,
        currency: basePrice.currency
      },
      basePrice,
      adjustment,
      confidence: this.calculateConfidence(demandForecast, elasticity),
      expectedConversion,
      expectedRevenue,
      reasoning: this.generateReasoning(adjustment, demandForecast)
    };
  }

  /**
   * Optimize price considering demand, elasticity, and competition
   */
  private optimizePrice(params: {
    basePrice: PriceQuote;
    demandForecast: DemandForecast;
    elasticity: number;
    competitorPrices: CompetitorPrice[];
    constraints: { minMargin: number; maxPrice: number; targetConversion: number };
  }): number {
    const { basePrice, demandForecast, elasticity, competitorPrices, constraints } = params;

    // Start with base price
    let optimalPrice = basePrice.amount;

    // Demand-based adjustment
    if (demandForecast.demandLevel === 'high') {
      optimalPrice *= 1.1;  // 10% increase for high demand
    } else if (demandForecast.demandLevel === 'low') {
      optimalPrice *= 0.95;  // 5% decrease for low demand
    }

    // Competitor-based adjustment
    const avgCompetitorPrice = this.averageCompetitorPrice(competitorPrices);
    if (avgCompetitorPrice > 0) {
      const priceDifference = (optimalPrice - avgCompetitorPrice) / avgCompetitorPrice;

      // If significantly higher than competitors, reduce price
      if (priceDifference > 0.15) {
        optimalPrice = avgCompetitorPrice * 1.05;  // Slightly above average
      }
      // If significantly lower, can increase
      else if (priceDifference < -0.15) {
        optimalPrice *= 1.08;
      }
    }

    // Apply margin constraint
    const cost = basePrice.amount * (1 - 0.2);  // Assume 20% margin in base
    const minPrice = cost / (1 - constraints.minMargin);

    optimalPrice = Math.max(optimalPrice, minPrice);
    optimalPrice = Math.min(optimalPrice, constraints.maxPrice);

    // Check conversion constraint
    const predictedConversion = this.predictConversion(
      optimalPrice,
      elasticity,
      demandForecast
    );

    if (predictedConversion < constraints.targetConversion * 0.8) {
      // Price too high, reduce to meet conversion target
      optimalPrice = this.findPriceForConversion(
        basePrice.amount,
        elasticity,
        constraints.targetConversion,
        demandForecast
      );
    }

    return Math.round(optimalPrice);
  }

  /**
   * Predict conversion rate based on price and elasticity
   */
  private predictConversion(
    price: number,
    elasticity: number,
    demand: DemandForecast
  ): number {
    // Base conversion from demand level
    const baseConversion: Record<string, number> = {
      high: 0.15,
      medium: 0.10,
      low: 0.06
    };

    const base = baseConversion[demand.demandLevel] || 0.10;

    // Apply elasticity
    // price_elasticity = (% change in quantity) / (% change in price)
    // % change in quantity = elasticity * % change in price
    const referencePrice = demand.averageHistoricalPrice || price * 0.9;
    const priceChangeRatio = (price - referencePrice) / referencePrice;
    const quantityChangeRatio = elasticity * priceChangeRatio;

    return base * (1 + quantityChangeRatio);
  }

  /**
   * Find price that achieves target conversion
   */
  private findPriceForConversion(
    referencePrice: number,
    elasticity: number,
    targetConversion: number,
    demand: DemandForecast
  ): number {
    const baseConversion = demand.baseConversion || 0.10;

    // We want: baseConversion * (1 + elasticity * priceChange) = targetConversion
    // So: priceChange = (targetConversion/baseConversion - 1) / elasticity
    const requiredChange = (targetConversion / baseConversion - 1) / elasticity;

    return referencePrice * (1 + requiredChange);
  }

  private calculateAdjustment(
    basePrice: number,
    optimalPrice: number,
    demand: DemandForecast,
    competitors: CompetitorPrice[]
  ): PriceAdjustment {
    const factors: AdjustmentFactor[] = [];

    // Demand factor
    if (demand.demandLevel === 'high') {
      factors.push({
        factor: 'high_demand',
        impact: 10,
        direction: 'up'
      });
    } else if (demand.demandLevel === 'low') {
      factors.push({
        factor: 'low_demand',
        impact: 5,
        direction: 'down'
      });
    }

    // Seasonality factor
    if (demand.isPeakSeason) {
      factors.push({
        factor: 'peak_season',
        impact: 8,
        direction: 'up'
      });
    }

    // Competitor factor
    const avgCompetitorPrice = this.averageCompetitorPrice(competitors);
    if (avgCompetitorPrice > 0) {
      const difference = (optimalPrice - avgCompetitorPrice) / avgCompetitorPrice;
      if (difference > 0) {
        factors.push({
          factor: 'above_market',
          impact: Math.round(difference * 100),
          direction: 'up'
        });
      }
    }

    // Booking window factor
    if (demand.daysUntilDeparture < 30) {
      factors.push({
        factor: 'last_minute',
        impact: 5,
        direction: 'down'
      });
    }

    const percentageChange = ((optimalPrice - basePrice) / basePrice) * 100;

    return {
      amount: optimalPrice - basePrice,
      percentage: Math.round(percentageChange * 10) / 10,
      factors
    };
  }
}
```

---

## 7. A/B Testing Framework

### Experiment Design

```typescript
// experimentation/ab-testing.ts

export interface Experiment {
  experimentId: string;
  name: string;
  description: string;
  hypothesis: string;
  metric: string;  // Primary metric to optimize
  status: 'draft' | 'running' | 'paused' | 'completed';
  variants: Variant[];
  targeting: TargetingRules;
  startTime?: Date;
  endTime?: Date;
  sampleSize: number;
  minDetectableEffect: number;
  significanceLevel: number;
}

export interface Variant {
  variantId: string;
  name: string;
  description: string;
  configuration: Record<string, any>;
  allocation: number;  // 0-1
  traffic: number;     // Actual traffic count
  metrics: VariantMetrics;
}

export interface VariantMetrics {
  exposures: number;
  conversions: number;
  conversionRate: number;
  revenue?: number;
  averageOrderValue?: number;
  confidenceInterval?: [number, number];
  pValue?: number;
  isWinner?: boolean;
}

export interface TargetingRules {
  customerSegments?: string[];
  destinations?: string[];
  channels?: string[];
  percentage: number;  // 0-1
}

/**
 * A/B Testing service
 */
export class ABTestingService {
  private experimentStore: ExperimentStore;
  private stats: StatisticalCalculator;

  /**
   * Create a new experiment
   */
  async createExperiment(config: ExperimentConfig): Promise<Experiment> {
    // Validate experiment design
    this.validateExperiment(config);

    // Calculate required sample size
    const sampleSize = this.calculateSampleSize({
      baselineRate: config.baselineRate,
      minDetectableEffect: config.minDetectableEffect,
      significanceLevel: config.significanceLevel || 0.05,
      power: config.power || 0.8
    });

    const experiment: Experiment = {
      experimentId: this.generateId(),
      name: config.name,
      description: config.description,
      hypothesis: config.hypothesis,
      metric: config.metric,
      status: 'draft',
      variants: config.variants.map((v, i) => ({
        ...v,
        variantId: `variant_${i}`,
        allocation: 1 / config.variants.length,
        traffic: 0,
        metrics: {
          exposures: 0,
          conversions: 0,
          conversionRate: 0
        }
      })),
      targeting: config.targeting || { percentage: 1 },
      sampleSize,
      minDetectableEffect: config.minDetectableEffect,
      significanceLevel: config.significanceLevel || 0.05
    };

    await this.experimentStore.save(experiment);
    return experiment;
  }

  /**
   * Assign user to variant
   */
  async assignVariant(
    experimentId: string,
    customerId: string,
    context: AssignmentContext
  ): Promise<Variant | null> {
    const experiment = await this.experimentStore.get(experimentId);

    // Check if experiment is running
    if (experiment.status !== 'running') {
      return null;
    }

    // Check targeting rules
    if (!this.matchesTargeting(experiment.targeting, context)) {
      return null;
    }

    // Check if already assigned
    const existingAssignment = await this.getAssignment(experimentId, customerId);
    if (existingAssignment) {
      return existingAssignment;
    }

    // Determine variant using consistent hashing
    const variantIndex = this.consistentHash(
      `${experimentId}:${customerId}`,
      experiment.variants.length
    );

    const variant = experiment.variants[variantIndex];

    // Record assignment
    await this.recordAssignment({
      experimentId,
      customerId,
      variantId: variant.variantId,
      timestamp: new Date(),
      context
    });

    // Update exposure count
    variant.metrics.exposures++;

    return variant;
  }

  /**
   * Track conversion event
   */
  async trackConversion(event: ConversionEvent): Promise<void> {
    const assignment = await this.getAssignment(
      event.experimentId,
      event.customerId
    );

    if (!assignment) return;

    const experiment = await this.experimentStore.get(event.experimentId);
    const variant = experiment.variants.find(
      v => v.variantId === assignment.variantId
    );

    if (!variant) return;

    // Update metrics
    if (event.type === experiment.metric) {
      variant.metrics.conversions++;
      variant.metrics.conversionRate =
        variant.metrics.conversions / variant.metrics.exposures;

      if (event.value) {
        variant.metrics.revenue = (variant.metrics.revenue || 0) + event.value;
        variant.metrics.averageOrderValue =
          (variant.metrics.revenue || 0) / variant.metrics.conversions;
      }
    }

    // Calculate statistical significance
    await this.calculateSignificance(experiment);

    await this.experimentStore.save(experiment);
  }

  /**
   * Calculate statistical significance for experiment
   */
  private async calculateSignificance(experiment: Experiment): Promise<void> {
    const control = experiment.variants[0];
    if (!control) return;

    for (let i = 1; i < experiment.variants.length; i++) {
      const variant = experiment.variants[i];

      // Z-test for proportions
      const zScore = this.stats.zTestProportions(
        control.metrics.conversions,
        control.metrics.exposures,
        variant.metrics.conversions,
        variant.metrics.exposures
      );

      // Convert to p-value
      variant.metrics.pValue = this.stats.zToPValue(zScore);

      // Calculate confidence interval
      const se = Math.sqrt(
        (variant.metrics.conversionRate * (1 - variant.metrics.conversionRate)) /
        variant.metrics.exposures
      );
      const margin = 1.96 * se;  // 95% CI
      variant.metrics.confidenceInterval = [
        variant.metrics.conversionRate - margin,
        variant.metrics.conversionRate + margin
      ];

      // Determine winner
      if (
        variant.metrics.pValue !== undefined &&
        variant.metrics.pValue < experiment.significanceLevel &&
        variant.metrics.conversionRate > control.metrics.conversionRate
      ) {
        variant.metrics.isWinner = true;
      }
    }
  }

  /**
   * Calculate required sample size
   */
  private calculateSampleSize(params: {
    baselineRate: number;
    minDetectableEffect: number;
    significanceLevel: number;
    power: number;
  }): number {
    const { baselineRate, minDetectableEffect, significanceLevel, power } = params;

    // Two-sample proportion test
    const p1 = baselineRate;
    const p2 = baselineRate * (1 + minDetectableEffect);
    const pBar = (p1 + p2) / 2;

    const zAlpha = this.stats.inverseNormalCDF(1 - significanceLevel / 2);
    const zBeta = this.stats.inverseNormalCDF(power);

    const n =
      (2 * pBar * (1 - pBar) * Math.pow(zAlpha + zBeta, 2)) /
      Math.pow(p2 - p1, 2);

    return Math.ceil(n);
  }

  /**
   * Check if experiment can be stopped early
   */
  async canStopEarly(experimentId: string): Promise<{
    canStop: boolean;
    reason?: string;
    recommendation: 'continue' | 'declare_winner' | 'declare_no_difference';
  }> {
    const experiment = await this.experimentStore.get(experimentId);

    // Check if we have enough samples
    const totalExposures = experiment.variants.reduce(
      (sum, v) => sum + v.metrics.exposures,
      0
    );

    if (totalExposures < experiment.sampleSize * 0.5) {
      return {
        canStop: false,
        recommendation: 'continue'
      };
    }

    // Check for clear winner
    const winner = experiment.variants.find(v => v.metrics.isWinner);
    if (winner) {
      return {
        canStop: true,
        reason: `Variant ${winner.name} is statistically significant`,
        recommendation: 'declare_winner'
      };
    }

    // Check if effect size is too small to ever reach significance
    const maxObservedEffect = this.calculateMaxEffectSize(experiment);
    if (maxObservedEffect < experiment.minDetectableEffect * 0.5) {
      const requiredSamplesForEffect = this.calculateSampleSize({
        baselineRate: experiment.variants[0].metrics.conversionRate,
        minDetectableEffect: maxObservedEffect,
        significanceLevel: experiment.significanceLevel,
        power: 0.8
      });

      if (totalExposures > requiredSamplesForEffect * 2) {
        return {
          canStop: true,
          reason: 'Effect size too small to detect with reasonable sample size',
          recommendation: 'declare_no_difference'
        };
      }
    }

    return {
      canStop: false,
      recommendation: 'continue'
    };
  }
}
```

---

## 8. Optimization Algorithms

### Trip Itinerary Optimization

```typescript
// optimization/itinerary-optimizer.ts

export interface ItineraryOptimizationRequest {
  destinationId: string;
  duration: number;  // days
  preferences: CustomerPreferences;
  constraints: ItineraryConstraints;
  budget: BudgetRange;
}

export interface ItineraryConstraints {
  maxTravelTimePerDay: number;  // hours
  mustSeeAttractions: string[];
  avoidAttractions: string[];
  restDays: number;
  dietaryRestrictions: string[];
  accessibility: string[];
}

export interface OptimizedItinerary {
  days: ItineraryDay[];
  totalCost: number;
  totalTravelTime: number;
  satisfactionScore: number;
  alternatives: AlternativeItinerary[];
}

/**
 * Itinerary optimization using genetic algorithm
 */
export class ItineraryOptimizer {
  private attractionModel: AttractionModel;
  private routingModel: RoutingModel;
  private pricingModel: PricingModel;

  /**
   * Generate optimal itinerary using genetic algorithm
   */
  async optimize(request: ItineraryOptimizationRequest): Promise<OptimizedItinerary> {
    // Get candidate attractions
    const attractions = await this.attractionModel.getAttractions(
      request.destinationId
    );

    // Filter by constraints and preferences
    const candidates = this.filterAttractions(attractions, request);

    // Generate initial population
    const population = this.generateInitialPopulation(
      candidates,
      request.duration,
      100  // population size
    );

    // Evolve population
    const evolved = this.evolve(population, {
      generations: 200,
      mutationRate: 0.1,
      crossoverRate: 0.7,
      fitnessFunction: (itinerary) => this.calculateFitness(itinerary, request)
    });

    // Get best solution
    const best = evolved[0];

    return {
      days: best.days,
      totalCost: best.totalCost,
      totalTravelTime: best.totalTravelTime,
      satisfactionScore: best.fitness,
      alternatives: evolved.slice(1, 4).map(i => ({
        days: i.days,
        totalCost: i.totalCost,
        satisfactionScore: i.fitness,
        difference: this.describeDifference(best, i)
      }))
    };
  }

  /**
   * Calculate fitness score for an itinerary
   */
  private calculateFitness(
    itinerary: ItinerarySolution,
    request: ItineraryOptimizationRequest
  ): number {
    let score = 0;

    // Preference matching
    for (const day of itinerary.days) {
      for (const activity of day.activities) {
        const attraction = activity.attraction;

        // Category preference
        if (request.preferences.categories[attraction.category]) {
          score += request.preferences.categories[attraction.category] * 2;
        }

        // Vibe preference
        for (const vibe of attraction.vibes) {
          if (request.preferences.vibes[vibe]) {
            score += request.preferences.vibes[vibe];
          }
        }
      }
    }

    // Must-see attractions bonus
    for (const mustSeeId of request.constraints.mustSeeAttractions) {
      const isIncluded = itinerary.days.some(day =>
        day.activities.some(a => a.attraction.id === mustSeeId)
      );
      if (isIncluded) {
        score += 50;
      }
    }

    // Cost penalty
    const costScore = this.calculateCostScore(itinerary.totalCost, request.budget);
    score += costScore * 30;

    // Travel time penalty
    const avgTravelTime = itinerary.totalTravelTime / request.duration;
    if (avgTravelTime > request.constraints.maxTravelTimePerDay) {
      score -= (avgTravelTime - request.constraints.maxTravelTimePerDay) * 10;
    }

    // Activity balance bonus
    const balanceScore = this.calculateBalanceScore(itinerary);
    score += balanceScore * 10;

    return score;
  }

  /**
   * Genetic algorithm evolution
   */
  private evolve(
    population: ItinerarySolution[],
    params: {
      generations: number;
      mutationRate: number;
      crossoverRate: number;
      fitnessFunction: (i: ItinerarySolution) => number;
    }
  ): ItinerarySolution[] {
    let currentPopulation = [...population];

    for (let gen = 0; gen < params.generations; gen++) {
      // Calculate fitness for all
      currentPopulation.forEach(solution => {
        solution.fitness = params.fitnessFunction(solution);
      });

      // Sort by fitness
      currentPopulation.sort((a, b) => b.fitness - a.fitness);

      // Selection (tournament)
      const selected = this.tournamentSelection(currentPopulation, 0.7);

      // Crossover
      const offspring: ItinerarySolution[] = [];
      for (let i = 0; i < selected.length; i += 2) {
        if (Math.random() < params.crossoverRate && i + 1 < selected.length) {
          const children = this.crossover(selected[i], selected[i + 1]);
          offspring.push(...children);
        } else {
          offspring.push(selected[i]);
          if (i + 1 < selected.length) {
            offspring.push(selected[i + 1]);
          }
        }
      }

      // Mutation
      for (const solution of offspring) {
        if (Math.random() < params.mutationRate) {
          this.mutate(solution);
        }
      }

      // Elitism - keep best solutions
      const eliteCount = Math.floor(currentPopulation.length * 0.1);
      const elite = currentPopulation.slice(0, eliteCount);

      // New population
      currentPopulation = [
        ...elite,
        ...offspring.slice(0, currentPopulation.length - eliteCount)
      ];

      // Check convergence
      if (this.hasConverged(currentPopulation)) {
        break;
      }
    }

    return currentPopulation;
  }

  private crossover(
    parent1: ItinerarySolution,
    parent2: ItinerarySolution
  ): [ItinerarySolution, ItinerarySolution] {
    // Order crossover (OX) for permutation
    const child1: ItinerarySolution = {
      days: JSON.parse(JSON.stringify(parent1.days)),
      totalCost: 0,
      totalTravelTime: 0,
      fitness: 0
    };

    const child2: ItinerarySolution = {
      days: JSON.parse(JSON.stringify(parent2.days)),
      totalCost: 0,
      totalTravelTime: 0,
      fitness: 0
    };

    // Select random crossover points
    const day1 = Math.floor(Math.random() * parent1.days.length);
    const day2 = Math.floor(Math.random() * parent1.days.length);
    const [start, end] = [Math.min(day1, day2), Math.max(day1, day2)];

    // Swap segments
    for (let i = start; i <= end; i++) {
      const temp = child1.days[i];
      child1.days[i] = child2.days[i];
      child2.days[i] = temp;
    }

    // Recalculate metrics
    this.recalculateMetrics(child1);
    this.recalculateMetrics(child2);

    return [child1, child2];
  }

  private mutate(solution: ItinerarySolution): void {
    // Random swap mutation
    const day1 = Math.floor(Math.random() * solution.days.length);
    const day2 = Math.floor(Math.random() * solution.days.length);

    if (day1 !== day2 && solution.days[day1].activities.length > 0) {
      // Move random activity from day1 to day2
      const activityIndex = Math.floor(
        Math.random() * solution.days[day1].activities.length
      );
      const activity = solution.days[day1].activities.splice(activityIndex, 1)[0];
      solution.days[day2].activities.push(activity);
    }

    this.recalculateMetrics(solution);
  }
}
```

---

## 9. Model Training Pipeline

### Training Orchestration

```typescript
// training/pipeline.ts

export interface TrainingJob {
  jobId: string;
  modelType: string;
  modelVersion: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  config: TrainingConfig;
  startTime?: Date;
  endTime?: Date;
  metrics?: TrainingMetrics;
  modelPath?: string;
}

export interface TrainingConfig {
  algorithm: string;
  hyperparameters: Record<string, any>;
  dataConfig: DataConfig;
  validationConfig: ValidationConfig;
  resources: ResourceConfig;
}

export interface TrainingMetrics {
  trainLoss: number[];
  valLoss: number[];
  trainMetrics: MetricHistory[];
  valMetrics: MetricHistory[];
  bestEpoch: number;
  bestScore: number;
  duration: number;
}

/**
 * Model training pipeline orchestrator
 */
export class TrainingPipeline {
  private jobQueue: TrainingJobQueue;
  const modelRegistry: ModelRegistry;
  private experimentTracker: ExperimentTracker;

  /**
   * Submit training job
   */
  async submitTraining(config: TrainingConfig): Promise<TrainingJob> {
    const job: TrainingJob = {
      jobId: this.generateJobId(),
      modelType: config.modelType,
      modelVersion: `v${Date.now()}`,
      status: 'pending',
      config
    };

    await this.jobQueue.enqueue(job);

    // Start processing if workers available
    await this.processQueue();

    return job;
  }

  /**
   * Process training job
   */
  private async processJob(job: TrainingJob): Promise<void> {
    job.status = 'running';
    job.startTime = new Date();
    await this.jobQueue.update(job);

    try {
      // Log experiment start
      await this.experimentTracker.startRun(job.jobId, {
        modelType: job.modelType,
        config: job.config
      });

      // Load data
      const data = await this.loadData(job.config.dataConfig);

      // Split data
      const splits = this.splitData(data, {
        train: 0.7,
        val: 0.15,
        test: 0.15,
        stratify: job.config.dataConfig.stratifyColumn
      });

      // Train model
      const result = await this.trainModel(job, splits);

      // Evaluate on test set
      const testMetrics = await this.evaluate(
        result.model,
        splits.test,
        job.config.validationConfig.metrics
      );

      // Log metrics
      await this.experimentTracker.logMetrics(job.jobId, {
        train: result.metrics,
        val: result.valMetrics,
        test: testMetrics
      });

      // Register model
      const modelPath = await this.modelRegistry.register({
        modelId: `${job.modelType}_${job.modelVersion}`,
        modelType: job.modelType,
        version: job.modelVersion,
        model: result.model,
        metrics: testMetrics,
        config: job.config,
        trainedAt: new Date()
      });

      job.status = 'completed';
      job.endTime = new Date();
      job.metrics = result.metrics;
      job.modelPath = modelPath;

      await this.jobQueue.update(job);

    } catch (error) {
      job.status = 'failed';
      job.endTime = new Date();
      await this.jobQueue.update(job);

      await this.experimentTracker.logError(job.jobId, error);
      throw error;
    }
  }

  /**
   * Train model with hyperparameter tuning
   */
  private async trainModel(
    job: TrainingJob,
    splits: DataSplits
  ): Promise<TrainingResult> {
    const config = job.config;

    // Hyperparameter tuning if enabled
    if (config.hyperparameterSearch) {
      return await this.hyperparameterTune(job, splits);
    }

    // Single training run
    return await this.singleTrainingRun(job, splits, config.hyperparameters);
  }

  /**
   * Hyperparameter tuning using Bayesian optimization
   */
  private async hyperparameterTune(
    job: TrainingJob,
    splits: DataSplits
  ): Promise<TrainingResult> {
    const searchSpace = job.config.hyperparameterSearch!.searchSpace;
    const optimizer = new BayesianOptimizer({
      searchSpace,
      nIterations: job.config.hyperparameterSearch!.maxIterations || 20
    });

    let bestResult: TrainingResult | null = null;
    let bestScore = -Infinity;

    for (let i = 0; i < optimizer.config.nIterations; i++) {
      // Suggest hyperparameters
      const hyperparams = await optimizer.suggest();

      // Train with suggested hyperparameters
      const result = await this.singleTrainingRun(job, splits, hyperparams);

      // Get validation score
      const valScore = this.getPrimaryMetric(result.valMetrics);

      // Update optimizer
      await optimizer.observe(hyperparams, valScore);

      // Track best
      if (valScore > bestScore) {
        bestScore = valScore;
        bestResult = result;
      }

      // Log to experiment tracker
      await this.experimentTracker.logHyperparameters(
        job.jobId,
        `iteration_${i}`,
        hyperparams,
        valScore
      );
    }

    return bestResult!;
  }

  /**
   * Single training run
   */
  private async singleTrainingRun(
    job: TrainingJob,
    splits: DataSplits,
    hyperparams: Record<string, any>
  ): Promise<TrainingResult> {
    const algorithm = this.createAlgorithm(job.config.algorithm, hyperparams);

    const trainMetrics: MetricHistory[] = [];
    const valMetrics: MetricHistory[] = [];

    // Training loop
    for (let epoch = 0; epoch < hyperparams.epochs || 100; epoch++) {
      // Train epoch
      await algorithm.trainEpoch(splits.train);

      // Compute metrics
      if (epoch % 10 === 0 || epoch === (hyperparams.epochs || 100) - 1) {
        const trainMetrics = await algorithm.evaluate(splits.train);
        const valMetrics = await algorithm.evaluate(splits.val);

        trainMetrics.push({ epoch, metrics: trainMetrics });
        valMetrics.push({ epoch, metrics: valMetrics });

        // Early stopping
        if (this.shouldStopEarly(valMetrics)) {
          break;
        }
      }
    }

    // Get best model
    const bestEpoch = this.findBestEpoch(valMetrics);
    const bestModel = await algorithm.getModelAtEpoch(bestEpoch);

    return {
      model: bestModel,
      metrics: trainMetrics,
      valMetrics: valMetrics,
      bestEpoch,
      bestScore: valMetrics[bestEpoch].metrics[job.config.validationConfig.primaryMetric]
    };
  }
}
```

---

## 10. API Specification

### Recommendation Endpoints

```typescript
// api/recommendations.ts

/**
 * GET /api/recommendations
 * Get personalized recommendations
 */
interface GetRecommendationsRequest {
  customerId: string;
  type: 'destination' | 'accommodation' | 'activity' | 'package';
  context?: {
    tripId?: string;
    destination?: string;
    dates?: { start: string; end: string };
    budget?: { min: number; max: number };
  };
  limit?: number;
  excludeIds?: string[];
}

interface GetRecommendationsResponse {
  items: Array<{
    entityId: string;
    type: string;
    score: number;
    confidence: number;
    reasoning: string[];
    price?: { amount: number; currency: string };
    availability?: { status: string; seats: number };
  }>;
  metadata: {
    algorithm: string;
    confidence: number;
    diversity_score: number;
    freshness_score: number;
  };
}

/**
 * POST /api/recommendations/feedback
 * Submit feedback on recommendations
 */
interface SubmitFeedbackRequest {
  customerId: string;
  recommendationId: string;
  feedback: {
    clicked?: boolean;
    booked?: boolean;
    rating?: number;
    dismissed?: boolean;
  };
}
```

### Prediction Endpoints

```typescript
// api/predictions.ts

/**
 * POST /api/predictions/price
 * Get price prediction
 */
interface PricePredictionRequest {
  destinationId: string;
  accommodationId?: string;
  departureDate: string;
  duration: number;
  roomType?: string;
  occupancy: number;
  includeFlight?: boolean;
}

interface PricePredictionResponse {
  predictedPrice: {
    amount: number;
    currency: string;
    breakdown: Record<string, number>;
  };
  confidence: number;
  trend: 'rising' | 'stable' | 'falling';
  recommendation: 'book_now' | 'wait' | 'neutral';
  reasoning: string[];
  historicalPrices: Array<{ date: string; price: number }>;
  forecast: Array<{
    date: string;
    predictedPrice: number;
    confidenceInterval: [number, number];
  }>;
}

/**
 * POST /api/predictions/suitability
 * Get trip suitability score
 */
interface SuitabilityPredictionRequest {
  customerId: string;
  tripDetails: {
    destinationId: string;
    accommodationId?: string;
    startDate: string;
    endDate: string;
    activities: string[];
    budget: { min: number; max: number };
    travelers: Array<{
      age: number;
      type: 'adult' | 'child' | 'senior';
    }>;
  };
}

interface SuitabilityPredictionResponse {
  overallScore: number;
  confidence: number;
  breakdown: {
    budgetMatch: number;
    destinationMatch: number;
    timingMatch: number;
    activityMatch: number;
    accommodationMatch: number;
    travelerMatch: number;
  };
  concerns: Array<{
    severity: 'low' | 'medium' | 'high';
    category: string;
    description: string;
    mitigation?: string;
  }>;
  recommendations: string[];
  alternatives?: Array<{
    destinationId: string;
    score: number;
    reason: string;
  }>;
}

/**
 * GET /api/predictions/churn/:customerId
 * Get churn prediction
 */
interface ChurnPredictionResponse {
  churnProbability: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  keyFactors: Array<{
    factor: string;
    impact: number;
    description: string;
  }>;
  recommendedActions: string[];
  predictedLifespan: number;
}
```

### Segmentation Endpoints

```typescript
// api/segments.ts

/**
 * GET /api/segments
 * List all customer segments
 */
interface ListSegmentsResponse {
  segments: Array<{
    segmentId: string;
    name: string;
    type: string;
    size: number;
    percentage: number;
    characteristics: {
      avgBookingValue: number;
      avgBookingsPerYear: number;
      preferredDestinations: string[];
    };
  }>;
}

/**
 * GET /api/segments/:segmentId/customers
 * Get customers in a segment
 */
interface GetSegmentCustomersRequest {
  segmentId: string;
  page?: number;
  limit?: number;
  sortBy?: string;
}

interface GetSegmentCustomersResponse {
  customers: Array<{
    customerId: string;
    name: string;
    score: number;
    metrics: {
      totalSpent: number;
      bookingsCount: number;
      lastBookingDate: string;
    };
  }>;
  pagination: {
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
  };
}

/**
 * POST /api/segments/reassign
 * Trigger reassignment of customers to segments
 */
interface ReassignSegmentsRequest {
  segmentType?: 'rfm' | 'behavioral' | 'lifestage';
  customerIds?: string[];  // Empty = all customers
}

interface ReassignSegmentsResponse {
  jobId: string;
  status: string;
  estimatedCustomers: number;
}
```

### A/B Testing Endpoints

```typescript
// api/experiments.ts

/**
 * POST /api/experiments
 * Create new experiment
 */
interface CreateExperimentRequest {
  name: string;
  description: string;
  hypothesis: string;
  metric: string;
  variants: Array<{
    name: string;
    description: string;
    configuration: Record<string, any>;
  }>;
  targeting?: {
    customerSegments?: string[];
    destinations?: string[];
    channels?: string[];
    percentage: number;
  };
  baselineRate: number;
  minDetectableEffect: number;
  significanceLevel?: number;
  power?: number;
}

interface CreateExperimentResponse {
  experimentId: string;
  status: string;
  sampleSize: number;
  estimatedDuration: number;  // days
}

/**
 * GET /api/experiments/:experimentId
 * Get experiment details
 */
interface GetExperimentResponse {
  experimentId: string;
  name: string;
  status: string;
  variants: Array<{
    variantId: string;
    name: string;
    allocation: number;
    traffic: number;
    metrics: {
      exposures: number;
      conversions: number;
      conversionRate: number;
      revenue?: number;
      confidenceInterval?: [number, number];
      pValue?: number;
      isWinner?: boolean;
    };
  }>;
  startTime?: string;
  endTime?: string;
  canStop: {
    canStop: boolean;
    reason?: string;
    recommendation: string;
  };
}

/**
 * POST /api/experiments/:experimentId/start
 * Start experiment
 */
interface StartExperimentResponse {
  status: string;
  startTime: string;
}

/**
 * POST /api/experiments/:experimentId/stop
 * Stop experiment and declare winner
 */
interface StopExperimentRequest {
  variantId?: string;  // If specified, declare this variant winner
}

interface StopExperimentResponse {
  status: string;
  endTime: string;
  winner?: {
    variantId: string;
    name: string;
    improvement: number;
    confidence: number;
  };
}
```

---

## 11. Testing Scenarios

### Unit Tests

```typescript
// __tests__/decision-intelligence/recommender.test.ts

describe('HybridRecommendationEngine', () => {
  let engine: HybridRecommendationEngine;
  let mockCustomerStore: MockCustomerStore;

  beforeEach(() => {
    mockCustomerStore = new MockCustomerStore();
    engine = new HybridRecommendationEngine({
      customerStore: mockCustomerStore
    });
  });

  describe('recommend', () => {
    it('should return recommendations for existing customer', async () => {
      // Arrange
      const request: RecommendationRequest = {
        customerId: 'cust_123',
        type: RecommendationType.DESTINATION,
        limit: 10
      };

      mockCustomerStore.setHistory('cust_123', [
        { destinationId: 'dest_1', rating: 5 },
        { destinationId: 'dest_2', rating: 4 }
      ]);

      // Act
      const result = await engine.recommend(request);

      // Assert
      expect(result.items).toHaveLength(10);
      expect(result.items[0].score).toBeGreaterThan(0);
      expect(result.items[0].reasoning).not.toEmpty();
      expect(result.metadata.confidence).toBeGreaterThan(0);
    });

    it('should use popularity for cold start users', async () => {
      // Arrange
      const request: RecommendationRequest = {
        customerId: 'new_customer',
        type: RecommendationType.DESTINATION,
        limit: 10
      };

      mockCustomerStore.setHistory('new_customer', []);

      // Act
      const result = await engine.recommend(request);

      // Assert
      expect(result.metadata.algorithm).toBe('popularity');
    });

    it('should apply diversification', async () => {
      // Arrange
      const request: RecommendationRequest = {
        customerId: 'cust_123',
        type: RecommendationType.DESTINATION,
        limit: 10
      };

      // Act
      const result = await engine.recommend(request);

      // Assert
      expect(result.metadata.diversity_score).toBeGreaterThan(0.3);
    });
  });
});

describe('PricePredictor', () => {
  let predictor: PricePredictor;
  let mockModel: MockPriceModel;

  beforeEach(() => {
    mockModel = new MockPriceModel();
    predictor = new PricePredictor({ model: mockModel });
  });

  describe('predict', () => {
    it('should return price prediction with forecast', async () => {
      // Arrange
      const request: PricePredictionRequest = {
        destinationId: 'dest_paris',
        departureDate: new Date('2026-06-01'),
        duration: 7,
        occupancy: 2
      };

      mockModel.setPrediction(2500);

      // Act
      const result = await predictor.predict(request);

      // Assert
      expect(result.predictedPrice.amount).toBe(2500);
      expect(result.trend).toBeDefined();
      expect(result.recommendation).toBeDefined();
      expect(result.forecast).toHaveLength(10);  // 30 days / 3 day intervals
    });

    it('should recommend booking when prices are rising', async () => {
      // Arrange
      const request: PricePredictionRequest = {
        destinationId: 'dest_paris',
        departureDate: new Date('2026-06-01'),
        duration: 7,
        occupancy: 2
      };

      mockModel.setPrediction(2500);
      mockModel.setTrend('rising');
      mockModel.setConfidence(0.8);

      // Act
      const result = await predictor.predict(request);

      // Assert
      expect(result.recommendation).toBe('book_now');
      expect(result.trend).toBe('rising');
    });
  });
});

describe('SuitabilityScorer', () => {
  let scorer: SuitabilityScorer;

  beforeEach(() => {
    scorer = new SuitabilityScorer();
  });

  describe('score', () => {
    it('should return high score for well-matched trip', async () => {
      // Arrange
      const request: SuitabilityRequest = {
        customerId: 'cust_123',
        tripDetails: {
          destinationId: 'dest_beach',
          startDate: new Date('2026-06-01'),
          endDate: new Date('2026-06-07'),
          activities: ['beach', 'relaxation'],
          budget: { min: 2000, max: 3000 },
          travelers: [{ age: 35, type: 'adult' }]
        }
      };

      // Act
      const result = await scorer.score(request);

      // Assert
      expect(result.overallScore).toBeGreaterThan(70);
      expect(result.breakdown).toBeDefined();
    });

    it('should flag concerns for budget mismatch', async () => {
      // Arrange
      const request: SuitabilityRequest = {
        customerId: 'cust_123',
        tripDetails: {
          destinationId: 'dest_luxury',
          startDate: new Date('2026-06-01'),
          endDate: new Date('2026-06-07'),
          activities: ['luxury'],
          budget: { min: 500, max: 1000 },  // Too low
          travelers: [{ age: 35, type: 'adult' }]
        }
      };

      // Act
      const result = await scorer.score(request);

      // Assert
      const budgetConcern = result.concerns.find(c => c.category === 'budget');
      expect(budgetConcern).toBeDefined();
      expect(budgetConcern?.severity).toBe('high');
    });
  });
});
```

### Integration Tests

```typescript
// __tests__/integration/decision-pipeline.test.ts

describe('Decision Intelligence Pipeline', () => {
  describe('End-to-end recommendation flow', () => {
    it('should process customer inquiry and return recommendations', async () => {
      // Setup test customer with history
      const customerId = await createTestCustomer({
        preferences: { categories: { beach: 5, adventure: 3 } },
        pastDestinations: ['dest_maldives', 'dest_bali']
      });

      // Get recommendations
      const response = await app.request('/api/recommendations', {
        method: 'POST',
        body: JSON.stringify({
          customerId,
          type: 'destination',
          limit: 5
        })
      });

      expect(response.status).toBe(200);
      const data = await response.json();

      expect(data.items).toHaveLength(5);
      expect(data.items[0]).toMatchObject({
        entityId: expect.any(String),
        score: expect.any(Number),
        confidence: expect.any(Number)
      });
    });
  });

  describe('Price prediction with model update', () => {
    it('should use updated model for predictions', async () => {
      // Train new model version
      const trainingJob = await app.request('/api/models/train', {
        method: 'POST',
        body: JSON.stringify({
          modelType: 'price_prediction',
          dataConfig: { dataSource: 'bookings_last_12m' }
        })
      });

      await waitForJob(trainingJob.body.jobId);

      // Get prediction using new model
      const prediction = await app.request('/api/predictions/price', {
        method: 'POST',
        body: JSON.stringify({
          destinationId: 'dest_paris',
          departureDate: '2026-06-01',
          duration: 7,
          occupancy: 2
        })
      });

      expect(prediction.status).toBe(200);
      expect(prediction.body.modelVersion).toBeDefined();
    });
  });
});
```

---

## 12. Metrics Definitions

### Model Performance Metrics

```typescript
// metrics/model-metrics.ts

export interface ModelMetrics {
  // Classification metrics
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1Score?: number;
  aucROC?: number;
  aucPR?: number;
  confusionMatrix?: ConfusionMatrix;

  // Regression metrics
  mae?: number;        // Mean Absolute Error
  mse?: number;        // Mean Squared Error
  rmse?: number;       // Root Mean Squared Error
  r2Score?: number;    // R-squared
  mape?: number;       // Mean Absolute Percentage Error

  // Ranking metrics
  ndcg?: number;       // Normalized Discounted Cumulative Gain
  precisionAtK?: Map<number, number>;
  recallAtK?: Map<number, number>;
  map?: number;        // Mean Average Precision

  // Business metrics
  conversionRate?: number;
  clickThroughRate?: number;
  revenuePerUser?: number;
  lift?: number;
}

export interface ConfusionMatrix {
  truePositive: number;
  trueNegative: number;
  falsePositive: number;
  falseNegative: number;
}

/**
 * Calculate recommendation quality metrics
 */
export function calculateRecommendationMetrics(
  recommendations: RecommendedItem[],
  groundTruth: string[],
  K: number = 10
): ModelMetrics {
  const topK = recommendations.slice(0, K);
  const relevant = topK.filter(r => groundTruth.includes(r.entityId));

  // Precision@K
  const precisionAtK = relevant.length / K;

  // Recall@K
  const recallAtK = groundTruth.length > 0
    ? relevant.length / Math.min(groundTruth.length, K)
    : 0;

  // NDCG@K
  const dcg = topK.reduce((sum, item, index) => {
    const relevance = groundTruth.includes(item.entityId) ? 1 : 0;
    return sum + (relevance / Math.log2(index + 2));
  }, 0);

  const idealOrder = [...groundTruth]
    .sort(() => -1)
    .slice(0, K);
  const idcg = idealOrder.reduce((sum, _, index) => {
    return sum + (1 / Math.log2(index + 2));
  }, 0);

  const ndcg = idcg > 0 ? dcg / idcg : 0;

  return {
    precisionAtK: new Map([[K, precisionAtK]]),
    recallAtK: new Map([[K, recallAtK]]),
    ndcg
  };
}
```

### Business Metrics

```typescript
// metrics/business-metrics.ts

export interface DecisionBusinessMetrics {
  // Recommendation impact
  recommendationConversionRate: number;
  recommendationRevenue: number;
  recommendationClickRate: number;

  // Prediction accuracy
  pricePredictionMAE: number;
  pricePredictionMAPE: number;
  suitabilityCalibration: number;  // How well scores match actual satisfaction

  // Segmentation
  segmentSizeDistribution: Map<string, number>;
  segmentMigrationRate: number;    // Customers changing segments
  segmentValueDistribution: Map<string, number>;

  // Experiment results
  experimentsRun: number;
  experimentsWon: number;
  averageLift: number;
  averageTestDuration: number;
}

/**
 * Track recommendation business impact
 */
export class RecommendationBusinessTracker {
  async trackRecommendationOutcome(event: {
    customerId: string;
    recommendationId: string;
    action: 'viewed' | 'clicked' | 'booked';
    value?: number;
  }): Promise<void> {
    await this.metricsStore.record({
      metric: 'recommendation_outcome',
      tags: {
        action: event.action,
        customerId: event.customerId
      },
      value: event.value || 1,
      timestamp: new Date()
    });
  }

  async getRecommendationPerformance(
    timeRange: { start: Date; end: Date }
  ): Promise<{
    conversionRate: number;
    clickRate: number;
    revenue: number;
    avgTimeToConvert: number;
  }> {
    const metrics = await this.metricsStore.query({
      metric: 'recommendation_outcome',
      timeRange
    });

    const views = metrics.filter(m => m.tags.action === 'viewed').length;
    const clicks = metrics.filter(m => m.tags.action === 'clicked').length;
    const bookings = metrics.filter(m => m.tags.action === 'booked');
    const revenue = bookings.reduce((sum, b) => sum + (b.value || 0), 0);

    return {
      conversionRate: views > 0 ? bookings.length / views : 0,
      clickRate: views > 0 ? clicks / views : 0,
      revenue,
      avgTimeToConvert: this.calculateAvgTimeToConvert(bookings)
    };
  }
}
```

---

## Summary

This document defines the Decision Intelligence systems for the Travel Agency Agent platform:

**Key Components:**
- **Recommendation Engine**: Hybrid collaborative + content-based filtering
- **Prediction Models**: Price forecasting, suitability scoring, churn prediction
- **Customer Segmentation**: RFM analysis, K-means behavioral clustering
- **Dynamic Pricing**: Demand-based, elasticity-aware optimization
- **A/B Testing**: Statistical experiment framework
- **Optimization Algorithms**: Genetic algorithm for itinerary optimization
- **Training Pipeline**: Automated model training with hyperparameter tuning

**Integration Points:**
- Feature Store for real-time feature serving
- Model Registry for version management
- Experiment Tracking for reproducibility
- Data Warehouse for training data

**Next:** [AIML_03: Natural Language Processing Patterns](./AIML_03_NLP_PATTERNS.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-04-25
**Status:** ✅ Complete
