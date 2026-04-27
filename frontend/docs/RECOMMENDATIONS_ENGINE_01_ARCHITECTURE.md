# Recommendations Engine Part 1: Architecture

> System design, algorithms overview, and infrastructure

**Series:** Recommendations Engine
**Next:** [Part 2: Collaborative Filtering](./RECOMMENDATIONS_ENGINE_02_COLLABORATIVE.md)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Recommendation Types](#recommendation-types)
3. [Data Pipeline](#data-pipeline)
4. [Model Serving](#model-serving)
5. [Evaluation Metrics](#evaluation-metrics)

---

## System Overview

### Architecture Diagram

```typescript
// Recommendations system architecture

interface RecommendationsArchitecture {
  // Data layer
  data: {
    events: 'User behavior events (clicks, bookings)';
    features: 'User and item features';
    models: 'Trained model artifacts';
  };

  // Training layer (offline)
  training: {
    input: 'Event data + features';
    process: 'Feature extraction → Model training → Evaluation';
    output: 'Trained models → Model registry';
    frequency: 'Daily for models, hourly for features';
  };

  // Serving layer (online)
  serving: {
    api: 'Recommendations API';
    cache: 'Redis for hot results';
    model: 'Model inference engine';
    latency: '<200ms p95';
  };

  // Feedback loop
  feedback: {
    events: 'User interactions with recommendations';
    process: 'Log → Feature store → Retraining';
  };
}
```

### Component Stack

```typescript
// Technology choices

interface TechStack {
  // ML framework
  training: {
    python: '3.11';
    framework: 'LightFM + scikit-learn';
    storage: 'MLflow for model registry';
  };

  // Feature store
  features: {
    store: 'Feast (Feature Store)';
    offline: 'PostgreSQL (historical)';
    online: 'Redis (real-time)';
  };

  // Serving
  serving: {
    api: 'FastAPI (Python)';
    cache: 'Redis (hot recommendations)';
    cdn: 'Cloudflare (precomputed feeds)';
  };

  // Events
  events: {
    collection: 'Snowplow Analytics';
    storage: 'BigQuery (data warehouse)';
    streaming: 'Kafka (real-time events)';
  };
}
```

---

## Recommendation Types

### Type 1: Similar Items (Item-Based)

```typescript
// "Similar to Paris" recommendations

interface SimilarItemsRecs {
  useCase: 'Destination/accommodation detail page';
  algorithm: 'Item-based collaborative filtering';
  input: 'Item ID';
  output: 'Similar items with scores';
  cache: 'Precomputed, refreshed daily';
  latency: '<50ms';

  example: {
    input: 'paris_destination';
    output: [
      { id: 'rome', score: 0.92, reason: 'Similar cultural attractions' },
      { id: 'barcelona', score: 0.88, reason: 'Similar urban experience' },
      { id: 'amsterdam', score: 0.85, reason: 'Similar romantic appeal' },
    ];
  };
}
```

### Type 2: Personalized Feed (User-Based)

```typescript
// "For You" personalized recommendations

interface PersonalizedFeedRecs {
  useCase: 'Homepage, user dashboard';
  algorithm: 'Hybrid (collaborative + content-based)';
  input: 'User ID, context';
  output: 'Personalized item list';
  cache: 'User-specific, TTL 1 hour';
  latency: '<200ms';

  example: {
    input: 'user_123';
    context: { season: 'summer', budget: 'moderate' };
    output: [
      {
        id: 'crete_beach_resort',
        score: 0.94,
        reason: 'Matches your beach preference',
        explanation: 'Because you liked Santorini',
      },
      {
        id: 'kyoto_cultural_tour',
        score: 0.87,
        reason: 'Cultural destinations you enjoy',
        explanation: 'Popular with similar travelers',
      },
    ];
  };
}
```

### Type 3: Trending (Popularity-Based)

```typescript
// "Trending Now" recommendations

interface TrendingRecs {
  useCase: 'Homepage, discovery';
  algorithm: 'Popularity score with time decay';
  input: 'None or location';
  output: 'Trending items';
  cache: 'Global, refreshed every 15 min';
  latency: '<20ms';

  formula: 'score = (views × 0.3 + bookings × 0.5) × e^(-days_old/7)';
}
```

### Type 4: Session-Based (Real-Time)

```typescript
// "Because You Viewed" recommendations

interface SessionBasedRecs {
  useCase: 'During browsing session';
  algorithm: 'Content-based similarity';
  input: 'Session items (viewed, clicked)';
  output: 'Similar to session items';
  cache: 'Session-specific, no cache';
  latency: '<100ms';

  example: {
    session: ['paris_hotel', 'paris_museum_tour'];
    output: [
      {
        id: 'paris_food_tour',
        score: 0.91,
        reason: 'Complements your Paris trip',
      },
    ];
  };
}
```

### Type 5: Cross-Sell (Association Rules)

```typescript
// "Complete Your Trip" recommendations

interface CrossSellRecs {
  useCase: 'Booking flow, checkout';
  algorithm: 'Association rules / market basket analysis';
  input: 'Cart items, destination';
  output: 'Complementary products';
  cache: 'Destination-specific, daily refresh';
  latency: '<150ms';

  example: {
    input: { destination: 'paris', hotel: 'booked' };
    output: [
      { id: 'paris_museum_pass', type: 'activity', confidence: 0.75 },
      { id: 'cdg_airport_transfer', type: 'transfer', confidence: 0.82 },
      { id: 'seine_dinner_cruise', type: 'experience', confidence: 0.68 },
    ];
  };
}
```

---

## Data Pipeline

### Event Collection

```typescript
// User behavior events to collect

interface RecommendationEvent {
  // View events
  view: {
    destination_viewed: 'User viewed destination page';
    accommodation_viewed: 'User viewed accommodation page';
    deal_viewed: 'User viewed deal';
  };

  // Engagement events
  engagement: {
    search: 'User searched for destination';
    filter_applied: 'User applied filter';
    map_interaction: 'User interacted with map';
  };

  // Intent events
  intent: {
    added_to_wishlist: 'User saved item';
    trip_started: 'User started planning trip';
    dates_selected: 'User selected travel dates';
  };

  // Conversion events
  conversion: {
    booking_completed: 'User made booking';
    booking_value: 'Transaction amount';
  };

  // Feedback events
  feedback: {
    recommendation_clicked: 'User clicked recommendation';
    recommendation_dismissed: 'User dismissed recommendation';
    rating_submitted: 'User submitted rating';
  };
}

// Event tracking
export function trackRecommendationEvent(event: RecEvent) {
  analytics.track('recommendation_event', {
    user_id: event.userId,
    session_id: event.sessionId,
    event_type: event.type,
    item_id: event.itemId,
    item_type: event.itemType,
    recommendation_id: event.recommendationId,
    model_version: event.modelVersion,
    position: event.position,
    context: event.context,
    timestamp: Date.now(),
  });
}
```

### Feature Engineering

```typescript
// User features for recommendations

interface UserFeatures {
  // Demographic
  demographic: {
    age_group: '18-24, 25-34, 35-44, 45-54, 55+';
    origin_country: 'User home country';
    language: 'Preferred language';
  };

  // Behavioral
  behavioral: {
    bookin_count: 'Total bookings made';
    avg_trip_value: 'Average spending per trip';
    travel_frequency: 'Trips per year';
    booking_window: 'Days between search and booking';
    loyalty_tier: 'bronze, silver, gold, platinum';
  };

  // Preferences (explicit)
  preferences: {
    travel_styles: ['adventure', 'beach', 'cultural', 'luxury', 'family'];
    interests: ['food', 'history', 'nature', 'nightlife'];
    budget_range: [min, max];
    group_types: ['solo', 'couple', 'family', 'friends'];
  };

  // Preferences (implicit)
  implicit: {
    preferred_regions: ['europe', 'caribbean', 'asia'];
    preferred_accommodation_types: ['hotel', 'resort', 'villa'];
    seasonal_preference: ['summer', 'winter', 'year-round'];
  };

  // Contextual
  contextual: {
    current_session_intent: 'browsing, planning, booking';
    current_trip_phase: 'searching, comparing, ready_to_book';
    device_type: 'mobile, desktop, tablet';
  };
}

// Item features for recommendations
interface DestinationFeatures {
  // Basic
  basic: {
    id: 'Destination ID';
    type: 'city, beach, mountain, etc.';
    country: 'Country code';
    region: 'Region within country';
  };

  // Content
  content: {
    name: 'Destination name';
    description: 'Text description';
    tags: ['beach', 'cultural', 'adventure', 'family'];
    amenities: ['museums', 'nightlife', 'nature'];
  };

  // Attributes
  attributes: {
    popularity_score: '0-1';
    avg_rating: '0-5';
    review_count: 'Total reviews';
    seasonality: 'Best months array';
    avg_price: 'Average trip cost';
  };

  // Location
  location: {
    coordinates: { lat, lng };
    climate: 'tropical, temperate, cold, desert';
    terrain: 'coastal, mountain, urban, rural';
  };
}
```

### Feature Store

```typescript
// Feast feature store configuration

from feast import FeatureStore
from datetime import timedelta

# Define feature views
user_features_view = FeatureView(
    name="user_features",
    entities=["user_id"],
    features=[
        Field(name="booking_count", dtype=float),
        Field(name="avg_trip_value", dtype=float),
        Field(name="preferred_region", dtype=str),
        Field(name="travel_style", dtype=str),
    ],
    batch_source=BigQuerySource(
        query="SELECT * FROM user_features"
    ),
    ttl=timedelta(days=1),
)

destination_features_view = FeatureView(
    name="destination_features",
    entities=["destination_id"],
    features=[
        Field(name="popularity_score", dtype=float),
        Field(name="avg_rating", dtype=float),
        Field(name="tags", dtype=List[str]),
    ],
    batch_source=BigQuerySource(
        query="SELECT * FROM destination_features"
    ),
    ttl=timedelta(hours=6),
)

# Get features for inference
def get_user_features(user_id: str) -> dict:
    store = FeatureStore(repo_path=".")
    return store.get_online_features(
        features=["user_features:booking_count", "user_features:travel_style"],
        entity_rows=[{"user_id": user_id}],
    ).to_dict()
```

---

## Model Serving

### Serving Architecture

```typescript
// Model serving infrastructure

interface ServingInfrastructure {
  // Batch scoring
  batch: {
    use_case: 'Precompute recommendations for all users';
    schedule: 'Daily at 2 AM';
    storage: 'Redis (user recs) + S3 (backup)';
    freshness: 'Up to 24 hours old';
  };

  // Real-time scoring
  realtime: {
    use_case: 'Session-based, contextual recommendations';
    api: '/recommendations/{user_id}';
    latency: '<200ms p95';
    cache: 'Redis with 1-hour TTL';
  };

  // CDN serving
  cdn: {
    use_case: 'Static feeds (trending, popular)';
    storage: 'Cloudflare KV';
    ttl: '15 minutes';
    latency: '<50ms globally';
  };
}
```

### Recommendations API

```python
# FastAPI recommendations service

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import lightfm
from lightfm import LightFM

app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
model = LightFM.load('models/hybrid_model.pkl')

class RecommendationRequest(BaseModel):
    user_id: str
    item_id: str | None = None
    rec_type: str = 'personalized'
    limit: int = 10
    context: dict | None = None

class RecommendationResponse(BaseModel):
    recommendations: list[dict]
    model_version: str
    cached: bool

@app.post("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(user_id: str, request: RecommendationRequest):
    # Check cache first
    cache_key = f"recs:{user_id}:{request.rec_type}"
    cached = redis_client.get(cache_key)

    if cached:
        return RecommendationResponse(
            recommendations=json.loads(cached),
            model_version="v1.0",
            cached=True
        )

    # Generate recommendations
    if request.rec_type == 'personalized':
        recs = get_personalized_recs(user_id, request.limit)
    elif request.rec_type == 'similar':
        recs = get_similar_recs(request.item_id, request.limit)
    elif request.rec_type == 'trending':
        recs = get_trending_recs(request.limit)
    else:
        raise HTTPException(status_code=400, detail="Invalid rec_type")

    # Cache results
    redis_client.setex(
        cache_key,
        3600,  # 1 hour TTL
        json.dumps(recs)
    )

    return RecommendationResponse(
        recommendations=recs,
        model_version="v1.0",
        cached=False
    )

def get_personalized_recs(user_id: str, limit: int):
    # Get user features
    user_features = get_user_features(user_id)

    # Get item features
    item_features = get_all_item_features()

    # Score items
    scores = model.predict(
        user_id=user_map[user_id],
        item_ids=np.arange(len(item_features)),
        user_features=user_features,
        item_features=item_features,
    )

    # Get top items
    top_indices = np.argsort(-scores)[:limit]

    return [
        {
            'item_id': reverse_item_map[idx],
            'score': float(scores[idx]),
            'reason': 'Based on your travel history'
        }
        for idx in top_indices
    ]
```

---

## Evaluation Metrics

### Offline Metrics

```python
# Offline model evaluation

from lightfm.evaluation import precision_at_k, recall_at_k, auc_score

def evaluate_model(model, test_interactions, k=10):
    """Evaluate model using standard metrics"""

    metrics = {
        # Precision@K: How many recommended items are relevant
        'precision_at_k': precision_at_k(
            model, test_interactions, k=k
        ).mean(),

        # Recall@K: How many relevant items were recommended
        'recall_at_k': recall_at_k(
            model, test_interactions, k=k
        ).mean(),

        # AUC: Ranking quality
        'auc_score': auc_score(
            model, test_interactions
        ).mean(),

        # NDCG: Position-aware relevance
        'ndcg_at_k': ndcg_at_k(
            model, test_interactions, k=k
        ).mean(),
    }

    return metrics

# Business metrics
def calculate_business_metrics(recommendations, actual_bookings):
    """Calculate business-relevant metrics"""

    return {
        # Click-through rate
        'ctr': len(recommendations[recommendations.clicked]) / len(recommendations),

        # Conversion rate
        'conversion_rate': len(actual_bookings) / len(recommendations),

        # Average position of clicked items
        'avg_click_position': recommendations[recommendations.clicked].position.mean(),

        # Revenue per recommendation
        'revenue_per_rec': actual_bookings.revenue.sum() / len(recommendations),
    }
```

### Online Metrics

```typescript
// A/B testing framework

interface ABTestConfig {
  name: string;
  variants: {
    control: 'Current production model';
    treatment: 'New model variant';
  };
  metrics: ['ctr', 'conversion_rate', 'revenue_per_user'];
  duration: '14 days minimum';
  sample_size: 'Calculated for statistical significance';
}

// Track recommendations exposure
export function exposeRecommendation(
  userId: string,
  recommendations: Recommendation[],
  variant: string
) {
  analytics.track('recommendation_exposure', {
    user_id: userId,
    variant,
    rec_ids: recommendations.map((r) => r.id),
    model_version: recommendations[0]?.modelVersion,
    timestamp: Date.now(),
  });
}

// Track recommendation interactions
export function trackRecommendationInteraction(
  userId: string,
  recommendationId: string,
  interaction: 'click' | 'booking' | 'dismiss'
) {
  analytics.track('recommendation_interaction', {
    user_id: userId,
    recommendation_id: recommendationId,
    interaction,
    timestamp: Date.now(),
  });
}
```

---

## Summary

Recommendations engine architecture for the travel agency platform:

- **Types**: Similar items, personalized feed, trending, session-based, cross-sell
- **Pipeline**: Events → Feature store → Training → Model registry → Serving
- **Algorithms**: Hybrid collaborative filtering + content-based
- **Serving**: Batch (Redis) + Real-time (API) + CDN (static)
- **Evaluation**: Offline (precision@k, recall) + Online (A/B tests)

**Key Architectural Decisions:**
- LightFM for hybrid collaborative + content filtering
- Feast for feature management
- Redis for low-latency serving
- MLflow for model registry
- Snowplow for event tracking

---

**Next:** [Part 2: Collaborative Filtering](./RECOMMENDATIONS_ENGINE_02_COLLABORATIVE.md) — User-based and item-based algorithms
