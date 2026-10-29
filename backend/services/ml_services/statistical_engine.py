"""
Layer 1: Statistical Analysis Engine (Neural-Heuristic Analysis)
Computes perplexity, entropy, and sentence-level burstiness using Qwen 2.5 (0.5B).
"""

import math
import logging
import os
import re
import pickle
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

# Silence noisy HuggingFace and HTTP loggers
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODEL_NAME = "Qwen/Qwen2.5-0.5B"

_device = None
_tokenizer = None
_model = None
_model_initialized = False


def get_statistical_model():
    """Lazy-load Qwen 2.5 0.5B model and tokenizer (offline-first)."""
    global _device, _tokenizer, _model, _model_initialized
    if _model_initialized:
        return _tokenizer, _model, _device

    _model_initialized = True
    try:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if _device == "cuda" else torch.float32

        try:
            # Try offline cache first to avoid remote HTTP HEAD/GET checks
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                dtype=dtype,
                low_cpu_mem_usage=True,
                local_files_only=True
            ).to(_device)
        except Exception:
            # Fallback to online download if cache is empty
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                dtype=dtype,
                low_cpu_mem_usage=True
            ).to(_device)

        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token

        _model.eval()
        logger.info(f"Loaded Qwen 2.5 0.5B for Statistical Engine on {_device}")
    except Exception as e:
        logger.error(f"Failed to load Qwen 2.5 0.5B: {e}")
        _tokenizer = None
        _model = None

    return _tokenizer, _model, _device


# Statistical model getter & compatibility aliases
get_qwen_model = get_statistical_model
get_gpt2_model = get_statistical_model


# Load the trained Scikit-learn Classifier
try:
    clf_path = os.path.join(os.path.dirname(__file__), "ai_classifier.pkl")
    if os.path.exists(clf_path):
        with open(clf_path, "rb") as f:
            classifier = pickle.load(f)
        logger.info("Loaded RandomForest statistical AI classifier.")
    else:
        classifier = None
        logger.warning("Statistical AI classifier not found. Will use calibrated statistical rules.")
except Exception as e:
    logger.error(f"Failed to load AI classifier: {e}")
    classifier = None


def _split_sentences(text: str):
    """Splits text into non-empty sentences or bullet items."""
    raw = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [s.strip() for s in raw if len(s.strip().split()) >= 3]


def analyze_statistics(text: str) -> dict:
    """
    Computes mathematical signals of AI generation from Qwen 2.5.
    Returns perplexity, entropy, sentence burstiness, and a likelihood score.
    """
    if not text or len(text.strip()) < 50:
        return _fallback_stats()

    tokenizer, model, device = get_statistical_model()
    if model is None or tokenizer is None:
        logger.warning("Statistical engine model not loaded. Using fallback.")
        return _fallback_stats()

    try:
        # Tokenize full text
        encodings = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
        input_ids = encodings.input_ids.to(device)

        with torch.inference_mode():
            outputs = model(input_ids, labels=input_ids)
            loss = outputs.loss
            logits = outputs.logits

        # 1. Perplexity (bounded)
        clamped_loss = torch.clamp(loss, max=25.0)
        mean_perplexity = torch.exp(clamped_loss).item()

        # 2. Extract Token Log-Probabilities & Entropy
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()

        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        token_losses = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

        perplexity_variance = torch.var(token_losses).item()
        max_perplexity_spike = torch.max(token_losses).item()
        entropy = torch.mean(token_losses).item()

        # 3. Compute Sentence-Level Burstiness (Coefficient of Variation)
        sentences = _split_sentences(text)
        sent_losses = []
        for s in sentences:
            s_enc = tokenizer(s, return_tensors="pt", truncation=True, max_length=512)
            s_ids = s_enc.input_ids.to(device)
            if s_ids.shape[1] > 2:
                with torch.inference_mode():
                    s_loss = model(s_ids, labels=s_ids).loss.item()
                    sent_losses.append(math.exp(min(s_loss, 20.0)))

        if len(sent_losses) > 1:
            mean_sent_ppl = sum(sent_losses) / len(sent_losses)
            var_sent = sum((x - mean_sent_ppl) ** 2 for x in sent_losses) / (len(sent_losses) - 1)
            burstiness_cv = math.sqrt(var_sent) / mean_sent_ppl if mean_sent_ppl > 0 else 0.0
        else:
            burstiness_cv = 0.0

        # Preserve both raw token variance and normalized sentence burstiness
        burstiness = perplexity_variance

        # 4. Normalization and Scoring
        # In Qwen 2.5: AI text is smooth (CV < 0.20, low loss var), Human has high CV (> 0.50)
        uniformity_score = max(0.0, min(1.0, 1.0 - (burstiness_cv / 0.8)))

        if classifier is not None:
            features = [[mean_perplexity, perplexity_variance, entropy]]
            prob_ai = classifier.predict_proba(features)[0][1]
            ai_likelihood = prob_ai * 100.0
            perp_score = max(0.0, 100.0 - mean_perplexity)
        else:
            # Calibrated for Qwen 2.5 baseline (AI PPL typically 15-35, Human PPL 25-100+)
            if mean_perplexity < 18.0:
                perp_score = 85.0
            elif mean_perplexity > 50.0:
                perp_score = 15.0
            else:
                perp_score = 85.0 - ((mean_perplexity - 18.0) / 32.0) * 70.0

            ai_likelihood = (perp_score * 0.4) + (uniformity_score * 100 * 0.6)

        pattern_type = "uniform" if uniformity_score > 0.65 else "irregular" if uniformity_score < 0.35 else "mixed"
        risk_level = "high" if ai_likelihood > 70 else "moderate" if ai_likelihood > 40 else "low"

        reasoning = (
            f"Qwen 2.5 Perplexity is {mean_perplexity:.1f}. "
            f"Sentence burstiness CV is {burstiness_cv:.2f} ({pattern_type} cadence)."
        )

        return {
            "normalized_perplexity": round(perp_score, 2),
            "mean_perplexity": round(mean_perplexity, 2),
            "perplexity_variance": round(perplexity_variance, 2),
            "max_perplexity_spike": round(max_perplexity_spike, 2),
            "burstiness": round(burstiness, 2),
            "burstiness_cv": round(burstiness_cv, 4),
            "entropy": round(entropy, 2),
            "uniformity_score": round(uniformity_score, 2),
            "z_score_human": 0.0,
            "statistical_ai_likelihood": round(max(0, min(100, ai_likelihood)), 2),
            "confidence": 0.85,
            "pattern_type": pattern_type,
            "risk_level": risk_level,
            "reasoning": reasoning
        }

    except Exception as e:
        logger.error(f"Statistical analysis with Qwen 2.5 failed: {e}")
        return _fallback_stats()


def _fallback_stats():
    return {
        "normalized_perplexity": 50.0,
        "mean_perplexity": 50.0,
        "perplexity_variance": 1.0,
        "max_perplexity_spike": 5.0,
        "burstiness": 1.0,
        "burstiness_cv": 0.0,
        "entropy": 3.0,
        "uniformity_score": 0.5,
        "z_score_human": 0.0,
        "statistical_ai_likelihood": 50.0,
        "confidence": 0.1,
        "pattern_type": "mixed",
        "risk_level": "moderate",
        "reasoning": "Fallback used due to insufficient text or model failure."
    }
