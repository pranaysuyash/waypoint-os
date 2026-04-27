# Recommendations Engine Part 4: Hybrid Approaches

> Combining algorithms, ensemble methods, and meta-recommendations

**Series:** Recommendations Engine
**Previous:** [Part 3: Content-Based Filtering](./RECOMMENDATIONS_ENGINE_03_CONTENT_BASED.md)
**Next:** [Part 5: Real-Time Personalization](./RECOMMENDATIONS_ENGINE_05_REALTIME.md)

---

## Table of Contents

1. [Weighted Hybrid](#weighted-hybrid)
2. [Switching Hybrid](#switching-hybrid)
3. [Ensemble Methods](#ensemble-methods)
4. [LightFM Implementation](#lightfm-implementation)
5. [Meta-Recommendations](#meta-recommendations)

---

## Weighted Hybrid

### Linear Combination

```python
# Weighted combination of multiple recommenders

class WeightedHybridRecommender:
    """Combine multiple recommenders with fixed weights"""

    def __init__(self, recommenders, weights):
        """
        recommenders: dict of {name: recommender_instance}
        weights: dict of {name: weight}
        """
        self.recommenders = recommenders
        self.weights = weights

        # Validate weights sum to 1
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")

    def recommend(self, user_id, n_recommendations=10):
        """Get hybrid recommendations"""

        # Get recommendations from each recommender
        all_recommendations = {}

        for name, recommender in self.recommenders.items():
            weight = self.weights[name]

            try:
                recs = recommender.recommend(user_id, n_recommendations * 2)

                # Apply weight and aggregate
                for rec in recs:
                    item_id = rec['item_id']
                    score = rec.get('score', rec.get('similarity', 0))

                    if item_id not in all_recommendations:
                        all_recommendations[item_id] = {
                            'item_id': item_id,
                            'score': 0,
                            'reasons': [],
                            'components': {}
                        }

                    all_recommendations[item_id]['score'] += score * weight
                    all_recommendations[item_id]['components'][name] = score
                    all_recommendations[item_id]['reasons'].append(
                        rec.get('reason', f'{name} recommendation')
                    )

            except Exception as e:
                print(f"Error from {name}: {e}")
                continue

        # Sort by combined score
        recommendations = sorted(
            all_recommendations.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:n_recommendations]

        return recommendations

# Usage
hybrid = WeightedHybridRecommender(
    recommenders={
        'collaborative': collaborative_filtering,
        'content_based': content_based,
        'popular': popularity_based
    },
    weights={
        'collaborative': 0.5,
        'content_based': 0.3,
        'popular': 0.2
    }
)
```

### Dynamic Weighting

```python
# Adjust weights based on context

class DynamicWeightedHybrid:
    """Adjust weights based on user context and performance"""

    def __init__(self, recommenders, base_weights):
        self.recommenders = recommenders
        self.base_weights = base_weights
        self.context_modifiers = {
            'cold_start': {'collaborative': -0.3, 'content_based': 0.2, 'popular': 0.1},
            'power_user': {'collaborative': 0.2, 'content_based': -0.1, 'popular': -0.1},
            'new_destination': {'collaborative': -0.2, 'content_based': 0.2},
        }

    def get_weights(self, user_context):
        """Calculate weights based on context"""

        weights = self.base_weights.copy()

        # Apply context modifiers
        for context, modifiers in self.context_modifiers.items():
            if user_context.get(context):
                for name, delta in modifiers.items():
                    weights[name] = weights.get(name, 0) + delta

        # Normalize to sum to 1
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        # Clip negative weights
        weights = {k: max(0, v) for k, v in weights.items()}

        # Renormalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def recommend(self, user_id, user_context, n_recommendations=10):
        """Get recommendations with dynamic weighting"""

        # Calculate weights
        weights = self.get_weights(user_context)

        # Get recommendations with current weights
        hybrid = WeightedHybridRecommender(self.recommenders, weights)
        recommendations = hybrid.recommend(user_id, n_recommendations)

        # Add weight info
        for rec in recommendations:
            rec['weights_used'] = weights

        return recommendations
```

---

## Switching Hybrid

### Context-Based Switching

```python
# Switch between recommenders based on context

class SwitchingHybridRecommender:
    """Use different recommenders for different contexts"""

    def __init__(self):
        self.recommenders = {}
        self.context_rules = []

    def register_recommender(self, name, recommender):
        """Register a recommender"""
        self.recommenders[name] = recommender

    def add_rule(self, condition, recommender_name):
        """
        Add a switching rule
        condition: callable that takes user_context and returns bool
        """
        self.context_rules.append((condition, recommender_name))

    def recommend(self, user_id, user_context, n_recommendations=10):
        """Get recommendations using appropriate recommender"""

        # Find matching rule
        selected_recommender = None

        for condition, recommender_name in self.context_rules:
            if condition(user_context):
                selected_recommender = self.recommenders[recommender_name]
                break

        # Fallback to default
        if selected_recommender is None:
            selected_recommender = self.recommenders.get('default')

        if selected_recommender is None:
            raise ValueError("No recommender available for context")

        # Get recommendations
        recommendations = selected_recommender.recommend(user_id, n_recommendations)

        # Add source info
        for rec in recommendations:
            rec['source'] = selected_recommender.__class__.__name__

        return recommendations

# Usage
switching = SwitchingHybridRecommender()

# Register recommenders
switching.register_recommender('collaborative', cf_recommender)
switching.register_recommender('content', cb_recommender)
switching.register_recommender('popular', pop_recommender)
switching.register_recommender('default', hybrid_recommender)

# Add rules
switching.add_rule(
    condition=lambda ctx: ctx.get('interaction_count', 0) < 5,
    recommender_name='popular'  # Cold start: use popular
)

switching.add_rule(
    condition=lambda ctx: ctx.get('interaction_count', 0) >= 50,
    recommender_name='collaborative'  # Power users: collaborative
)

switching.add_rule(
    condition=lambda ctx: ctx.get('viewing_new_item', False),
    recommender_name='content'  # New item: content-based
)
```

### Confidence-Based Switching

```python
# Switch based on recommender confidence

class ConfidenceBasedSwitching:
    """Use the recommender with highest confidence"""

    def __init__(self, recommenders):
        self.recommenders = recommenders

    def recommend(self, user_id, n_recommendations=10):
        """Get recommendations from most confident recommender"""

        results = {}

        # Get recommendations and confidence from each
        for name, recommender in self.recommenders.items():
            try:
                recs = recommender.recommend(user_id, n_recommendations)

                # Calculate confidence
                confidence = self._calculate_confidence(recs, name)

                results[name] = {
                    'recommendations': recs,
                    'confidence': confidence
                }

            except Exception as e:
                print(f"{name} failed: {e}")
                continue

        # Select highest confidence
        if not results:
            return []

        best_name = max(results.keys(), key=lambda k: results[k]['confidence'])
        best_result = results[best_name]

        # Add source info
        for rec in best_result['recommendations']:
            rec['source'] = best_name
            rec['confidence'] = best_result['confidence']

        return best_result['recommendations']

    def _calculate_confidence(self, recommendations, recommender_name):
        """Calculate confidence score for recommendations"""

        if not recommendations:
            return 0.0

        # Different confidence calculations per recommender
        if recommender_name == 'collaborative':
            # Confidence based on user interaction count
            user_interactions = self._get_user_interaction_count()
            return min(1.0, user_interactions / 50)

        elif recommender_name == 'content_based':
            # Confidence based on content similarity spread
            scores = [r.get('similarity', 0) for r in recommendations]
            if not scores:
                return 0.0

            # High spread = high confidence
            return max(scores) - min(scores)

        else:
            # Default confidence
            return 0.5
```

---

## Ensemble Methods

### Stacking Ensemble

```python
# Stack multiple recommenders with a meta-learner

from sklearn.ensemble import GradientBoostingRegressor
import numpy as np

class StackingEnsemble:
    """Stack recommenders and learn to combine their predictions"""

    def __init__(self, base_recommenders):
        """
        base_recommenders: list of (name, recommender) tuples
        """
        self.base_recommenders = dict(base_recommenders)
        self.meta_learner = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1
        )
        self.is_fitted = False

    def fit(self, training_pairs):
        """
        Train meta-learner on past recommendations
        training_pairs: list of (user_id, item_id, outcome) tuples
        outcome: 1 for positive (booked/clicked), 0 for negative (shown/ignored)
        """
        # Collect base model predictions
        X = []
        y = []

        for user_id, item_id, outcome in training_pairs:
            features = []

            # Get predictions from each base recommender
            for name, recommender in self.base_recommenders.items():
                try:
                    recs = recommender.recommend(user_id, n_recommendations=100)

                    # Find score for this item
                    score = 0
                    for rec in recs:
                        if rec['item_id'] == item_id:
                            score = rec.get('score', rec.get('similarity', 0))
                            break

                    features.append(score)

                except Exception:
                    features.append(0)

            X.append(features)
            y.append(outcome)

        # Train meta-learner
        X = np.array(X)
        y = np.array(y)

        self.meta_learner.fit(X, y)
        self.is_fitted = True

    def recommend(self, user_id, n_recommendations=10):
        """Get ensemble recommendations"""

        if not self.is_fitted:
            raise ValueError("Ensemble not fitted. Call fit() first.")

        # Get candidate items (from all recommenders)
        candidate_items = set()

        for recommender in self.base_recommenders.values():
            try:
                recs = recommender.recommend(user_id, n_recommendations * 3)
                for rec in recs:
                    candidate_items.add(rec['item_id'])
            except Exception:
                continue

        # Score each candidate with ensemble
        scored_items = []

        for item_id in candidate_items:
            # Get base model scores
            features = []

            for name, recommender in self.base_recommenders.items():
                try:
                    recs = recommender.recommend(user_id, n_recommendations=100)

                    score = 0
                    for rec in recs:
                        if rec['item_id'] == item_id:
                            score = rec.get('score', rec.get('similarity', 0))
                            break

                    features.append(score)

                except Exception:
                    features.append(0)

            # Predict with meta-learner
            ensemble_score = self.meta_learner.predict([features])[0]

            scored_items.append({
                'item_id': item_id,
                'score': float(ensemble_score)
            })

        # Return top items
        scored_items.sort(key=lambda x: x['score'], reverse=True)

        return scored_items[:n_recommendations]
```

### Rank Fusion

```python
# Combine rankings from multiple recommenders

from collections import defaultdict

class ReciprocalRankFusion:
    """Combine rankings using Reciprocal Rank Fusion"""

    def __init__(self, k=60):
        """
        k: Constant that prevents highly ranked items from dominating
        """
        self.k = k

    def recommend(self, user_id, recommenders, n_recommendations=10):
        """
        recommenders: dict of {name: (recommender, weight)}
        """

        # Collect rankings
        all_rankings = {}

        for name, (recommender, weight) in recommenders.items():
            try:
                recs = recommender.recommend(user_id, n_recommendations * 2)

                for rank, rec in enumerate(recs):
                    item_id = rec['item_id']

                    if item_id not in all_rankings:
                        all_rankings[item_id] = {
                            'item_id': item_id,
                            'score': 0,
                            'sources': []
                        }

                    # RRF formula: weight / (k + rank)
                    contribution = weight / (self.k + rank + 1)
                    all_rankings[item_id]['score'] += contribution
                    all_rankings[item_id]['sources'].append(name)

            except Exception as e:
                print(f"Error from {name}: {e}")
                continue

        # Sort by combined score
        recommendations = sorted(
            all_rankings.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:n_recommendations]

        return recommendations

# Usage
rrf = ReciprocalRankFusion(k=60)

recommendations = rrf.recommend(
    user_id='user_123',
    recommenders={
        'collaborative': (cf_recommender, 1.0),
        'content': (cb_recommender, 0.8),
        'popular': (pop_recommender, 0.5)
    }
)
```

---

## LightFM Implementation

### Hybrid Model Training

```python
# LightFM hybrid collaborative + content filtering

from lightfm import LightFM
from lightfm.data import Dataset
import numpy as np

class LightFMHybridRecommender:
    """
    LightFM combines:
    - Collaborative filtering (user-item interactions)
    - Content features (user and item features)
    """

    def __init__(self, no_components=30, loss='warp'):
        self.no_components = no_components
        self.loss = loss
        self.model = None
        self.dataset = None
        self.user_mapping = {}
        self.item_mapping = {}

    def fit(
        self,
        interactions,
        user_features=None,
        item_features=None,
        epochs=20
    ):
        """
        interactions: list of (user_id, item_id) tuples
        user_features: dict of {user_id: {feature_name: value}}
        item_features: dict of {item_id: {feature_name: value}}
        """

        # Create dataset
        self.dataset = Dataset()
        self.dataset.fit(
            users=set(u for u, _ in interactions),
            items=set(i for _, i in interactions),
            user_features=set(f for u in user_features for f in user_features[u].keys()) if user_features else set(),
            item_features=set(f for i in item_features for f in item_features[i].keys()) if item_features else set()
        )

        # Build mappings
        self.user_mapping = self.dataset.mapping()[0]
        self.item_mapping = self.dataset.mapping()[2]

        # Build interaction matrix
        (interactions_matrix, weights) = self.dataset.build_interactions(
            [(self.user_mapping[u], self.item_mapping[i]) for u, i in interactions]
        )

        # Build feature matrices
        user_feature_matrix = None
        if user_features:
            user_feature_matrix = self._build_feature_matrix(
                user_features,
                self.user_mapping,
                'user'
            )

        item_feature_matrix = None
        if item_features:
            item_feature_matrix = self._build_feature_matrix(
                item_features,
                self.item_mapping,
                'item'
            )

        # Initialize and train model
        self.model = LightFM(
            no_components=self.no_components,
            loss=self.loss,
            user_alpha=0.01,
            item_alpha=0.01,
            learning_rate=0.05,
            random_state=42
        )

        self.model.fit(
            interactions_matrix,
            user_features=user_feature_matrix,
            item_features=item_feature_matrix,
            epochs=epochs,
            num_threads=4,
            verbose=True
        )

        return self

    def _build_feature_matrix(self, features, mapping, feature_type):
        """Build feature matrix for LightFM"""

        feature_names = set()
        for item in features.values():
            feature_names.update(item.keys())

        # Fit features in dataset
        if feature_type == 'user':
            self.dataset.fit_user_features(features_list=feature_names)
        else:
            self.dataset.fit_item_features(features_list=feature_names)

        # Build feature matrix
        feature_tuples = []
        for id_, feats in features.items():
            idx = mapping.get(id_)
            if idx is None:
                continue

            for feature_name, value in feats.items():
                feature_tuples.append((idx, feature_name, value))

        return self.dataset.build_features(feature_tuples)

    def recommend(self, user_id, n_recommendations=10, item_features=None):
        """Get recommendations for user"""

        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")

        user_idx = self.user_mapping.get(user_id)
        if user_idx is None:
            # Handle cold start
            return self._cold_start_recommendations(user_id, n_recommendations)

        # Build item feature matrix if provided
        item_feature_matrix = None
        if item_features:
            item_feature_matrix = self._build_feature_matrix(
                item_features,
                self.item_mapping,
                'item'
            )

        # Score all items
        n_items = len(self.item_mapping)
        scores = self.model.predict(
            user_idx,
            np.arange(n_items),
            item_features=item_feature_matrix
        )

        # Get user's interacted items
        user_interactions = self._get_user_interactions(user_id)
        interacted_indices = [
            self.item_mapping[i] for i in user_interactions
            if i in self.item_mapping
        ]

        # Mask interacted items
        scores[interacted_indices] = -np.inf

        # Get top items
        top_indices = np.argsort(-scores)[:n_recommendations]

        # Map back to item IDs
        reverse_item_map = {v: k for k, v in self.item_mapping.items()}

        return [
            {
                'item_id': reverse_item_map[idx],
                'score': float(scores[idx]),
                'explanation': self._explain_recommendation(user_id, reverse_item_map[idx])
            }
            for idx in top_indices
        ]

    def _explain_recommendation(self, user_id, item_id):
        """Generate explanation for recommendation"""

        # Check if similar users liked this
        similar_users = self._find_similar_users(user_id, k=5)
        if similar_users:
            return f"Travelers like you enjoyed this destination"

        # Check content similarity
        return f"Based on your travel preferences"

    def _cold_start_recommendations(self, user_id, n_recommendations):
        """Handle cold start users"""

        # Fall back to popular items
        return get_popular_items(n_recommendations)
```

---

## Meta-Recommendations

### Two-Stage Recommendation

```python
# Meta-recommendation: recommend recommendation types

class MetaRecommender:
    """Predict which recommendation strategy to use"""

    def __init__(self, strategies):
        """
        strategies: dict of {name: recommender}
        """
        self.strategies = strategies
        self.strategy_selector = None

    def train_selector(self, user_outcomes):
        """
        Train a model to select the best strategy
        user_outcomes: list of {
            user_id,
            user_features,
            strategy_used,
            outcome (click, booking, etc.)
        }
        """

        from sklearn.ensemble import RandomForestClassifier

        X = []
        y = []

        for outcome in user_outcomes:
            features = list(outcome['user_features'].values())
            strategy = outcome['strategy_used']

            X.append(features)
            y.append(strategy)

        # Train strategy selector
        self.strategy_selector = RandomForestClassifier(
            n_estimators=100,
            max_depth=10
        )

        self.strategy_selector.fit(X, y)

    def recommend(self, user_id, user_features, n_recommendations=10):
        """Select and use best strategy"""

        if self.strategy_selector is None:
            # Default to first strategy
            selected_strategy = list(self.strategies.keys())[0]
        else:
            # Predict best strategy
            features = list(user_features.values())
            selected_strategy = self.strategy_selector.predict([features])[0]

        # Get recommendations from selected strategy
        recommender = self.strategies[selected_strategy]
        recommendations = recommender.recommend(user_id, n_recommendations)

        # Add meta info
        for rec in recommendations:
            rec['strategy_used'] = selected_strategy

        return recommendations
```

### Bandit Strategy Selection

```python
# Multi-armed bandit for online strategy selection

import numpy as np

class BanditStrategySelector:
    """Use bandit algorithm to select recommendation strategy"""

    def __init__(self, strategies, epsilon=0.1):
        """
        strategies: dict of {name: recommender}
        epsilon: Exploration rate for epsilon-greedy
        """
        self.strategies = strategies
        self.epsilon = epsilon

        # Track rewards for each strategy
        self.counts = {name: 0 for name in strategies}
        self.rewards = {name: 0.0 for name in strategies}

    def select_strategy(self):
        """Select strategy using epsilon-greedy"""

        if np.random.random() < self.epsilon:
            # Explore: random strategy
            return np.random.choice(list(self.strategies.keys()))
        else:
            # Exploit: best strategy
            avg_rewards = {
                name: (self.rewards[name] / self.counts[name] if self.counts[name] > 0 else 0)
                for name in self.strategies
            }
            return max(avg_rewards, key=avg_rewards.get)

    def update(self, strategy_name, reward):
        """Update strategy statistics"""

        self.counts[strategy_name] += 1
        self.rewards[strategy_name] += reward

    def recommend(self, user_id, n_recommendations=10):
        """Get recommendations using bandit-selected strategy"""

        # Select strategy
        strategy_name = self.select_strategy()
        recommender = self.strategies[strategy_name]

        # Get recommendations
        recommendations = recommender.recommend(user_id, n_recommendations)

        # Add strategy info
        for rec in recommendations:
            rec['strategy'] = strategy_name

        return recommendations

    def record_outcome(self, strategy_name, clicked, booked=False):
        """Record outcome and update bandit"""

        # Calculate reward
        reward = 0.1 if clicked else 0
        reward += 1.0 if booked else 0

        self.update(strategy_name, reward)
```

---

## Summary

Hybrid approaches for the travel agency platform:

- **Weighted**: Linear combination with fixed or dynamic weights
- **Switching**: Context-based or confidence-based selection
- **Ensemble**: Stacking with meta-learner, rank fusion
- **LightFM**: Hybrid collaborative + content model
- **Meta**: Strategy selection with bandits

**Key Hybrid Decisions:**
- Dynamic weighting based on user context
- Cold start switching to content-based
- RRF for combining rankings
- LightFM for unified hybrid model
- Bandit for online strategy optimization

---

**Next:** [Part 5: Real-Time Personalization](./RECOMMENDATIONS_ENGINE_05_REALTIME.md) — Dynamic recommendations and context awareness
