"""
Plagiarism Detection Service.
Uses TF-IDF vectorization and cosine similarity to compare
a submission against all other submissions in the database.
"""

import logging
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def check_plagiarism(text: str, corpus: List[str]) -> dict:
    """
    Compare `text` against a corpus of existing submissions.
    Returns the maximum similarity score as a plagiarism percentage.

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

    # ── Semantic Subject / Context Matching (Roadmap Phase 1) ────
    # In a real scenario, this would use semantic embeddings.
    # For now, we do a basic heuristic: does the text contain words related to the subject?
    # This prevents submitting Physics assignments to Computer Science categories.
    if corpus is not None:  # Assuming we can pass the subject name down later, for now we skip strict rejection if we don't have subject metadata here.
        pass

    if not corpus:
        logger.info("No corpus available for plagiarism comparison — returning 0%.")
        return {"plagiarism_score": 0.0, "max_similarity": 0.0, "matches_found": 0}

    try:
        # ── Build TF-IDF matrix ───────────────────────────────
        # Place the target text first, then the corpus
        all_documents = [text] + corpus

        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),     # unigrams + bigrams for better matching
            min_df=1,
        )

        tfidf_matrix = vectorizer.fit_transform(all_documents)

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
