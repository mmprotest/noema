"""Memory subsystems for Noema."""

from __future__ import annotations

import math
import json
import random
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from .types import Coalition


@dataclass
class WorkingMemoryEntry:
    text: str
    added_at: float
    salience: float


class WorkingMemory:
    """Short-term memory with exponential decay."""

    def __init__(self, max_items: int, decay: float) -> None:
        self.max_items = max_items
        self.decay = max(decay, 0.01)
        self._items: List[WorkingMemoryEntry] = []

    def add(self, coalition: Coalition, now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        self._items.append(
            WorkingMemoryEntry(
                text=coalition.full_text,
                added_at=timestamp,
                salience=coalition.bounded_salience,
            )
        )
        self._items = self._items[-self.max_items :]

    def decay_factor(self, entry: WorkingMemoryEntry, now: float | None = None) -> float:
        now_ts = time.time() if now is None else now
        elapsed = max(0.0, now_ts - entry.added_at)
        return math.exp(-self.decay * elapsed)

    def weighted_salience(self, text: str, now: float | None = None) -> float:
        for entry in reversed(self._items):
            if entry.text == text:
                return entry.salience * self.decay_factor(entry, now=now)
        return 0.1

    def contents(self) -> List[WorkingMemoryEntry]:
        return list(self._items)


class EpisodicStore(ABC):
    """Interface for episodic memory backends."""

    @abstractmethod
    def add(self, coalition: Coalition) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        raise NotImplementedError


class InMemoryEpisodic(EpisodicStore):
    def __init__(self) -> None:
        self._items: List[Tuple[str, List[float]]] = []

    def add(self, coalition: Coalition) -> None:
        vector = _hash_embedding(coalition.full_text)
        self._items.append((coalition.full_text, vector))

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        if not self._items:
            return []
        query_vec = _hash_embedding(query)
        scores = [(_cosine(query_vec, vec), text) for text, vec in self._items]
        ranked = sorted(scores, key=lambda x: x[0], reverse=True)[:limit]
        return [(text, float(score)) for score, text in ranked]


class SqliteEpisodic(EpisodicStore):
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS episodes (text TEXT NOT NULL, embedding BLOB NOT NULL)"
        )
        self._conn.commit()

    def add(self, coalition: Coalition) -> None:
        emb = _hash_embedding(coalition.full_text)
        self._conn.execute(
            "INSERT INTO episodes(text, embedding) VALUES (?, ?)",
            (coalition.full_text, json.dumps(emb)),
        )
        self._conn.commit()

    def _all(self) -> Iterable[Tuple[str, np.ndarray]]:
        cur = self._conn.execute("SELECT text, embedding FROM episodes")
        for text, blob in cur.fetchall():
            yield text, json.loads(blob)

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        items = list(self._all())
        if not items:
            return []
        query_vec = _hash_embedding(query)
        scores = [(_cosine(query_vec, vec), text) for text, vec in items]
        ranked = sorted(scores, key=lambda x: x[0], reverse=True)[:limit]
        return [(text, float(score)) for score, text in ranked]


class DuckDBEpisodic(EpisodicStore):
    """Fallback DuckDB-like store implemented with SQLite for offline use."""

    def __init__(self, path: str | Path) -> None:
        self._sqlite = SqliteEpisodic(path)

    def add(self, coalition: Coalition) -> None:
        self._sqlite.add(coalition)

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        return self._sqlite.search(query, limit)


def _hash_embedding(text: str) -> List[float]:
    rng = _rng_for_text(text)
    return [rng.uniform(-1.0, 1.0) for _ in range(32)]


def _rng_for_text(text: str) -> random.Random:
    return random.Random(hash(text) & 0xFFFFFFFF)


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


__all__ = [
    "WorkingMemory",
    "WorkingMemoryEntry",
    "EpisodicStore",
    "InMemoryEpisodic",
    "SqliteEpisodic",
    "DuckDBEpisodic",
]
