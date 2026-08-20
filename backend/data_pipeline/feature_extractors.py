"""
Feature Extractors
===================
Reusable functions that extract numerical features from essay text.
Used by Phase 3 (training pipeline) and later by the live system (Phase 6).

Feature Groups:
  A. Statistical   (3): perplexity, burstiness, entropy — via DistilGPT-2
  B. Stylometric  (11): sentence/word/paragraph stats, POS ratios, contractions
  C. Readability   (1): Flesch Reading Ease
  D. Semantic      (3): generic phrasing, personal voice, coherence — via regex
"""

import re
import math
import string
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONTRACTIONS = {
    "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't",
    "shouldn't", "isn't", "aren't", "wasn't", "weren't", "hasn't", "hasn't",
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

# Semantic patterns (reused from semantic_engine.py)
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

# Feature names in consistent order
FEATURE_NAMES = [
    # Statistical (3)
    "mean_perplexity",
    "perplexity_variance",
    "entropy",
    # Stylometric (11)
    "avg_sentence_length",
    "sentence_length_std",
    "type_token_ratio",
    "stop_word_ratio",
    "punctuation_frequency",
    "contraction_ratio",
    "noun_ratio",
    "verb_ratio",
    "adjective_ratio",
    "named_entity_density",
    "avg_paragraph_length",
    # Readability (1)
    "flesch_reading_ease",
    # Semantic (3)
    "generic_phrasing",
    "lack_of_personal_voice",
    "over_structured_coherence",
]


# ---------------------------------------------------------------------------
# B. Stylometric Features
# ---------------------------------------------------------------------------
def extract_stylometric_features(text: str, nlp=None) -> dict:
    """
    Extract stylometric features from text.
    
    Args:
        text: The essay text.
        nlp: A loaded spaCy model (en_core_web_sm). If None, POS/NER features
             will be set to 0.
    
    Returns:
        Dict with 11 stylometric features.
    """
    words = re.findall(r'\w+', text.lower())
    word_count = len(words) if words else 1  # avoid div-by-zero

    # --- Sentence-level stats ---
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    sent_lengths = [len(re.findall(r'\w+', s)) for s in sentences]
    sent_lengths = [l for l in sent_lengths if l > 0]  # remove empty

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

    # --- Type-Token Ratio ---
    unique_words = len(set(words))
    type_token_ratio = unique_words / word_count

    # --- Stop-word ratio ---
    stop_count = sum(1 for w in words if w in STOP_WORDS)
    stop_word_ratio = stop_count / word_count

    # --- Punctuation frequency ---
    punct_count = sum(1 for c in text if c in string.punctuation)
    total_chars = len(text) if len(text) > 0 else 1
    punctuation_frequency = punct_count / total_chars

    # --- Contraction ratio ---
    # Check against raw tokens preserving apostrophes
    raw_tokens = re.findall(r"\b[\w']+\b", text.lower())
    contraction_count = sum(1 for t in raw_tokens if t in CONTRACTIONS)
    contraction_ratio = contraction_count / word_count

    # --- POS ratios + NER density (via spaCy) ---
    noun_ratio = 0.0
    verb_ratio = 0.0
    adjective_ratio = 0.0
    named_entity_density = 0.0

    if nlp is not None:
        try:
            # Limit text length for spaCy efficiency
            doc = nlp(text[:10000])
            spacy_tokens = [t for t in doc if not t.is_space]
            n_tokens = len(spacy_tokens) if spacy_tokens else 1

            noun_count = sum(1 for t in spacy_tokens if t.pos_ in ("NOUN", "PROPN"))
            verb_count = sum(1 for t in spacy_tokens if t.pos_ == "VERB")
            adj_count = sum(1 for t in spacy_tokens if t.pos_ == "ADJ")

            noun_ratio = noun_count / n_tokens
            verb_ratio = verb_count / n_tokens
            adjective_ratio = adj_count / n_tokens

            ner_count = len(doc.ents)
            named_entity_density = ner_count / n_tokens
        except Exception as e:
            logger.warning(f"spaCy processing failed: {e}")

    # --- Paragraph stats ---
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]  # treat entire text as one paragraph
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
# C. Readability Features
# ---------------------------------------------------------------------------
def extract_readability_features(text: str) -> dict:
    """
    Extract readability metrics from text.
    Uses textstat library if available, otherwise manual calculation.
    """
    try:
        import textstat
        fre = textstat.flesch_reading_ease(text)
    except ImportError:
        # Manual Flesch Reading Ease calculation
        words = re.findall(r'\w+', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        word_count = len(words) if words else 1
        sent_count = len(sentences) if sentences else 1
        
        # Count syllables (rough approximation)
        def count_syllables(word):
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
        
        syllable_count = sum(count_syllables(w) for w in words)
        
        fre = 206.835 - 1.015 * (word_count / sent_count) - 84.6 * (syllable_count / word_count)

    return {
        "flesch_reading_ease": round(fre, 4),
    }


# ---------------------------------------------------------------------------
# D. Semantic Features
# ---------------------------------------------------------------------------
def extract_semantic_features(text: str) -> dict:
    """
    Extract semantic/style features using regex patterns.
    Mirrors logic from semantic_engine.py but returns raw scores for ML.
    """
    lower_text = text.lower()
    words = re.findall(r'\w+', lower_text)
    word_count = len(words) if words else 1

    # Generic phrasing
    generic_count = sum(len(re.findall(p, lower_text)) for p in GENERIC_PHRASES)
    generic_phrasing = min(1.0, (generic_count * 10) / word_count)

    # Lack of personal voice
    personal_count = sum(len(re.findall(p, lower_text)) for p in PERSONAL_VOICE)
    lack_of_personal_voice = max(0.0, 1.0 - ((personal_count * 5) / word_count))

    # Over-structured coherence
    transition_count = sum(len(re.findall(p, lower_text)) for p in AI_TRANSITIONS)
    over_structured_coherence = min(1.0, (transition_count * 15) / word_count)

    return {
        "generic_phrasing": round(generic_phrasing, 4),
        "lack_of_personal_voice": round(lack_of_personal_voice, 4),
        "over_structured_coherence": round(over_structured_coherence, 4),
    }


# ---------------------------------------------------------------------------
# A. Statistical Features (DistilGPT-2)
# ---------------------------------------------------------------------------
_stat_model = None
_stat_tokenizer = None
_stat_device = None


def _load_stat_model():
    """Lazy-load DistilGPT-2 model and tokenizer."""
    global _stat_model, _stat_tokenizer, _stat_device
    if _stat_model is not None:
        return

    import torch
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast

    _stat_device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        _stat_tokenizer = GPT2TokenizerFast.from_pretrained("distilgpt2", local_files_only=True)
        _stat_model = GPT2LMHeadModel.from_pretrained("distilgpt2", local_files_only=True).to(_stat_device)
    except Exception:
        _stat_tokenizer = GPT2TokenizerFast.from_pretrained("distilgpt2")
        _stat_model = GPT2LMHeadModel.from_pretrained("distilgpt2").to(_stat_device)
    _stat_model.eval()
    logger.info(f"Loaded distilgpt2 on {_stat_device}")


def extract_statistical_features(text: str) -> dict:
    """
    Extract perplexity, burstiness (variance), and entropy using DistilGPT-2.
    """
    import torch

    _load_stat_model()

    try:
        encodings = _stat_tokenizer(
            text, return_tensors="pt", truncation=True, max_length=1024
        )
        input_ids = encodings.input_ids.to(_stat_device)

        with torch.no_grad():
            outputs = _stat_model(input_ids, labels=input_ids)
            loss = outputs.loss
            logits = outputs.logits

        # Mean perplexity
        clamped_loss = torch.clamp(loss, max=50.0)
        mean_perplexity = torch.exp(clamped_loss).item()

        # Token-level losses for variance
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        token_losses = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        )

        perplexity_variance = torch.var(token_losses).item()
        entropy = torch.mean(token_losses).item()

        return {
            "mean_perplexity": round(mean_perplexity, 4),
            "perplexity_variance": round(perplexity_variance, 4),
            "entropy": round(entropy, 4),
        }

    except Exception as e:
        logger.error(f"Statistical feature extraction failed: {e}")
        return {
            "mean_perplexity": 50.0,
            "perplexity_variance": 1.0,
            "entropy": 3.0,
        }


# ---------------------------------------------------------------------------
# Full Extraction
# ---------------------------------------------------------------------------
def extract_all_features(text: str, nlp=None) -> dict:
    """
    Extract all 18 features from a single essay.
    
    Args:
        text: Essay text.
        nlp: Loaded spaCy model (optional, for POS/NER features).
    
    Returns:
        Dict with all 18 features keyed by FEATURE_NAMES.
    """
    features = {}
    features.update(extract_statistical_features(text))
    features.update(extract_stylometric_features(text, nlp=nlp))
    features.update(extract_readability_features(text))
    features.update(extract_semantic_features(text))
    return features
