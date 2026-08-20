"""
Feature Extractors for Live AI Detection System
=================================================
Extracts the full 18-feature vector from essay text at inference time.
Reuses the existing statistical_engine (DistilGPT-2) and semantic_engine
for their respective features, and adds stylometric + readability features.

This module is used by ai_detection.py to feed the trained RF classifier.
"""

import re
import math
import string
import logging
import os
import json
import pickle
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load feature names, model, and scaler
# ---------------------------------------------------------------------------
_ml_dir = os.path.dirname(__file__)

# Feature names (ordered list matching training)
_feature_names_path = os.path.join(_ml_dir, "feature_names.json")
try:
    with open(_feature_names_path, "r") as f:
        FEATURE_NAMES = json.load(f)
    logger.info(f"Loaded {len(FEATURE_NAMES)} feature names.")
except Exception as e:
    logger.warning(f"Could not load feature_names.json: {e}")
    FEATURE_NAMES = []

# Trained RF model (v2 = 18-feature model from data pipeline)
_model_path = os.path.join(_ml_dir, "rf_model_v2.pkl")
try:
    if os.path.exists(_model_path):
        with open(_model_path, "rb") as f:
            rf_model_v2 = pickle.load(f)
        logger.info("Loaded v2 RandomForest AI classifier (18 features).")
    else:
        rf_model_v2 = None
        logger.warning("rf_model_v2.pkl not found. V2 classifier unavailable.")
except Exception as e:
    logger.error(f"Failed to load rf_model_v2: {e}")
    rf_model_v2 = None

# Scaler
_scaler_path = os.path.join(_ml_dir, "scaler_v2.pkl")
try:
    if os.path.exists(_scaler_path):
        with open(_scaler_path, "rb") as f:
            scaler_v2 = pickle.load(f)
        logger.info("Loaded v2 StandardScaler.")
    else:
        scaler_v2 = None
except Exception as e:
    logger.error(f"Failed to load scaler_v2: {e}")
    scaler_v2 = None

# spaCy model (lazy loaded)
_nlp = None

