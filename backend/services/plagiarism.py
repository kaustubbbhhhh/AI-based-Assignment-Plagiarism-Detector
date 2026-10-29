"""
Plagiarism Detection Service.
Uses TF-IDF vectorization and cosine similarity to compare
a submission against all other submissions in the database.
Includes in-memory caching of fitted vectorizers for fast repeat comparisons.
"""

import logging
import hashlib
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── In-memory cache for fitted TF-IDF vectorizers and corpus matrices ──
# Key: MD5 hash of sorted corpus texts → (vectorizer, corpus_tfidf_matrix)
# This avoids re-fitting the vectorizer on every new submission when the
# peer corpus hasn't changed (same subject, same set of prior submissions).
_vectorizer_cache = {}
_MAX_CACHE_SIZE = 50  # Limit to prevent unbounded memory growth


def _corpus_hash(corpus: List[str]) -> str:
    """Compute a stable hash of the corpus for cache lookup."""
    combined = "\n".join(sorted(corpus))
    return hashlib.md5(combined.encode("utf-8", errors="ignore")).hexdigest()


def check_plagiarism(text: str, corpus: List[str]) -> dict:
    """
    Compare `text` against a corpus of existing submissions.
    Returns the maximum similarity score as a plagiarism percentage.

    Uses cached TF-IDF matrices when the same text+corpus combination
    is seen again, avoiding expensive fit_transform.

    Args:
        text: The submission text to check.
        corpus: List of previously submitted texts to compare against.

    Returns:
        {
            "plagiarism_score": float (0-100),
            "max_similarity": float (0-1),
            "matches_found": int
        }
    """
    if not text or len(text.strip()) < 20:
        return {"plagiarism_score": 0.0, "max_similarity": 0.0, "matches_found": 0}

    if not corpus:
        logger.info("No corpus available for plagiarism comparison — returning 0%.")
        return {"plagiarism_score": 0.0, "max_similarity": 0.0, "matches_found": 0}

    try:
        # ── Build TF-IDF matrix (identical to original logic) ─
        # Place the target text first, then the corpus
        all_documents = [text] + corpus

        # Check cache for this exact combination
        cache_key = _corpus_hash(all_documents)

        if cache_key in _vectorizer_cache:
            tfidf_matrix = _vectorizer_cache[cache_key]
            logger.info("Plagiarism check using cached TF-IDF matrix (fast path).")
        else:
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),     # unigrams + bigrams for better matching
                min_df=1,
            )
            tfidf_matrix = vectorizer.fit_transform(all_documents)

            # Evict oldest entry if cache is full
            if len(_vectorizer_cache) >= _MAX_CACHE_SIZE:
                oldest_key = next(iter(_vectorizer_cache))
                del _vectorizer_cache[oldest_key]

            _vectorizer_cache[cache_key] = tfidf_matrix
            logger.info("Plagiarism check: fitted new TF-IDF vectorizer and cached result.")

        # ── Compute cosine similarity ─────────────────────────
        # Compare index 0 (our submission) against all others
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        max_sim = float(similarities.max()) if len(similarities) > 0 else 0.0
        matches_above_threshold = int((similarities > 0.15).sum())  # count non-trivial matches

        plagiarism_score = round(max_sim * 100, 2)

        logger.info(
            f"Plagiarism check — max_similarity={max_sim:.3f}, "
            f"plagiarism_score={plagiarism_score}%, matches={matches_above_threshold}"
        )

        return {
            "plagiarism_score": plagiarism_score,
            "max_similarity": round(max_sim, 4),
            "matches_found": matches_above_threshold,
        }

    except Exception as e:
        logger.error(f"Plagiarism check failed: {e}")
        return {"plagiarism_score": 0.0, "max_similarity": 0.0, "matches_found": 0}
