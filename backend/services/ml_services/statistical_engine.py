"""
Layer 1: Statistical Analysis Engine (Neural-Heuristic Analysis)
Computes perplexity, entropy, and burstiness using distilgpt2.
"""

import math
import logging
import os
import pickle
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

logger = logging.getLogger(__name__)

# Silence noisy HuggingFace and HTTP loggers
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

_device = None
_tokenizer = None
_model = None
_gpt2_initialized = False


def get_gpt2_model():
    """Lazy-load distilgpt2 model and tokenizer (offline-first)."""
    global _device, _tokenizer, _model, _gpt2_initialized
    if _gpt2_initialized:
        return _tokenizer, _model, _device

    _gpt2_initialized = True
    try:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            # Try offline cache first to avoid remote HTTP HEAD/GET checks
            _tokenizer = GPT2TokenizerFast.from_pretrained("distilgpt2", local_files_only=True)
            _model = GPT2LMHeadModel.from_pretrained("distilgpt2", local_files_only=True).to(_device)
        except Exception:
            # Fallback to online download if cache is empty
            _tokenizer = GPT2TokenizerFast.from_pretrained("distilgpt2")
            _model = GPT2LMHeadModel.from_pretrained("distilgpt2").to(_device)

        _model.eval()
        logger.info(f"Loaded distilgpt2 for Statistical Engine on {_device}")
    except Exception as e:
        logger.error(f"Failed to load distilgpt2: {e}")
        _tokenizer = None
        _model = None

    return _tokenizer, _model, _device


# Load the trained Scikit-learn Classifier
try:
    clf_path = os.path.join(os.path.dirname(__file__), "ai_classifier.pkl")
    if os.path.exists(clf_path):
        with open(clf_path, "rb") as f:
            classifier = pickle.load(f)
        logger.info("Loaded RandomForest statistical AI classifier.")
    else:
        classifier = None
        logger.warning("Statistical AI classifier not found. Will use fallback math.")
except Exception as e:
    logger.error(f"Failed to load AI classifier: {e}")
    classifier = None


def analyze_statistics(text: str) -> dict:
    """
    Computes mathematical signals of AI generation from a local LLM.
    Returns perplexity, entropy, burstiness, and a likelihood score.
    """
    if not text or len(text.strip()) < 50:
        return _fallback_stats()

    tokenizer, model, device = get_gpt2_model()
    if model is None or tokenizer is None:
        logger.warning("Statistical engine model not loaded. Using fallback.")
        return _fallback_stats()

    try:
        # Tokenize text
        encodings = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
        input_ids = encodings.input_ids.to(device)

        with torch.no_grad():
            outputs = model(input_ids, labels=input_ids)
            loss = outputs.loss
            logits = outputs.logits

        # 1. Perplexity
        # Clip loss to avoid infinity in exp()
        clamped_loss = torch.clamp(loss, max=50.0)
        mean_perplexity = torch.exp(clamped_loss).item()
        
        # 2. Extract Token Log-Probabilities & Entropy
        # Shift logits and labels for next-token prediction
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()
        
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        token_losses = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        
        # Perplexity variance (Burstiness indicator)
        perplexity_variance = torch.var(token_losses).item()
        max_perplexity_spike = torch.max(token_losses).item()
        
        # Approximate entropy from token losses
        entropy = torch.mean(token_losses).item()

        # 3. Compute Burstiness (variance of losses)
        # Low variance means highly uniform probabilities = Machine
        # High variance means bursts of predictability and unpredictability = Human
        burstiness = perplexity_variance

        # 4. Normalization and Scoring
        # Scale burstiness properly for logging
        uniformity_score = max(0.0, min(1.0, 1.0 - ((burstiness - 2.0) / 10.0)))
        
        if classifier is not None:
            # Use trained ML model for accurate probabilities
            features = [[mean_perplexity, perplexity_variance, entropy]]
            prob_ai = classifier.predict_proba(features)[0][1]
            ai_likelihood = prob_ai * 100.0
            
            # Estimate perp_score purely for UI metadata
            perp_score = max(0.0, 100.0 - mean_perplexity)
        else:
            # Fallback to hand-tuned math
            if mean_perplexity < 45.0:
                perp_score = 90.0 # Very likely AI
            elif mean_perplexity > 90.0:
                perp_score = 10.0 # Very likely Human
            else:
                perp_score = 90.0 - ((mean_perplexity - 45.0) / 45.0) * 80.0
                
            ai_likelihood = (perp_score * 0.4) + (uniformity_score * 100 * 0.6)
        
        pattern_type = "uniform" if uniformity_score > 0.7 else "irregular" if uniformity_score < 0.3 else "mixed"
        risk_level = "high" if ai_likelihood > 75 else "moderate" if ai_likelihood > 45 else "low"
        
        reasoning = f"Perplexity is {mean_perplexity:.1f}. Pattern is {pattern_type} with variance {burstiness:.2f}."

        return {
            "normalized_perplexity": round(perp_score, 2),
            "mean_perplexity": round(mean_perplexity, 2),
            "perplexity_variance": round(perplexity_variance, 2),
            "max_perplexity_spike": round(max_perplexity_spike, 2),
            "burstiness": round(burstiness, 2),
            "entropy": round(entropy, 2),
            "uniformity_score": round(uniformity_score, 2),
            "z_score_human": 0.0, # Placeholder
            "statistical_ai_likelihood": round(max(0, min(100, ai_likelihood)), 2),
            "confidence": 0.8,
            "pattern_type": pattern_type,
            "risk_level": risk_level,
            "reasoning": reasoning
        }

    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        return _fallback_stats()


def _fallback_stats():
    return {
        "normalized_perplexity": 50.0,
        "mean_perplexity": 50.0,
        "perplexity_variance": 1.0,
        "max_perplexity_spike": 5.0,
        "burstiness": 1.0,
        "entropy": 3.0,
        "uniformity_score": 0.5,
        "z_score_human": 0.0,
        "statistical_ai_likelihood": 50.0,
        "confidence": 0.1,
        "pattern_type": "mixed",
        "risk_level": "moderate",
        "reasoning": "Fallback used due to insufficient text or model failure."
    }
