"""
Confidence Calibration & Similarity Metrics.
Provides string similarity metrics (Levenshtein distance) and score calibration.
"""

from typing import Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def compute_string_similarity(s1: str, s2: str) -> float:
    """
    Computes normalized string similarity in [0.0, 1.0].
    1.0 = exact match, 0.0 = completely disjoint.
    """
    s1_clean = s1.strip().lower()
    s2_clean = s2.strip().lower()

    if not s1_clean and not s2_clean:
        return 1.0
    if not s1_clean or not s2_clean:
        return 0.0

    max_len = max(len(s1_clean), len(s2_clean))
    dist = levenshtein_distance(s1_clean, s2_clean)
    return max(0.0, 1.0 - (dist / float(max_len)))


def calibrate_confidence(
    base_conf: float,
    similarity: float,
    length: int,
    is_specialized: bool = False
) -> float:
    """
    Calibrates confidence based on model agreement, token length, and specialization.
    """
    conf = base_conf

    # High agreement bonus
    if similarity >= 0.85:
        conf = min(0.99, conf + 0.05 * similarity)
    # Severe disagreement penalty
    elif similarity < 0.40:
        conf = max(0.20, conf - 0.15 * (1.0 - similarity))

    # Specialization boost
    if is_specialized:
        conf = min(0.99, conf + 0.04)

    # Empty string penalty
    if length == 0:
        return 0.0

    return round(float(conf), 3)
