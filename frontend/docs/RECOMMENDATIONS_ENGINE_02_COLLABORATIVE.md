# Recommendations Engine Part 2: Collaborative Filtering

> User-based, item-based, and matrix factorization algorithms

**Series:** Recommendations Engine
**Previous:** [Part 1: Architecture](./RECOMMENDATIONS_ENGINE_01_ARCHITECTURE.md)
**Next:** [Part 3: Content-Based Filtering](./RECOMMENDATIONS_ENGINE_03_CONTENT_BASED.md)

---

## Table of Contents

1. [User-Based Collaborative Filtering](#user-based-collaborative-filtering)
2. [Item-Based Collaborative Filtering](#item-based-collaborative-filtering)
3. [Matrix Factorization](#matrix-factorization)
4. [Implicit Feedback](#implicit-feedback)
5. [Cold Start Solutions](#cold-start-solutions)

---

## User-Based Collaborative Filtering

### Algorithm Overview

```python
# User-based collaborative filtering

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class UserBasedCF:
    """Find similar users, recommend their liked items"""

    def __init__(self, k_neighbors=20):
        self.k = k_neighbors
        self.user_item_matrix = None
        self.similarity_matrix = None

    def fit(self, interactions):
        """
        interactions: sparse matrix of shape (n_users, n_items)
        """
        self.user_item_matrix = interactions

        # Compute user-user similarity
        self.similarity_matrix = cosine_similarity(interactions)

        # Set diagonal to 0 (users aren't similar to themselves)
        np.fill_diagonal(self.similarity_matrix, 0)

    def recommend(self, user_id, n_recommendations=10):
        """Get recommendations for a user"""

        # Get user index
        user_idx = self.user_map[user_id]

        # Find k similar users
        similar_users = np.argsort(
            -self.similarity_matrix[user_idx]
        )[:self.k]

        # Get their similarity scores
        similarities = self.similarity_matrix[user_idx][similar_users]

        # Get items liked by similar users
        similar_users_items = self.user_item_matrix[similar_users]

        # Score items by weighted sum of similarities
        scores = similar_users_items.T @ similarities

        # Remove items already interacted with
        user_items = self.user_item_matrix[user_idx]
        scores[user_items > 0] = -np.inf

        # Get top recommendations
        top_items = np.argsort(-scores)[:n_recommendations]

        return [
            {
                'item_id': self.reverse_item_map[idx],
                'score': float(scores[idx]),
                'reason': f'Users like you also liked this'
            }
            for idx in top_items
        ]
```

### Implementation with LightFM

```python
# LightFM user-based implementation

from lightfm import LightFM
from lightfm.data import Dataset

# Create dataset
dataset = Dataset()
dataset.fit(
    users=user_ids,
    items=item_ids,
    user_features=user_feature_names,
    item_features=item_feature_names
)

# Build interactions
(interactions, weights) = dataset.build_interactions(
    [(user_id, item_id) for user_id, item_id in interaction_data]
)

# Train user-based model
model = LightFM(
    loss='warp',  # Weighted Approximate-Rank Pairwise
    user_alpha=0.01,
    item_alpha=0.01,
    no_components=30
)

model.fit(
    interactions,
    user_features=user_features,
    item_features=item_features,
    epochs=20,
    num_threads=4
)

# Get recommendations
def get_user_based_recommendations(user_id, k=10):
    user_idx = dataset.mapping()[0][user_id]

    # Score all items
    scores = model.predict(
        user_idx,
        np.arange(dataset.item_count()),
        user_features=user_features,
        item_features=item_features
    )

    # Get top items
    top_indices = np.argsort(-scores)[:k]

    return [
        {
            'item_id': dataset.mapping()[2][idx],
            'score': float(scores[idx])
        }
        for idx in top_indices
    ]
```

---

## Item-Based Collaborative Filtering

### Algorithm Overview

```python
# Item-based collaborative filtering

class ItemBasedCF:
    """Find similar items to user's liked items"""

    def __init__(self, k_neighbors=20):
        self.k = k_neighbors
        self.item_similarity_matrix = None

    def fit(self, interactions):
        """
        interactions: sparse matrix of shape (n_users, n_items)
        """
        # Compute item-item similarity (transpose for item-item)
        self.item_similarity_matrix = cosine_similarity(interactions.T)

    def recommend(self, user_id, n_recommendations=10):
        """Get recommendations based on user's liked items"""

        user_idx = self.user_map[user_id]
        user_items = self.user_item_matrix[user_idx]

        # Find items user has interacted with
        liked_items = np.where(user_items > 0)[0]

        # For each liked item, find similar items
        recommendations = {}
        for item_idx in liked_items:
            # Get similar items
            similarities = self.item_similarity_matrix[item_idx]

            # Score by similarity × user's rating
            for similar_item, similarity in enumerate(similarities):
                if similar_item == item_idx:
                    continue

                score = similarity * user_items[item_idx]
                if similar_item not in recommendations:
                    recommendations[similar_item] = 0
                recommendations[similar_item] += score

        # Remove already interacted items
        for item_idx in liked_items:
            recommendations.pop(item_idx, None)

        # Get top items
        sorted_recs = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n_recommendations]

        return [
            {
                'item_id': self.reverse_item_map[idx],
                'score': float(score),
                'reason': f'Similar to your liked items'
            }
            for idx, score in sorted_recs
        ]
```

### Precomputed Similarity

```python
# Precompute item similarities for fast serving

import pickle
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

def precompute_item_similarities(interactions, output_path):
    """Precompute and save item-item similarity matrix"""

    # Compute similarity matrix
    item_similarities = cosine_similarity(interactions.T)

    # For each item, store top-k similar items
    k = 100
    top_similar_items = {}
    n_items = interactions.shape[1]

    for item_idx in range(n_items):
        # Get top-k similar items
        similar_indices = np.argsort(-item_similarities[item_idx])[:k+1]
        similar_indices = similar_indices[similar_indices != item_idx][:k]

        similar_scores = item_similarities[item_idx][similar_indices]

        top_similar_items[item_idx] = {
            'indices': similar_indices.tolist(),
            'scores': similar_scores.tolist()
        }

    # Save to file
    with open(output_path, 'wb') as f:
        pickle.dump(top_similar_items, f)

    return top_similar_items

# Fast serving with precomputed similarities
def get_similar_items(item_id, k=10):
    """Get similar items from precomputed matrix"""

    with open('item_similarities.pkl', 'rb') as f:
        similarities = pickle.load(f)

    item_idx = item_map[item_id]
    similar_items = similarities[item_idx]

    # Return top-k
    top_indices = similar_items['indices'][:k]
    top_scores = similar_items['scores'][:k]

    return [
        {
            'item_id': reverse_item_map[idx],
            'score': float(score)
        }
        for idx, score in zip(top_indices, top_scores)
    ]
```

---

## Matrix Factorization

### SVD Implementation

```python
# Matrix factorization with SVD

from scipy.sparse.linalg import svds

class SVDRecommender:
    """Singular Value Decomposition for recommendations"""

    def __init__(self, n_factors=50):
        self.n_factors = n_factors
        self.user_factors = None
        self.item_factors = None

    def fit(self, interactions):
        """
        Factorize user-item matrix into user and item factors
        """
        # Convert to sparse matrix if needed
        sparse_matrix = csr_matrix(interactions)

        # Perform SVD
        U, sigma, Vt = svds(
            sparse_matrix,
            k=self.n_factors
        )

        # Store factors
        self.user_factors = U
        self.item_factors = Vt.T

        # Scale by singular values
        self.sigma = sigma

    def predict(self, user_id, item_id):
        """Predict user's rating for item"""

        user_idx = self.user_map[user_id]
        item_idx = self.item_map[item_id]

        # Dot product of user and item factors
        prediction = np.dot(
            self.user_factors[user_idx] * self.sigma,
            self.item_factors[item_idx]
        )

        return float(prediction)

    def recommend(self, user_id, n_recommendations=10):
        """Get top recommendations for user"""

        user_idx = self.user_map[user_id]
        user_factor = self.user_factors[user_idx] * self.sigma

        # Score all items
        scores = self.item_factors @ user_factor

        # Get user's interacted items
        user_items = self.user_item_matrix[user_idx]
        scores[user_items > 0] = -np.inf

        # Return top items
        top_indices = np.argsort(-scores)[:n_recommendations]

        return [
            {
                'item_id': self.reverse_item_map[idx],
                'score': float(scores[idx])
            }
            for idx in top_indices
        ]
```

### Alternating Least Squares (ALS)

```python
# ALS for implicit feedback

from implicit.als import AlternatingLeastSquares
import implicit

class ALSRecommender:
    """ALS for implicit feedback data"""

    def __init__(self, factors=64, iterations=15):
        self.model = AlternatingLeastSquares(
            factors=factors,
            iterations=iterations,
            calculate_training_loss=True,
            random_state=42
        )

    def fit(self, interactions):
        """
        interactions: CSR matrix of user-item interactions
        """
        # Train model
        self.model.fit(interactions)

        # Store user and item factors
        self.user_factors = self.model.user_factors
        self.item_factors = self.model.item_factors

    def recommend(self, user_id, n_recommendations=10, filter_already_liked=True):
        """Get recommendations for user"""

        user_idx = self.user_map[user_id]

        # Get recommendations
        recommendations = self.model.recommend(
            user_idx,
            self.user_item_matrix,
            N=n_recommendations,
            filter_already_liked_items=filter_already_liked
        )

        return [
            {
                'item_id': self.reverse_item_map[idx],
                'score': float(score)
            }
            for idx, score in recommendations
        ]

    def similar_items(self, item_id, n=10):
        """Find similar items"""

        item_idx = self.item_map[item_id]

        # Get similar items
        similar_items, scores = self.model.similar_items(
            item_idx,
            N=n+1  # +1 because item itself is included
        )

        # Remove the item itself
        similar_items = similar_items[1:]
        scores = scores[1:]

        return [
            {
                'item_id': self.reverse_item_map[idx],
                'score': float(score)
            }
            for idx, score in zip(similar_items, scores)
        ]
```

---

## Implicit Feedback

### Handling Implicit Signals

```python
# Implicit feedback with weighted interactions

import numpy as np

class ImplicitFeedbackRecommender:
    """Handle implicit feedback (views, clicks, etc.)"""

    def __init__(self, alpha=40, epsilon=1e-6):
        """
        alpha: Confidence scaling factor
        Higher alpha = more confidence in observed interactions
        """
        self.alpha = alpha
        self.epsilon = epsilon

    def build_confidence_matrix(self, interactions):
        """
        Convert binary interactions to confidence weights

        c_ui = 1 + alpha * r_ui
        where r_ui is the interaction count
        """
        # Count interactions per user-item pair
        interaction_counts = interactions

        # Apply confidence weighting
        confidence = 1 + self.alpha * interaction_counts

        # Clip values
        confidence = np.clip(confidence, 0, 1 + self.alpha * 100)

        return confidence

    def fit(self, interactions):
        """Train on implicit feedback"""

        # Build confidence matrix
        confidence = self.build_confidence_matrix(interactions)

        # Train ALS with confidence weights
        self.model = AlternatingLeastSquares(
            factors=64,
            iterations=20,
            confidence=self.alpha
        )

        # Fit with confidence
        self.model.fit(confidence, show_progress=False)

    def recommend(self, user_id, n_recommendations=10):
        """Get recommendations with implicit feedback"""

        user_idx = self.user_map[user_id]

        # Get user's interaction history
        user_history = self.user_item_matrix[user_idx]

        # Get recommendations
        recs = self.model.recommend(
            user_idx,
            user_history,
            N=n_recommendations,
            filter_already_liked_items=True
        )

        return [
            {
                'item_id': self.reverse_item_map[idx],
                'score': float(score),
                'confidence': float(score / self.alpha)
            }
            for idx, score in recs
        ]
```

### BPR (Bayesian Personalized Ranking)

```python
# BPR optimization for implicit feedback

import torch
import torch.nn as nn

class BPRRecommender(nn.Module):
    """Bayesian Personalized Ranking for implicit feedback"""

    def __init__(self, n_users, n_items, n_factors=64):
        super().__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.n_factors = n_factors

        # User and item embeddings
        self.user_embeddings = nn.Embedding(n_users, n_factors)
        self.item_embeddings = nn.Embedding(n_items, n_factors)

        # Initialize with small values
        nn.init.normal_(self.user_embeddings.weight, std=0.01)
        nn.init.normal_(self.item_embeddings.weight, std=0.01)

    def forward(self, user, item_i, item_j):
        """
        user: User index
        item_i: Positive item index
        item_j: Negative item index
        """
        # Get embeddings
        u = self.user_embeddings(user)
        i = self.item_embeddings(item_i)
        j = self.item_embeddings(item_j)

        # Compute scores
        x_ui = (u * i).sum(dim=1)
        x_uj = (u * j).sum(dim=1)

        # BPR objective: maximize difference
        return x_ui - x_uj

    def recommend(self, user_idx, k=10):
        """Get recommendations for user"""

        user = self.user_embeddings.weight[user_idx]
        items = self.item_embeddings.weight

        # Compute scores for all items
        scores = items @ user

        # Get top items
        top_items = torch.topk(scores, k).indices

        return [
            {
                'item_id': self.reverse_item_map[idx.item()],
                'score': float(scores[idx])
            }
            for idx in top_items
        ]

# Training loop
def train_bpr(model, train_data, epochs=20, lr=0.01):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.Sigmoid()  # BPR uses sigmoid on score difference

    for epoch in range(epochs):
        total_loss = 0

        for user, positive, negative in train_data:
            # Forward pass
            score_diff = model(user, positive, negative)
            loss = -torch.log(criterion(score_diff)).mean()

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1}, Loss: {total_loss/len(train_data):.4f}")
```

---

## Cold Start Solutions

### New User Recommendations

```python
# Cold start strategies for new users

class ColdStartRecommender:
    """Handle new users with minimal interaction history"""

    def __init__(self, item_features, popular_items):
        self.item_features = item_features
        self.popular_items = popular_items

    def recommend_for_new_user(
        self,
        user_profile: dict,
        n_recommendations=10
    ):
        """
        user_profile: {
            'origin_country': 'US',
            'interests': ['beach', 'adventure'],
            'budget_range': [500, 2000],
            'travel_styles': ['luxury']
        }
        """

        # Strategy 1: Popular items (fallback)
        if not user_profile:
            return [
                {
                    'item_id': item['id'],
                    'score': item['popularity_score'],
                    'reason': 'Popular with all travelers'
                }
                for item in self.popular_items[:n_recommendations]
            ]

        # Strategy 2: Content-based matching
        if user_profile.get('interests'):
            recs = self._content_based_recommendations(
                user_profile['interests'],
                n_recommendations
            )
            if recs:
                return recs

        # Strategy 3: Demographic-based
        if user_profile.get('origin_country'):
            recs = self._demographic_recommendations(
                user_profile['origin_country'],
                n_recommendations
            )
            if recs:
                return recs

        # Fallback to popular
        return self.recommend_for_new_user({}, n_recommendations)

    def _content_based_recommendations(self, interests, k):
        """Find items matching user interests"""

        # Score items by interest overlap
        item_scores = {}
        for item_id, features in self.item_features.items():
            item_tags = set(features.get('tags', []))
            interest_tags = set(interests)

            # Jaccard similarity
            overlap = len(item_tags & interest_tags)
            union = len(item_tags | interest_tags)
            score = overlap / union if union > 0 else 0

            if score > 0:
                item_scores[item_id] = score

        # Get top items
        sorted_items = sorted(
            item_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]

        return [
            {
                'item_id': item_id,
                'score': float(score),
                'reason': f'Matches your interests: {", ".join(interests)}'
            }
            for item_id, score in sorted_items
        ]

    def _demographic_recommendations(self, country, k):
        """Recommend items popular in user's country"""

        # Get items popular in user's country
        country_popular = [
            item for item in self.popular_items
            if item.get('top_country') == country
        ]

        if not country_popular:
            return None

        return [
            {
                'item_id': item['id'],
                'score': item['popularity_score'],
                'reason': f'Popular with travelers from {country}'
            }
            for item in country_popular[:k]
        ]
```

### New Item Recommendations

```python
# Cold start for new items (content-based boosting)

class NewItemBooster:
    """Boost new items to get initial interactions"""

    def __init__(self, similarity_model):
        self.similarity_model = similarity_model
        self.new_item_threshold = 10  # Interactions before not "new"

    def score_with_new_item_boost(
        self,
        item_id,
        base_score,
        item_interactions
    ):
        """Boost score for new items"""

        n_interactions = item_interactions.get(item_id, 0)

        if n_interactions < self.new_item_threshold:
            # Apply boost: more boost for fewer interactions
            boost_factor = 1 + (self.new_item_threshold - n_interactions) / 10

            return {
                'item_id': item_id,
                'base_score': base_score,
                'boosted_score': base_score * boost_factor,
                'boost_applied': True,
                'reason': 'New destination - help us discover it!'
            }

        return {
            'item_id': item_id,
            'base_score': base_score,
            'boosted_score': base_score,
            'boost_applied': False
        }

    def get_similar_item_boost(self, new_item_id):
        """Score new item by similarity to established items"""

        # Find similar established items
        similar_items = self.similarity_model.get_similar_items(
            new_item_id,
            k=5
        )

        # Average score of similar items
        avg_score = sum(item['score'] for item in similar_items) / len(similar_items)

        # Boost based on similarity
        boost = 1 + avg_score * 0.5

        return {
            'item_id': new_item_id,
            'score': avg_score * boost,
            'reason': f'Similar to popular destinations you might like'
        }
```

---

## Summary

Collaborative filtering approaches for the travel agency platform:

- **User-Based**: Find similar users, recommend their preferences
- **Item-Based**: Find items similar to user's history
- **Matrix Factorization**: SVD and ALS for latent factors
- **Implicit Feedback**: Weight interactions by confidence
- **Cold Start**: Content-based + popularity fallbacks

**Key Implementation Decisions:**
- LightFM for hybrid collaborative filtering
- Precompute item similarities for fast serving
- ALS for implicit feedback (views, clicks)
- BPR for ranking optimization
- Multi-strategy cold start handling

---

**Next:** [Part 3: Content-Based Filtering](./RECOMMENDATIONS_ENGINE_03_CONTENT_BASED.md) — Similarity matching and content analysis