def _get_nlp():
    """Lazy-load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
            logger.info("Loaded spaCy en_core_web_sm for feature extraction.")
        except Exception as e:
            logger.warning(f"Could not load spaCy model: {e}. POS/NER features will be 0.")
            _nlp = False  # sentinel to avoid retrying
    return _nlp if _nlp is not False else None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONTRACTIONS = {
    "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't",
    "shouldn't", "isn't", "aren't", "wasn't", "weren't", "hasn't",
    "haven't", "hadn't", "i'm", "i've", "i'd", "i'll", "we're", "we've",
    "we'd", "we'll", "you're", "you've", "you'd", "you'll", "they're",
    "they've", "they'd", "they'll", "he's", "she's", "it's", "that's",
    "there's", "here's", "what's", "who's", "let's", "ain't",
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "am", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "dare", "ought", "used", "it", "its", "this", "that", "these", "those",
    "i", "me", "my", "mine", "we", "us", "our", "ours", "you", "your",
    "yours", "he", "him", "his", "she", "her", "hers", "they", "them",
    "their", "theirs", "what", "which", "who", "whom", "where", "when",
    "how", "not", "no", "nor", "as", "if", "so", "than", "too", "very",
    "just", "about", "above", "after", "again", "all", "also", "any",
    "because", "before", "between", "both", "each", "few", "more", "most",
    "other", "over", "own", "same", "some", "such", "then", "through",
    "under", "until", "up", "while",
}

# Semantic patterns (same as semantic_engine.py + pipeline feature_extractors.py)
AI_TRANSITIONS = [
    r"\bfurthermore\b", r"\bmoreover\b", r"\bin conclusion\b", r"\bconsequently\b",
    r"\badditionally\b", r"\bhowever\b", r"\btherefore\b", r"\bthus\b",
    r"\bto summarize\b", r"\bultimately\b", r"\bfirstly\b", r"\bsecondly\b",
    r"\bdelving into\b", r"\bit is important to note\b", r"\bcrucially\b",
    r"\bin essence\b", r"\bat its core\b", r"\ball in all\b",
    r"\btaking everything into consideration\b",
    r"\bit is worth noting that\b", r"\bone could argue\b", r"\bto begin with\b",
    r"\bin this essay\b", r"\bwe will explore\b", r"\bthe landscape of\b",
    r"\bthe realm of\b", r"\bnavigating the complexities\b", r"\bmultifaceted\b",
    r"\ba critical aspect of\b", r"\bprior to\b", r"\bsubsequently\b",
]

PERSONAL_VOICE = [
    r"\bi\b", r"\bmy\b", r"\bme\b", r"\bmine\b", r"\bwe\b", r"\bour\b", r"\bus\b",
    r"\bexperience\b", r"\bfelt\b", r"\bthink\b", r"\bbelieve\b", r"\bnotice\b",
    r"\bremember\b", r"\bguess\b", r"\bmaybe\b", r"\bprobably\b", r"\bhonestly\b",
    r"\bhopefully\b", r"\bpersonally\b", r"\bactually\b", r"\bliterally\b",
    r"\bkind of\b", r"\bbasically\b",
]

GENERIC_PHRASES = [
    r"\bcan be defined as\b", r"\bplays a crucial role\b", r"\bis a multifaceted\b",
    r"\bhas garnered significant attention\b", r"\blandscape of\b", r"\brealm of\b",
    r"\blet's dive in\b", r"\bin today's fast-paced\b", r"\ba testament to\b",
    r"\bever-evolving\b", r"\brapidly changing\b", r"\btechnological advancements\b",
    r"\bsignificant impact\b", r"\bprofound effect\b", r"\bvital component\b",
    r"\bnot merely\b", r"\bbut also\b", r"\bstands as a\b", r"\bshed light on\b",
    r"\bdelve deeper\b", r"\buncover\b", r"\btransformative\b", r"\bseamless\b",
]


# ---------------------------------------------------------------------------
# Stylometric Features
# ---------------------------------------------------------------------------
def _extract_stylometric(text: str) -> dict:
    """Extract 11 stylometric features."""
    words = re.findall(r'\w+', text.lower())
    word_count = len(words) if words else 1

    # Sentence-level stats
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sent_lengths = [len(re.findall(r'\w+', s)) for s in sentences]
    sent_lengths = [l for l in sent_lengths if l > 0]

    if sent_lengths:
        avg_sentence_length = sum(sent_lengths) / len(sent_lengths)
        if len(sent_lengths) > 1:
            mean_sl = avg_sentence_length
            variance = sum((l - mean_sl) ** 2 for l in sent_lengths) / (len(sent_lengths) - 1)
            sentence_length_std = math.sqrt(variance)
        else:
            sentence_length_std = 0.0
    else:
        avg_sentence_length = 0.0
        sentence_length_std = 0.0

    # Type-Token Ratio
    unique_words = len(set(words))
    type_token_ratio = unique_words / word_count

    # Stop-word ratio
    stop_count = sum(1 for w in words if w in STOP_WORDS)
    stop_word_ratio = stop_count / word_count

    # Punctuation frequency
    punct_count = sum(1 for c in text if c in string.punctuation)
    total_chars = len(text) if len(text) > 0 else 1
    punctuation_frequency = punct_count / total_chars

    # Contraction ratio
    raw_tokens = re.findall(r"\b[\w']+\b", text.lower())
    contraction_count = sum(1 for t in raw_tokens if t in CONTRACTIONS)
    contraction_ratio = contraction_count / word_count

    # POS ratios + NER density (via spaCy)
    noun_ratio = 0.0
    verb_ratio = 0.0
    adjective_ratio = 0.0
    named_entity_density = 0.0

    nlp = _get_nlp()
    if nlp is not None:
        try:
            doc = nlp(text[:10000])
            spacy_tokens = [t for t in doc if not t.is_space]
            n_tokens = len(spacy_tokens) if spacy_tokens else 1

            noun_ratio = sum(1 for t in spacy_tokens if t.pos_ in ("NOUN", "PROPN")) / n_tokens
            verb_ratio = sum(1 for t in spacy_tokens if t.pos_ == "VERB") / n_tokens
            adjective_ratio = sum(1 for t in spacy_tokens if t.pos_ == "ADJ") / n_tokens
            named_entity_density = len(doc.ents) / n_tokens
        except Exception as e:
            logger.warning(f"spaCy processing failed: {e}")

    # Paragraph stats
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    para_lengths = [len(re.findall(r'\w+', p)) for p in paragraphs]
    avg_paragraph_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0.0

    return {
        "avg_sentence_length": round(avg_sentence_length, 4),
        "sentence_length_std": round(sentence_length_std, 4),
        "type_token_ratio": round(type_token_ratio, 4),
        "stop_word_ratio": round(stop_word_ratio, 4),
        "punctuation_frequency": round(punctuation_frequency, 4),
        "contraction_ratio": round(contraction_ratio, 4),
        "noun_ratio": round(noun_ratio, 4),
        "verb_ratio": round(verb_ratio, 4),
        "adjective_ratio": round(adjective_ratio, 4),
        "named_entity_density": round(named_entity_density, 4),
        "avg_paragraph_length": round(avg_paragraph_length, 4),
    }


# ---------------------------------------------------------------------------
# Readability Features
# ---------------------------------------------------------------------------
def _extract_readability(text: str) -> dict:
    """Extract Flesch Reading Ease score."""
    try:
        import textstat
        fre = textstat.flesch_reading_ease(text)
    except ImportError:
        words = re.findall(r'\w+', text)
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        word_count = len(words) if words else 1
        sent_count = len(sentences) if sentences else 1

        def _syllables(word):
            word = word.lower()
            count = 0
            vowels = "aeiou"
            if word[0] in vowels:
                count += 1
            for i in range(1, len(word)):
                if word[i] in vowels and word[i - 1] not in vowels:
                    count += 1
            if word.endswith("e"):
                count -= 1
            return max(count, 1)

        syllable_count = sum(_syllables(w) for w in words)
        fre = 206.835 - 1.015 * (word_count / sent_count) - 84.6 * (syllable_count / word_count)

    return {"flesch_reading_ease": round(fre, 4)}


# ---------------------------------------------------------------------------
# Semantic Features
# ---------------------------------------------------------------------------
def _extract_semantic(text: str) -> dict:
    """Extract 3 semantic/style features via regex."""
    lower_text = text.lower()
    words = re.findall(r'\w+', lower_text)
    word_count = len(words) if words else 1

    generic_count = sum(len(re.findall(p, lower_text)) for p in GENERIC_PHRASES)
    generic_phrasing = min(1.0, (generic_count * 10) / word_count)

    personal_count = sum(len(re.findall(p, lower_text)) for p in PERSONAL_VOICE)
    lack_of_personal_voice = max(0.0, 1.0 - ((personal_count * 5) / word_count))

    transition_count = sum(len(re.findall(p, lower_text)) for p in AI_TRANSITIONS)
    over_structured_coherence = min(1.0, (transition_count * 15) / word_count)

    return {
        "generic_phrasing": round(generic_phrasing, 4),
        "lack_of_personal_voice": round(lack_of_personal_voice, 4),
        "over_structured_coherence": round(over_structured_coherence, 4),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def is_v2_available() -> bool:
    """Check if the v2 model (18-feature) is loaded and ready."""
    return rf_model_v2 is not None and scaler_v2 is not None and len(FEATURE_NAMES) > 0


def extract_and_predict(text: str, stats: dict) -> dict:
    """
    Extract full 18-feature vector, scale it, and predict AI probability.

    Args:
        text: The essay text.
        stats: Pre-computed statistical features from analyze_statistics()
               (must contain mean_perplexity, perplexity_variance, entropy).

    Returns:
        Dict with ai_probability (0-1), ai_score (0-100), and feature_vector.
    """
    if not is_v2_available():
        return None

    try:
        # 1. Gather all features
        features = {}

        # Statistical (from pre-computed stats — avoids running DistilGPT-2 twice)
        features["mean_perplexity"] = stats.get("mean_perplexity", 50.0)
        features["perplexity_variance"] = stats.get("perplexity_variance", 1.0)
        features["entropy"] = stats.get("entropy", 3.0)

        # Stylometric (new)
        features.update(_extract_stylometric(text))

        # Readability (new)
        features.update(_extract_readability(text))

        # Semantic (new — previously only used in Layer 2 scoring)
        features.update(_extract_semantic(text))

        # 2. Build ordered feature vector matching FEATURE_NAMES
        feature_vector = np.array([[features[name] for name in FEATURE_NAMES]])

        # 3. Scale
        feature_vector_scaled = scaler_v2.transform(feature_vector)

        # 4. Predict
        prob_ai = rf_model_v2.predict_proba(feature_vector_scaled)[0][1]
        ai_score = prob_ai * 100.0

        return {
            "ai_probability": round(prob_ai, 4),
            "ai_score": round(ai_score, 2),
            "feature_vector": {name: round(features[name], 4) for name in FEATURE_NAMES},
            "model_version": "v2_random_forest_18features",
        }

    except Exception as e:
        logger.error(f"V2 feature extraction/prediction failed: {e}")
        return None
