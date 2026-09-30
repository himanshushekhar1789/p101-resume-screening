"""Embedding service abstraction using SentenceTransformers for Phase 7 semantic matching.

Provides:
- CPU-first local model loading and inference
- Lazy singleton model initialization
- Text representation embedding generation
- Exact cosine similarity calculation
- In-memory cache for repeated text representations
- Diagnostic and latency metrics
"""

import hashlib
import logging
import time
from typing import Dict, List, Optional, Sequence, Union

from backend.app.config import get_settings

logger = logging.getLogger(__name__)


def compute_cosine_similarity(
    vector_a: Sequence[float],
    vector_b: Sequence[float],
) -> float:
    """Calculate the cosine similarity between two float vectors.

    Bounded strictly in [-1.0, 1.0]. Returns 0.0 if either vector has zero norm.
    Works natively with lists, tuples, or numpy ndarrays.
    """
    if not vector_a or not vector_b:
        return 0.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for a, b in zip(vector_a, vector_b):
        a_f = float(a)
        b_f = float(b)
        dot += a_f * b_f
        norm_a += a_f * a_f
        norm_b += b_f * b_f

    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0

    sim = dot / ((norm_a ** 0.5) * (norm_b ** 0.5))
    return float(max(-1.0, min(1.0, sim)))


class EmbeddingService:
    """Service providing embedding generation and cosine similarity calculation.

    Loads a SentenceTransformer model (default: all-MiniLM-L6-v2) lazily,
    ensuring thread-safe CPU-first inference, structured in-memory caching,
    and granular performance telemetry.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        settings = get_settings()
        self.model_name: str = model_name or settings.embedding_model_name
        self.device: str = device or "cpu"
        self._model = None
        self._model_version: Optional[str] = None
        self._load_duration_sec: float = 0.0

        # In-memory embedding cache keyed by SHA-256 hash of text
        self._cache: Dict[str, List[float]] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0

        # Performance telemetry
        self._total_embedded_texts: int = 0
        self._total_inference_time_sec: float = 0.0

    @property
    def model_version(self) -> str:
        """Return model identifier / version information."""
        return self._model_version or self.model_name

    def load_model(self):
        """Lazily load the SentenceTransformer model if not already loaded."""
        if self._model is not None:
            return self._model

        logger.info(
            "Loading SentenceTransformer model '%s' on device '%s'...",
            self.model_name,
            self.device,
        )
        start_time = time.perf_counter()

        try:
            from sentence_transformers import SentenceTransformer
            import sentence_transformers

            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._model_version = f"{self.model_name} (v{getattr(sentence_transformers, '__version__', 'unknown')})"
            self._load_duration_sec = time.perf_counter() - start_time
            logger.info(
                "Successfully loaded '%s' in %.3f seconds.",
                self.model_name,
                self._load_duration_sec,
            )
            return self._model
        except Exception as e:
            logger.error("Failed to load SentenceTransformer model '%s': %s", self.model_name, e)
            raise RuntimeError(
                f"Failed to initialize SentenceTransformer model '{self.model_name}': {e}. "
                f"Ensure 'sentence-transformers' and 'torch' are installed."
            ) from e

    def _hash_text(self, text: str) -> str:
        """Compute SHA-256 hash of text representation for cache key."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed_text(self, text: str) -> List[float]:
        """Generate vector embedding for a single string.

        Leverages in-memory cache if text has been embedded previously.
        """
        text_clean = text.strip() if text else ""
        if not text_clean:
            return []

        cache_key = self._hash_text(text_clean)
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]

        self._cache_misses += 1
        model = self.load_model()

        start_time = time.perf_counter()
        raw_embedding = model.encode(text_clean, convert_to_numpy=True)
        duration = time.perf_counter() - start_time

        embedding_list = [float(x) for x in raw_embedding]
        self._cache[cache_key] = embedding_list

        self._total_embedded_texts += 1
        self._total_inference_time_sec += duration

        return embedding_list

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of strings in batch.

        Reuses cached embeddings for recurring texts and batches remaining misses.
        """
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        miss_indices: List[int] = []
        miss_texts: List[str] = []

        for idx, text in enumerate(texts):
            text_clean = text.strip() if text else ""
            if not text_clean:
                results[idx] = []
                continue

            cache_key = self._hash_text(text_clean)
            if cache_key in self._cache:
                self._cache_hits += 1
                results[idx] = self._cache[cache_key]
            else:
                self._cache_misses += 1
                miss_indices.append(idx)
                miss_texts.append(text_clean)

        if miss_texts:
            model = self.load_model()
            start_time = time.perf_counter()
            batch_embeddings = model.encode(miss_texts, convert_to_numpy=True)
            duration = time.perf_counter() - start_time

            for idx, raw_emb in zip(miss_indices, batch_embeddings):
                emb_list = [float(x) for x in raw_emb]
                cache_key = self._hash_text(miss_texts[miss_indices.index(idx)])
                self._cache[cache_key] = emb_list
                results[idx] = emb_list

            self._total_embedded_texts += len(miss_texts)
            self._total_inference_time_sec += duration

        return [res if res is not None else [] for res in results]

    def cosine_similarity(
        self,
        vector_a: Sequence[float],
        vector_b: Sequence[float],
    ) -> float:
        """Compute cosine similarity between two vector representations."""
        return compute_cosine_similarity(vector_a, vector_b)

    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """Return cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_ratio = (self._cache_hits / total_requests) if total_requests > 0 else 0.0
        avg_latency_ms = (
            (self._total_inference_time_sec / self._total_embedded_texts) * 1000.0
            if self._total_embedded_texts > 0
            else 0.0
        )
        return {
            "cached_entries": len(self._cache),
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_ratio": round(hit_ratio, 4),
            "total_embedded_texts": self._total_embedded_texts,
            "load_duration_sec": round(self._load_duration_sec, 3),
            "avg_inference_latency_ms": round(avg_latency_ms, 2),
        }


# Global singleton instance
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
) -> EmbeddingService:
    """Retrieve or initialize the global EmbeddingService singleton."""
    global _embedding_service_instance
    if _embedding_service_instance is None or (
        model_name and _embedding_service_instance.model_name != model_name
    ):
        _embedding_service_instance = EmbeddingService(model_name=model_name, device=device)
    return _embedding_service_instance
