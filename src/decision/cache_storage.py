"""
decision.cache_storage — Disk-backed JSON cache storage for decisions.

This module handles reading/writing cached decisions to disk.
Each decision type has its own JSON file for efficient lookups.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from .cache_schema import CachedDecision, CacheStats


class DecisionCacheStorage:
    """
    Thread-safe disk-backed cache storage for decisions.

    Each decision type gets its own JSON file:
    - data/decision_cache/elderly_mobility_risk.json
    - data/decision_cache/toddler_pacing_risk.json
    - data/decision_cache/budget_feasibility.json
    - etc.
    """

    def __init__(self, cache_dir: Optional[str | Path] = None):
        """
        Initialize cache storage.

        Args:
            cache_dir: Directory for cache files (default: data/decision_cache/)
        """
        if cache_dir is None:
            # Default to project root/data/decision_cache
            project_root = Path(__file__).resolve().parent.parent.parent
            cache_dir = project_root / "data" / "decision_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety for concurrent access
        self._locks: Dict[str, Lock] = {}
        self._global_lock = Lock()

        # Statistics
        self.stats = CacheStats()

    def _get_lock(self, decision_type: str) -> Lock:
        """Get or create a lock for the specific decision type."""
        with self._global_lock:
            if decision_type not in self._locks:
                self._locks[decision_type] = Lock()
            return self._locks[decision_type]

    def _get_cache_file_path(self, decision_type: str) -> Path:
        """Get the cache file path for a decision type."""
        # Sanitize decision_type for filename
        safe_name = decision_type.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_name}.json"

    def get(self, cache_key: str, decision_type: str) -> Optional[CachedDecision]:
        """
        Retrieve a cached decision.

        Args:
            cache_key: The cache key to look up
            decision_type: Type of decision (determines which file to read)

        Returns:
            CachedDecision if found and valid, None otherwise
        """
        self.stats.total_lookups += 1

        cache_file = self._get_cache_file_path(decision_type)

        if not cache_file.exists():
            self.stats.record_miss()
            return None

        lock = self._get_lock(decision_type)

        with lock:
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                # Find the specific cache key
                if cache_key in cache_data:
                    decision_data = cache_data[cache_key]
                    decision = CachedDecision.from_dict(decision_data)

                    # Check if still valid
                    if decision.is_valid():
                        decision.mark_used()
                        # Update the use count in the file
                        cache_data[cache_key] = decision.to_dict()
                        with open(cache_file, "w") as f:
                            json.dump(cache_data, f, indent=2)

                        self.stats.record_hit()
                        return decision
                    else:
                        # Invalid (too old or low success rate)
                        # Remove it
                        del cache_data[cache_key]
                        with open(cache_file, "w") as f:
                            json.dump(cache_data, f, indent=2)

            except (json.JSONDecodeError, IOError, KeyError) as e:
                # Corrupt cache file - treat as miss
                pass

        self.stats.record_miss()
        return None

    def set(
        self,
        cache_key: str,
        decision_type: str,
        decision: CachedDecision,
    ) -> None:
        """
        Store a cached decision.

        Args:
            cache_key: The cache key
            decision_type: Type of decision
            decision: The CachedDecision to store
        """
        cache_file = self._get_cache_file_path(decision_type)
        lock = self._get_lock(decision_type)

        with lock:
            # Load existing data
            cache_data = {}
            if cache_file.exists():
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    # Start fresh if file is corrupt
                    cache_data = {}

            # Add/update the entry
            cache_data[cache_key] = decision.to_dict()

            # Write back
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

    def delete(self, cache_key: str, decision_type: str) -> bool:
        """
        Delete a cached decision.

        Args:
            cache_key: The cache key to delete
            decision_type: Type of decision

        Returns:
            True if deleted, False if not found
        """
        cache_file = self._get_cache_file_path(decision_type)
        lock = self._get_lock(decision_type)

        with lock:
            if not cache_file.exists():
                return False

            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                if cache_key in cache_data:
                    del cache_data[cache_key]

                    with open(cache_file, "w") as f:
                        json.dump(cache_data, f, indent=2)

                    return True
            except (json.JSONDecodeError, IOError):
                pass

        return False

    def get_all_for_type(self, decision_type: str) -> Dict[str, CachedDecision]:
        """
        Get all cached decisions for a specific type.

        Args:
            decision_type: Type of decision

        Returns:
            Dictionary mapping cache_key to CachedDecision
        """
        cache_file = self._get_cache_file_path(decision_type)
        result = {}

        if not cache_file.exists():
            return result

        lock = self._get_lock(decision_type)

        with lock:
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                for key, data in cache_data.items():
                    decision = CachedDecision.from_dict(data)
                    if decision.is_valid():
                        result[key] = decision

            except (json.JSONDecodeError, IOError):
                pass

        return result

    def clear_type(self, decision_type: str) -> int:
        """
        Clear all cached decisions for a specific type.

        Args:
            decision_type: Type of decision to clear

        Returns:
            Number of entries deleted
        """
        cache_file = self._get_cache_file_path(decision_type)
        lock = self._get_lock(decision_type)

        with lock:
            if not cache_file.exists():
                return 0

            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                count = len(cache_data)

                # Delete the file
                cache_file.unlink()

                return count
            except (json.JSONDecodeError, IOError):
                return 0

    def clear_all(self) -> int:
        """
        Clear all cached decisions.

        Returns:
            Total number of entries deleted
        """
        total = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    total += len(cache_data)

                cache_file.unlink()
            except (json.JSONDecodeError, IOError):
                pass

        return total

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats

    def get_size_bytes(self) -> int:
        """Get total size of cache directory in bytes."""
        total = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                total += cache_file.stat().st_size
            except OSError:
                pass

        return total

    def get_entry_count(self) -> int:
        """Get total number of cached entries across all types."""
        total = 0

        for cache_file in self.cache_dir.glob("*.json"):
            lock = self._get_lock(cache_file.stem)

            with lock:
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                        total += len(cache_data)
                except (json.JSONDecodeError, IOError):
                    pass

        return total


# Singleton instance for convenient access
_default_storage: Optional[DecisionCacheStorage] = None


def get_default_storage() -> DecisionCacheStorage:
    """Get the default singleton cache storage instance."""
    global _default_storage
    if _default_storage is None:
        _default_storage = DecisionCacheStorage()
    return _default_storage
