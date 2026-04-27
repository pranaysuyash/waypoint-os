# Recommendations Engine Part 5: Real-Time Personalization

> Dynamic recommendations, contextual scoring, and online learning

**Series:** Recommendations Engine
**Previous:** [Part 4: Hybrid Approaches](./RECOMMENDATIONS_ENGINE_04_HYBRID.md)

---

## Table of Contents

1. [Real-Time Scoring Pipeline](#real-time-scoring-pipeline)
2. [Contextual Recommendations](#contextual-recommendations)
3. [Session-Based Recommendations](#session-based-recommendations)
4. [Exploration vs Exploitation](#exploration-vs-exploitation)
5. [Online Learning](#online-learning)

---

## Real-Time Scoring Pipeline

### Low-Latency Architecture

```python
# Real-time scoring service

from fastapi import FastAPI, BackgroundTasks
import redis
import json
from typing import List

app = FastAPI()

# Redis for caching and feature store
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class RealTimeScorer:
    """Low-latency recommendation scoring"""

    def __init__(self, model, feature_store):
        self.model = model
        self.feature_store = feature_store
        self.cache_ttl = 300  # 5 minutes

    async def score_items(
        self,
        user_id: str,
        item_ids: List[str],
        context: dict
    ) -> List[dict]:
        """
        Score items in real-time
        Target: <200ms p95
        """

        # Check cache first
        cache_key = f"scores:{user_id}:{hash(frozenset(context.items()))}"
        cached = redis_client.get(cache_key)

        if cached:
            return json.loads(cached)

        # Get user features (from Redis feature store)
        user_features = await self.feature_store.get_user_features(user_id)

        # Get item features (batch from Redis)
        item_features = await self.feature_store.get_batch_item_features(item_ids)

        # Score items
        scores = []
        for item_id in item_ids:
            if item_id not in item_features:
                continue

            # Merge user features, item features, and context
            features = {
                **user_features,
                **item_features[item_id],
                **context
            }

            # Predict score
            score = self.model.predict(features)

            scores.append({
                'item_id': item_id,
                'score': float(score)
            })

        # Sort by score
        scores.sort(key=lambda x: x['score'], reverse=True)

        # Cache results
        redis_client.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(scores)
        )

        return scores

scorer = RealTimeScorer(model, feature_store)

@app.post("/recommendations/{user_id}")
async def get_recommendations(
    user_id: str,
    context: dict,
    n: int = 10
):
    """Get real-time recommendations"""

    # Get candidate items (pre-filtered)
    candidate_ids = await get_candidate_items(user_id, context)

    # Score in real-time
    scored_items = await scorer.score_items(user_id, candidate_ids, context)

    # Return top n
    return {
        'user_id': user_id,
        'recommendations': scored_items[:n],
        'timestamp': time.time()
    }
```

### Feature Store Integration

```python
# Redis-based feature store for real-time access

class RedisFeatureStore:
    """Real-time feature store using Redis"""

    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)

    async def get_user_features(self, user_id: str) -> dict:
        """Get user features with low latency"""

        # Try cache first
        cache_key = f"user_features:{user_id}"
        cached = self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Fetch from database or compute
        features = await self._fetch_user_features(user_id)

        # Cache with TTL
        self.redis.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(features)
        )

        return features

    async def get_batch_item_features(self, item_ids: List[str]) -> dict:
        """Batch get item features"""

        # Pipeline for efficiency
        pipe = self.redis.pipeline()

        for item_id in item_ids:
            pipe.get(f"item_features:{item_id}")

        results = pipe.execute()

        features = {}
        for item_id, result in zip(item_ids, results):
            if result:
                features[item_id] = json.loads(result)
            else:
                # Miss: fetch and cache
                item_features = await self._fetch_item_features(item_id)
                features[item_id] = item_features

                # Cache
                self.redis.setex(
                    f"item_features:{item_id}",
                    7200,  # 2 hours
                    json.dumps(item_features)
                )

        return features

    async def update_user_features(self, user_id: str, features: dict):
        """Update user features in real-time"""

        cache_key = f"user_features:{user_id}"

        # Merge with existing
        existing = await self.get_user_features(user_id)
        merged = {**existing, **features}

        # Update cache
        self.redis.setex(
            cache_key,
            3600,
            json.dumps(merged)
        )

        # Also persist to database
        await self._persist_user_features(user_id, merged)
```

---

## Contextual Recommendations

### Context Features

```python
# Context-aware recommendation scoring

class ContextualScorer:
    """Score items based on user context"""

    def __init__(self, base_model):
        self.base_model = base_model

    def score_with_context(
        self,
        user_id: str,
        item_id: str,
        context: dict
    ) -> float:
        """
        context: {
            'time_of_day': 'morning', 'afternoon', 'evening',
            'day_of_week': 'weekday', 'weekend',
            'season': 'summer', 'winter', etc.,
            'device': 'mobile', 'desktop',
            'location': 'home', 'destination',
            'travel_phase': 'searching', 'planning', 'booking',
            'companions': 'solo', 'couple', 'family', 'group'
        }
        """

        # Get base score
        base_score = self.base_model.predict(user_id, item_id)

        # Apply context modifiers
        modifiers = self._get_context_modifiers(item_id, context)

        # Final score = base * product of modifiers
        final_score = base_score
        for modifier in modifiers.values():
            final_score *= modifier

        return final_score

    def _get_context_modifiers(self, item_id: str, context: dict) -> dict:
        """Calculate context-specific modifiers"""

        modifiers = {}

        # Time of day modifier
        if context.get('time_of_day') == 'evening':
            # Boost romantic destinations in evening
            if self._is_romantic(item_id):
                modifiers['evening'] = 1.2

        # Season modifier
        season = context.get('season')
        if season and self._is_best_season(item_id, season):
            modifiers['season'] = 1.3

        # Device modifier
        if context.get('device') == 'mobile':
            # Boost bookable activities on mobile
            if self._is_bookable_activity(item_id):
                modifiers['mobile'] = 1.15

        # Travel phase modifier
        phase = context.get('travel_phase')
        if phase == 'booking':
            # Boost high-conversion items
            if self._has_high_conversion(item_id):
                modifiers['booking'] = 1.25
        elif phase == 'searching':
            # Boost discovery items
            if self._is_discovery_focused(item_id):
                modifiers['searching'] = 1.1

        return modifiers

    def _is_romantic(self, item_id: str) -> bool:
        """Check if item is romantic"""
        # Look up item tags
        tags = self._get_item_tags(item_id)
        return 'romantic' in tags or 'honeymoon' in tags

    def _is_best_season(self, item_id: str, season: str) -> bool:
        """Check if season is best for destination"""
        best_seasons = self._get_best_seasons(item_id)
        return season in best_seasons
```

### Location-Aware Recommendations

```python
# Geo-contextual recommendations

class LocationAwareRecommender:
    """Recommendations based on user's location"""

    def __init__(self, base_recommender, geo_index):
        self.base_recommender = base_recommender
        self.geo_index = geo_index  # Spatial index for destinations

    def recommend(
        self,
        user_id: str,
        user_location: dict,  # {'lat': float, 'lng': float}
        n_recommendations: int = 10
    ) -> List[dict]:

        # Get base recommendations
        base_recs = self.base_recommender.recommend(user_id, n_recommendations * 2)

        # Add distance-based boosting
        for rec in base_recs:
            item_location = self._get_item_location(rec['item_id'])

            if item_location:
                # Calculate distance
                distance = self._calculate_distance(
                    user_location,
                    item_location
                )

                # Apply distance modifier
                # Closer items get boosted
                if distance < 100:  # Within 100km
                    rec['score'] *= 1.3
                elif distance < 500:  # Within 500km
                    rec['score'] *= 1.1
                elif distance > 2000:  # Far away
                    rec['score'] *= 0.9

                rec['distance'] = distance

        # Sort by modified score
        base_recs.sort(key=lambda x: x['score'], reverse=True)

        return base_recs[:n_recommendations]

    def _calculate_distance(self, loc1: dict, loc2: dict) -> float:
        """Calculate distance between two locations in km"""

        from geopy.distance import geodesic

        return geodesic(
            (loc1['lat'], loc1['lng']),
            (loc2['lat'], loc2['lng'])
        ).kilometers
```

---

## Session-Based Recommendations

### Session Modeling

```python
# Session-based recommendations using RNN/Transformer

import numpy as np
from typing import List

class SessionRecommender:
    """Recommend based on current browsing session"""

    def __init__(self, model, item_encoder):
        self.model = model
        self.item_encoder = item_encoder

    def recommend_from_session(
        self,
        session_items: List[str],
        n_recommendations: int = 10
    ) -> List[dict]:

        # Encode session items
        session_sequence = [
            self.item_encoder.encode(item_id)
            for item_id in session_items[-10:]  # Last 10 items
        ]

        # Pad if needed
        if len(session_sequence) < 10:
            session_sequence.extend([0] * (10 - len(session_sequence)))

        # Predict next items
        scores = self.model.predict(np.array([session_sequence]))[0]

        # Get top items
        top_indices = np.argsort(-scores)[:n_recommendations]

        # Filter out items already in session
        viewed_ids = set(session_items)
        recommendations = []

        for idx in top_indices:
            item_id = self.item_encoder.decode(idx)
            if item_id not in viewed_ids:
                recommendations.append({
                    'item_id': item_id,
                    'score': float(scores[idx])
                })

            if len(recommendations) >= n_recommendations:
                break

        return recommendations

# Real-time session updates
class SessionTracker:
    """Track and update session in real-time"""

    def __init__(self):
        self.sessions = {}

    def add_event(self, session_id: str, item_id: str, event_type: str):
        """Add event to session"""

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'items': [],
                'events': [],
                'start_time': time.time()
            }

        session = self.sessions[session_id]

        # Track item sequence
        if event_type in ['view', 'click']:
            session['items'].append(item_id)

        # Track events
        session['events'].append({
            'item_id': item_id,
            'type': event_type,
            'timestamp': time.time()
        })

        # Update in Redis for persistence
        self._persist_session(session_id)

    def get_session_items(self, session_id: str) -> List[str]:
        """Get items in current session"""

        session = self.sessions.get(session_id)
        if session:
            return session['items']

        # Try loading from Redis
        return self._load_session(session_id)

    def _persist_session(self, session_id: str):
        """Save session to Redis"""

        key = f"session:{session_id}"
        data = json.dumps(self.sessions[session_id])

        redis_client.setex(key, 3600, data)  # 1 hour TTL
```

### Real-Time Session Recommendations

```python
# Update recommendations as session evolves

from fastapi import WebSocket, WebSocketDisconnect

class RealTimeSessionRecommender:
    """WebSocket-based real-time recommendations"""

    def __init__(self, session_recommender, session_tracker):
        self.recommender = session_recommender
        self.tracker = session_tracker

    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        await websocket.accept()

        try:
            while True:
                # Receive event
                data = await websocket.receive_json()
                event_type = data.get('type')
                item_id = data.get('item_id')

                # Update session
                self.tracker.add_event(session_id, item_id, event_type)

                # Get updated recommendations
                session_items = self.tracker.get_session_items(session_id)

                if session_items:
                    recommendations = self.recommender.recommend_from_session(
                        session_items
                    )

                    # Send to client
                    await websocket.send_json({
                        'type': 'recommendations_update',
                        'recommendations': recommendations,
                        'trigger_event': event_type
                    })

        except WebSocketDisconnect:
            print(f"Session {session_id} disconnected")

# WebSocket endpoint
@app.websocket("/ws/recommendations/{session_id}")
async def recommendations_websocket(
    websocket: WebSocket,
    session_id: str
):
    handler = RealTimeSessionRecommender(session_recommender, session_tracker)
    await handler.handle_websocket(websocket, session_id)
```

---

## Exploration vs Exploitation

### Epsilon-Greedy Strategy

```python
# Balance exploration and exploitation

import numpy as np

class ExplorationExploitation:
    """Manage exploration-exploitation tradeoff"""

    def __init__(
        self,
        recommenders,
        epsilon=0.1,
        epsilon_decay=0.995,
        min_epsilon=0.05
    ):
        """
        recommenders: dict of strategies
        epsilon: Initial exploration rate
        """
        self.recommenders = recommenders
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon

    def recommend(self, user_id, n_recommendations=10):
        """Recommend with exploration"""

        # Decide: explore or exploit?
        if np.random.random() < self.epsilon:
            # Explore: try different strategies
            strategy = np.random.choice(list(self.recommenders.keys()))
            exploration = True
        else:
            # Exploit: use best known strategy
            strategy = self.get_best_strategy(user_id)
            exploration = False

        # Get recommendations
        recommender = self.recommenders[strategy]
        recommendations = recommender.recommend(user_id, n_recommendations)

        # Add metadata
        for rec in recommendations:
            rec['strategy'] = strategy
            rec['exploration'] = exploration

        return recommendations

    def record_outcome(self, user_id, item_id, outcome):
        """Record outcome and update strategy performance"""

        strategy = item_id.get('strategy')
        if strategy:
            # Update strategy performance tracking
            self._update_strategy_performance(
                user_id,
                strategy,
                outcome
            )

        # Decay exploration rate
        self.epsilon = max(
            self.min_epsilon,
            self.epsilon * self.epsilon_decay
        )

    def get_best_strategy(self, user_id: str) -> str:
        """Get best performing strategy for user"""

        # Calculate average reward per strategy
        strategy_rewards = {}

        for strategy in self.recommenders:
            rewards = self._get_strategy_rewards(user_id, strategy)
            if rewards:
                strategy_rewards[strategy] = np.mean(rewards)
            else:
                strategy_rewards[strategy] = 0

        # Return best strategy
        return max(strategy_rewards, key=strategy_rewards.get)
```

### Thompson Sampling

```python
# Bayesian approach to exploration

class ThompsonSamplingBandit:
    """Thompson sampling for strategy selection"""

    def __init__(self, strategies):
        """
        strategies: dict of {name: recommender}
        """
        self.strategies = strategies

        # Beta distribution parameters for each strategy
        # alpha = successes + 1, beta = failures + 1
        self.alpha = {name: 1 for name in strategies}
        self.beta = {name: 1 for name in strategies}

    def select_strategy(self) -> str:
        """Select strategy using Thompson sampling"""

        samples = {}
        for name in self.strategies:
            # Sample from Beta distribution
            samples[name] = np.random.beta(self.alpha[name], self.beta[name])

        # Select strategy with highest sample
        return max(samples, key=samples.get)

    def recommend(self, user_id, n_recommendations=10):
        """Recommend using Thompson-sampled strategy"""

        strategy = self.select_strategy()
        recommender = self.strategies[strategy]

        recommendations = recommender.recommend(user_id, n_recommendations)

        # Add strategy info
        for rec in recommendations:
            rec['strategy'] = strategy
            rec['thompson_sample'] = self.alpha[strategy] / (
                self.alpha[strategy] + self.beta[strategy]
            )

        return recommendations

    def update(self, strategy: str, reward: float):
        """Update parameters based on reward"""

        # Convert reward to binary (success/failure)
        success = 1 if reward > 0 else 0

        if success:
            self.alpha[strategy] += 1
        else:
            self.beta[strategy] += 1
```

### Diversity Injection

```python
# Ensure diverse recommendations

class DiverseRecommender:
    """Inject diversity into recommendations"""

    def __init__(self, base_recommender, diversity_threshold=0.7):
        self.base_recommender = base_recommender
        self.diversity_threshold = diversity_threshold

    def recommend(self, user_id, n_recommendations=10):
        """Get diverse recommendations"""

        # Get larger pool of candidates
        candidates = self.base_recommender.recommend(
            user_id,
            n_recommendations * 3
        )

        diverse_recs = []
        excluded_categories = set()

        for rec in candidates:
            # Check similarity to already selected
            if self._is_too_similar(rec, diverse_recs):
                continue

            # Check category diversity
            category = self._get_category(rec['item_id'])
            if category in excluded_categories:
                continue

            diverse_recs.append(rec)

            # Exclude similar categories for future picks
            excluded_categories.update(
                self._get_related_categories(category)
            )

            if len(diverse_recs) >= n_recommendations:
                break

        return diverse_recs

    def _is_too_similar(self, rec, existing_recs) -> bool:
        """Check if recommendation is too similar to existing"""

        for existing in existing_recs:
            similarity = self._calculate_similarity(
                rec['item_id'],
                existing['item_id']
            )

            if similarity > self.diversity_threshold:
                return True

        return False
```

---

## Online Learning

### Incremental Model Updates

```python
# Update model in real-time

from river import compose
from river import linear_model
from river import preprocessing
from river import metrics

class OnlineLearningRecommender:
    """Incrementally update model from new data"""

    def __init__(self):
        # Build online model pipeline
        self.model = compose.Pipeline(
            preprocessing.StandardScaler(),
            linear_model.LogisticRegression()
        )

        self.metric = metrics.Accuracy()

    def learn_one(self, user_id: str, item_id: str, clicked: bool):
        """Learn from a single interaction"""

        # Extract features
        features = self._extract_features(user_id, item_id)

        # Update model
        self.model.learn_one(features, clicked)

        # Update metric
        y_pred = self.model.predict_one(features)
        self.metric = self.metric.update(clicked, y_pred)

    def predict_proba_one(
        self,
        user_id: str,
        item_id: str
    ) -> float:
        """Predict click probability"""

        features = self._extract_features(user_id, item_id)
        return self.model.predict_proba_one(features).get(True, 0.0)

    def recommend(
        self,
        user_id: str,
        candidate_items: List[str],
        n_recommendations: int = 10
    ) -> List[dict]:

        # Score all candidates
        scores = []
        for item_id in candidate_items:
            proba = self.predict_proba_one(user_id, item_id)
            scores.append({
                'item_id': item_id,
                'score': proba
            })

        # Sort by score
        scores.sort(key=lambda x: x['score'], reverse=True)

        return scores[:n_recommendations]
```

### Real-Time Feature Updates

```python
# Update user profile in real-time

class RealTimeUserProfile:
    """Maintain and update user profile from events"""

    def __init__(self, feature_store):
        self.feature_store = feature_store

    async def on_event(self, event: dict):
        """Handle real-time event"""

        user_id = event['user_id']
        event_type = event['type']
        item_id = event.get('item_id')

        # Update user profile based on event
        if event_type == 'click':
            await self._update_from_click(user_id, item_id)
        elif event_type == 'booking':
            await self._update_from_booking(user_id, item_id)
        elif event_type == 'search':
            await self._update_from_search(user_id, event.get('query'))

    async def _update_from_click(self, user_id: str, item_id: str):
        """Update profile from click event"""

        # Get item features
        item_features = await self.feature_store.get_item_features(item_id)

        # Update user's interest scores
        for tag in item_features.get('tags', []):
            await self._increment_interest(user_id, f'tag:{tag}', 0.1)

        for category in item_features.get('categories', []):
            await self._increment_interest(user_id, f'category:{category}', 0.15)

    async def _increment_interest(
        self,
        user_id: str,
        feature: str,
        amount: float
    ):
        """Increment interest score for feature"""

        # Update in Redis
        key = f"user_interests:{user_id}:{feature}"
        current = float(redis_client.get(key) or 0)
        redis_client.set(key, str(min(1.0, current + amount)))

    async def get_interests(self, user_id: str) -> dict:
        """Get user's current interests"""

        # Scan all interest keys for user
        pattern = f"user_interests:{user_id}:*"
        keys = redis_client.keys(pattern)

        interests = {}
        for key in keys:
            feature = key.split(':')[-1]
            score = float(redis_client.get(key) or 0)
            if score > 0.01:  # Only return significant interests
                interests[feature] = score

        return interests
```

---

## Summary

Real-time personalization for the travel agency platform:

- **Scoring**: <200ms latency with Redis feature store
- **Context**: Time, season, device, location modifiers
- **Session**: RNN-based session recommendations
- **Exploration**: Epsilon-greedy, Thompson sampling
- **Online**: Incremental model updates, real-time profile updates

**Key Real-Time Decisions:**
- Redis for sub-millisecond feature lookups
- WebSocket for live session updates
- Context modifiers for dynamic scoring
- Thompson sampling for exploration
- River library for online learning

---

**Series Complete:** [Recommendations Engine Master Index](./RECOMMENDATIONS_ENGINE_MASTER_INDEX.md)
