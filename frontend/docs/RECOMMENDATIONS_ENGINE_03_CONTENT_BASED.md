# Recommendations Engine Part 3: Content-Based Filtering

> Similarity algorithms, feature extraction, and content analysis

**Series:** Recommendations Engine
**Previous:** [Part 2: Collaborative Filtering](./RECOMMENDATIONS_ENGINE_02_COLLABORATIVE.md)
**Next:** [Part 4: Hybrid Approaches](./RECOMMENDATIONS_ENGINE_04_HYBRID.md)

---

## Table of Contents

1. [Content Similarity](#content-similarity)
2. [Text Analysis](#text-analysis)
3. [Image Similarity](#image-similarity)
4. [Travel Profile Building](#travel-profile-building)
5. [Destination Embeddings](#destination-embeddings)

---

## Content Similarity

### Jaccard Similarity

```python
# Jaccard similarity for categorical features

from sklearn.metrics import jaccard_score
import numpy as np

class JaccardSimilarity:
    """Jaccard similarity for sets/tags"""

    @staticmethod
    def similarity(set1, set2):
        """Compute Jaccard similarity between two sets"""
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0

    def find_similar_items(self, item_id, item_tags, k=10):
        """Find items with similar tags"""

        similarities = []
        target_tags = set(item_tags[item_id])

        for other_id, other_tags in item_tags.items():
            if other_id == item_id:
                continue

            similarity = self.similarity(
                target_tags,
                set(other_tags)
            )

            similarities.append({
                'item_id': other_id,
                'similarity': similarity
            })

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return similarities[:k]

# Usage
destination_tags = {
    'paris': ['city', 'culture', 'romance', 'food', 'museums'],
    'rome': ['city', 'culture', 'history', 'food', 'ancient'],
    'barcelona': ['city', 'culture', 'beach', 'food', 'architecture'],
    'amsterdam': ['city', 'culture', 'romance', 'canals', 'museums'],
}

jaccard = JaccardSimilarity()
similar_to_paris = jaccard.find_similar_items('paris', destination_tags)
# Returns: rome (0.6), amsterdam (0.6), barcelona (0.5)
```

### Cosine Similarity

```python
# Cosine similarity for numerical features

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CosineSimilarityRecommender:
    """Content-based recommendations using cosine similarity"""

    def __init__(self):
        self.feature_matrix = None
        self.item_ids = None

    def fit(self, items_features):
        """
        items_features: dict of {item_id: feature_vector}
        feature_vector: dict of numerical features
        """
        self.item_ids = list(items_features.keys())

        # Build feature matrix
        self.feature_matrix = np.array([
            list(items_features[item_id].values())
            for item_id in self.item_ids
        ])

        # Normalize features
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        self.feature_matrix = self.scaler.fit_transform(self.feature_matrix)

    def recommend(self, item_id, k=10):
        """Find similar items"""

        item_idx = self.item_ids.index(item_id)
        item_vector = self.feature_matrix[item_idx].reshape(1, -1)

        # Compute cosine similarity
        similarities = cosine_similarity(
            item_vector,
            self.feature_matrix
        )[0]

        # Get top k (excluding self)
        similarities[item_idx] = -1
        top_indices = np.argsort(-similarities)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]
```

### Combined Similarity

```python
# Combine multiple similarity measures

class HybridContentSimilarity:
    """Combine different similarity types"""

    def __init__(self, weights={
        'tags': 0.4,
        'category': 0.3,
        'attributes': 0.3
    }):
        self.weights = weights

    def combined_similarity(self, item1, item2):
        """Compute weighted similarity score"""

        scores = {}

        # Tag similarity (Jaccard)
        if 'tags' in self.weights:
            scores['tags'] = self._tag_similarity(item1, item2)

        # Category similarity (exact match)
        if 'category' in self.weights:
            scores['category'] = 1.0 if item1['category'] == item2['category'] else 0.0

        # Attribute similarity (cosine)
        if 'attributes' in self.weights:
            scores['attributes'] = self._attribute_similarity(item1, item2)

        # Weighted sum
        combined_score = sum(
            self.weights.get(key, 0) * score
            for key, score in scores.items()
        )

        return {
            'combined_score': combined_score,
            'component_scores': scores
        }

    def _tag_similarity(self, item1, item2):
        """Jaccard similarity for tags"""
        tags1 = set(item1.get('tags', []))
        tags2 = set(item2.get('tags', []))
        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)
        return intersection / union if union > 0 else 0

    def _attribute_similarity(self, item1, item2):
        """Cosine similarity for numerical attributes"""
        attrs = ['rating', 'price', 'popularity']

        vec1 = [item1.get(attr, 0) for attr in attrs]
        vec2 = [item2.get(attr, 0) for attr in attrs]

        # Normalize
        max_vals = [max(item1.get(attr, 1), item2.get(attr, 1)) for attr in attrs]
        vec1 = [v / (m or 1) for v, m in zip(vec1, max_vals)]
        vec2 = [v / (m or 1) for v, m in zip(vec2, max_vals)]

        # Cosine similarity
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a ** 2 for a in vec1) ** 0.5
        norm2 = sum(b ** 2 for b in vec2) ** 0.5

        return dot / (norm1 * norm2) if norm1 and norm2 else 0
```

---

## Text Analysis

### TF-IDF Similarity

```python
# Text similarity using TF-IDF

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TextSimilarityRecommender:
    """Content-based recommendations using text descriptions"""

    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.item_ids = None

    def fit(self, items_descriptions):
        """
        items_descriptions: dict of {item_id: description_text}
        """
        self.item_ids = list(items_descriptions.keys())
        descriptions = list(items_descriptions.values())

        # Create TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=2
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(descriptions)

    def recommend(self, query_text, k=10):
        """Find items similar to query text"""

        # Vectorize query
        query_vector = self.vectorizer.transform([query_text])

        # Compute similarities
        similarities = cosine_similarity(
            query_vector,
            self.tfidf_matrix
        )[0]

        # Get top k
        top_indices = np.argsort(-similarities)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx]),
                'matched_terms': self._get_matched_terms(
                    query_text,
                    self.item_ids[idx]
                )
            }
            for idx in top_indices
        ]

    def _get_matched_terms(self, query, item_id):
        """Extract terms that matched"""
        query_terms = set(query.lower().split())
        item_idx = self.item_ids.index(item_id)
        feature_names = self.vectorizer.get_feature_names_out()

        # Get non-zero features for item
        item_vector = self.tfidf_matrix[item_idx].toarray()[0]
        item_terms = set(feature_names[item_vector > 0])

        matched = query_terms & item_terms
        return list(matched)
```

### Sentence Embeddings

```python
# Modern embeddings with transformers

from sentence_transformers import SentenceTransformer
import torch

class EmbeddingSimilarity:
    """Semantic similarity using sentence embeddings"""

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.item_ids = None

    def fit(self, items_texts):
        """
        items_texts: dict of {item_id: text_content}
        text_content can be description, or combined fields
        """
        self.item_ids = list(items_texts.keys())
        texts = list(items_texts.values())

        # Generate embeddings
        self.embeddings = self.model.encode(
            texts,
            convert_to_tensor=True,
            show_progress_bar=True
        )

    def recommend(self, query_text, k=10):
        """Find semantically similar items"""

        # Encode query
        query_embedding = self.model.encode(
            query_text,
            convert_to_tensor=True
        )

        # Compute cosine similarity
        similarities = torch.nn.functional.cosine_similarity(
            query_embedding.unsqueeze(0),
            self.embeddings
        )

        # Get top k
        top_indices = torch.argsort(similarities, descending=True)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]

    def batch_recommend(self, item_id, k=10):
        """Find items similar to a given item"""

        item_idx = self.item_ids.index(item_id)
        item_embedding = self.embeddings[item_idx]

        # Compute similarities
        similarities = torch.nn.functional.cosine_similarity(
            item_embedding.unsqueeze(0),
            self.embeddings
        )

        # Exclude self and get top k
        similarities[item_idx] = -1
        top_indices = torch.argsort(similarities, descending=True)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]
```

---

## Image Similarity

### Visual Feature Extraction

```python
# Image similarity using pre-trained models

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

class ImageSimilarityRecommender:
    """Visual similarity using deep learning features"""

    def __init__(self):
        # Load pre-trained ResNet (remove classification head)
        resnet = models.resnet50(pretrained=True)
        self.model = nn.Sequential(*list(resnet.children())[:-1])
        self.model.eval()

        # Image preprocessing
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        self.embeddings = None
        self.item_ids = None

    def extract_features(self, image_path):
        """Extract features from an image"""

        image = Image.open(image_path).convert('RGB')
        input_tensor = self.preprocess(image)
        input_batch = input_tensor.unsqueeze(0)

        with torch.no_grad():
            features = self.model(input_batch)

        return features.flatten().numpy()

    def fit(self, items_images):
        """
        items_images: dict of {item_id: image_path}
        """
        self.item_ids = list(items_images.keys())

        # Extract features for all images
        embeddings = []
        for item_id in self.item_ids:
            features = self.extract_features(items_images[item_id])
            embeddings.append(features)

        self.embeddings = np.array(embeddings)

    def recommend(self, image_path, k=10):
        """Find visually similar items"""

        # Extract query features
        query_features = self.extract_features(image_path)

        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            query_features.reshape(1, -1),
            self.embeddings
        )[0]

        # Get top k
        top_indices = np.argsort(-similarities)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]
```

### CLIP Multi-Modal

```python
# CLIP for text-image similarity

import clip
import torch
from PIL import Image

class CLIPRecommender:
    """Multi-modal recommendations using CLIP"""

    def __init__(self, model_name='ViT-B/32'):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(model_name, device=device)
        self.device = device

        self.image_embeddings = None
        self.text_embeddings = None
        self.item_ids = None

    def fit(self, items_data):
        """
        items_data: dict of {item_id: {'image': path, 'text': description}}
        """
        self.item_ids = list(items_data.keys())

        image_embeddings = []
        text_embeddings = []

        for item_id in self.item_ids:
            item = items_data[item_id]

            # Process image
            image = Image.open(item['image'])
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)

            # Process text
            text_input = clip.tokenize([item['text']]).to(self.device)

            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_input)

            image_embeddings.append(image_features.cpu().numpy())
            text_embeddings.append(text_features.cpu().numpy())

        self.image_embeddings = np.vstack(image_embeddings)
        self.text_embeddings = np.vstack(text_embeddings)

    def recommend_by_text(self, query_text, k=10, use_images=True):
        """Find items matching text query"""

        # Encode query
        text_input = clip.tokenize([query_text]).to(self.device)
        with torch.no_grad():
            query_embedding = self.model.encode_text(text_input).cpu().numpy()

        # Compute similarities
        if use_images:
            embeddings = self.image_embeddings
        else:
            embeddings = self.text_embeddings

        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, embeddings)[0]

        # Get top k
        top_indices = np.argsort(-similarities)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]

    def recommend_by_image(self, image_path, k=10):
        """Find items similar to query image"""

        # Process query image
        image = Image.open(image_path)
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            query_embedding = self.model.encode_image(image_input).cpu().numpy()

        # Compute similarities with item images
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, self.image_embeddings)[0]

        # Get top k
        top_indices = np.argsort(-similarities)[:k]

        return [
            {
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]
```

---

## Travel Profile Building

### User Preference Extraction

```python
# Build travel preferences from behavior

class TravelProfileBuilder:
    """Extract and update user travel preferences"""

    def __init__(self, item_features):
        self.item_features = item_features

    def build_profile(self, user_interactions):
        """
        user_interactions: list of {'item_id', 'interaction_type', 'timestamp'}
        """
        profile = {
            'destinations': {},
            'preferences': {
                'travel_styles': {},
                'interests': {},
                'budget_range': [],
                'accommodation_types': {},
                'seasons': {}
            }
        }

        # Aggregate by interaction type
        weights = {
            'booking': 5.0,
            'wishlist': 3.0,
            'click': 1.0,
            'view': 0.5
        }

        for interaction in user_interactions:
            item_id = interaction['item_id']
            weight = weights.get(interaction['interaction_type'], 0.5)

            # Get item features
            if item_id not in self.item_features:
                continue

            features = self.item_features[item_id]

            # Accumulate destination preferences
            if 'destination' in features:
                dest = features['destination']
                profile['destinations'][dest] = \
                    profile['destinations'].get(dest, 0) + weight

            # Accumulate travel styles
            for style in features.get('travel_styles', []):
                profile['preferences']['travel_styles'][style] = \
                    profile['preferences']['travel_styles'].get(style, 0) + weight

            # Accumulate interests
            for interest in features.get('interests', []):
                profile['preferences']['interests'][interest] = \
                    profile['preferences']['interests'].get(interest, 0) + weight

            # Accumulate accommodation types
            acc_type = features.get('accommodation_type')
            if acc_type:
                profile['preferences']['accommodation_types'][acc_type] = \
                    profile['preferences']['accommodation_types'].get(acc_type, 0) + weight

            # Track budget
            if 'price' in features:
                profile['preferences']['budget_range'].append(features['price'])

        # Normalize and summarize
        return self._normalize_profile(profile)

    def _normalize_profile(self, profile):
        """Normalize scores and extract top preferences"""

        # Normalize travel styles
        total_style_weight = sum(profile['preferences']['travel_styles'].values())
        if total_style_weight > 0:
            profile['preferences']['travel_styles'] = {
                k: v / total_style_weight
                for k, v in profile['preferences']['travel_styles'].items()
            }

        # Get top interests
        sorted_interests = sorted(
            profile['preferences']['interests'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        profile['preferences']['top_interests'] = [
            k for k, v in sorted_interests[:10]
        ]

        # Compute budget range
        if profile['preferences']['budget_range']:
            budget_values = profile['preferences']['budget_range']
            profile['preferences']['budget'] = {
                'min': min(budget_values),
                'max': max(budget_values),
                'avg': sum(budget_values) / len(budget_values)
            }

        return profile
```

### Dynamic Profile Updates

```python
# Real-time profile updates

from collections import defaultdict
import numpy as np

class DynamicTravelProfile:
    """Maintain and update user travel profile in real-time"""

    def __init__(self, decay_factor=0.95):
        """
        decay_factor: Weight for old preferences (0-1)
        Lower values = faster adaptation to new behavior
        """
        self.decay_factor = decay_factor
        self.profiles = {}

    def update_profile(self, user_id, interaction, item_features):
        """Update user profile with new interaction"""

        if user_id not in self.profiles:
            self.profiles[user_id] = self._init_profile()

        profile = self.profiles[user_id]
        weight = self._interaction_weight(interaction['type'])

        # Update with exponential moving average
        for feature, value in self._extract_features(item_features).items():
            old_value = profile['features'].get(feature, 0)
            profile['features'][feature] = \
                self.decay_factor * old_value + (1 - self.decay_factor) * value * weight

        # Update timestamp
        profile['last_updated'] = interaction['timestamp']

        return profile

    def _init_profile(self):
        """Initialize new user profile"""
        return {
            'features': defaultdict(float),
            'created_at': None,
            'last_updated': None
        }

    def _interaction_weight(self, interaction_type):
        """Weight for different interaction types"""
        weights = {
            'booking': 1.0,
            'wishlist_add': 0.7,
            'click': 0.3,
            'view': 0.1,
            'dismiss': -0.2
        }
        return weights.get(interaction_type, 0.1)

    def _extract_features(self, item_features):
        """Extract feature vector from item"""
        features = {}

        # One-hot encode categorical features
        for category in ['travel_style', 'region', 'accommodation_type']:
            value = item_features.get(category)
            if value:
                features[f'{category}:{value}'] = 1.0

        # Binary features
        for tag in item_features.get('tags', []):
            features[f'tag:{tag}'] = 1.0

        # Normalize numerical features
        if 'rating' in item_features:
            features['rating'] = item_features['rating'] / 5.0

        if 'price' in item_features:
            features['price'] = np.log1p(item_features['price']) / 10  # Log-scale and normalize

        return features

    def get_profile(self, user_id):
        """Get user's current profile"""
        return self.profiles.get(user_id, self._init_profile())
```

---

## Destination Embeddings

### Graph-Based Embeddings

```python
# Node2Vec for destination relationships

import networkx as nx
from node2vec import Node2Vec
from gensim.models import Word2Vec

class DestinationGraphEmbeddings:
    """Learn destination embeddings from relationship graph"""

    def __init__(self, dimensions=64, walk_length=30, num_walks=200):
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.embeddings = None

    def build_graph(self, destinations, interactions):
        """Build destination co-occurrence graph"""

        G = nx.Graph()

        # Add nodes
        for dest_id in destinations:
            G.add_node(dest_id)

        # Add edges based on co-occurrence in trips
        for user_trip in interactions:
            dests_in_trip = user_trip['destinations']
            for i, dest1 in enumerate(dests_in_trip):
                for dest2 in dests_in_trip[i+1:]:
                    if G.has_edge(dest1, dest2):
                        G[dest1][dest2]['weight'] += 1
                    else:
                        G.add_edge(dest1, dest2, weight=1)

        return G

    def train(self, graph):
        """Train Node2Vec embeddings"""

        # Node2Vec
        node2vec = Node2Vec(
            graph,
            dimensions=self.dimensions,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            workers=4,
            p=1,  # Return parameter
            q=0.5,  # In-out parameter (bias towards homophily)
        )

        # Fit model
        model = node2vec.fit(window=10, min_count=1, batch_words=4)

        # Store embeddings
        self.embeddings = {
            node: model.wv[node]
            for node in graph.nodes()
        }

        return self.embeddings

    def find_similar(self, destination_id, k=10):
        """Find destinations with similar embeddings"""

        if destination_id not in self.embeddings:
            return []

        target_emb = self.embeddings[destination_id]

        # Compute cosine similarity
        similarities = {}
        for dest_id, emb in self.embeddings.items():
            if dest_id == destination_id:
                continue

            # Cosine similarity
            dot = np.dot(target_emb, emb)
            norm = np.linalg.norm(target_emb) * np.linalg.norm(emb)
            similarity = dot / norm if norm > 0 else 0

            similarities[dest_id] = similarity

        # Get top k
        sorted_similar = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]

        return [
            {'destination_id': dest_id, 'similarity': float(sim)}
            for dest_id, sim in sorted_similar
        ]
```

---

## Summary

Content-based filtering for the travel agency platform:

- **Similarity**: Jaccard for tags, cosine for features
- **Text**: TF-IDF and sentence embeddings
- **Images**: ResNet features, CLIP multi-modal
- **Profiles**: Dynamic preference extraction
- **Embeddings**: Graph-based destination relationships

**Key Implementation Decisions:**
- Combine multiple similarity measures
- Sentence transformers for semantic text search
- CLIP for text-image matching
- Exponential decay for dynamic profiles
- Node2Vec for destination relationships

---

**Next:** [Part 4: Hybrid Approaches](./RECOMMENDATIONS_ENGINE_04_HYBRID.md) — Combining algorithms and ensemble methods
