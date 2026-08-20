"""
Fusion Engine (AI Detection Architecture)
==========================================
Uses the trained v2 Random Forest classifier (18 features) when available,
with fallback to the legacy two-layer fusion (60/40 weighted) when not.

The v2 model was trained on 2,739 labeled essays with features spanning:
  - Statistical: perplexity, burstiness, entropy (DistilGPT-2)
  - Stylometric: sentence lengths, TTR, contractions, POS ratios, NER density
  - Readability: Flesch Reading Ease
  - Semantic: generic phrasing, personal voice, over-structured coherence

Layer 1 (statistical_engine) and Layer 2 (semantic_engine) continue to run
as feature extractors and their detailed output is still returned in the
response for UI transparency.
"""

import logging
from .ml_services.statistical_engine import analyze_statistics
from .ml_services.semantic_engine import analyze_semantics
from .ml_services.feature_extractors import is_v2_available, extract_and_predict

logger = logging.getLogger(__name__)


def analyze_ai_content(text: str) -> dict:
    """
    Run AI detection analysis on the given text.
    
    Uses v2 trained classifier when available, otherwise falls back
    to legacy two-layer fusion.
    
    Returns final decision JSON with ai_score, label, reasoning, and
    per-layer details.
    """
    if not text or len(text.strip()) < 50:
        return {"ai_score": 0.0, "label": "Original", "reasoning": "Text too short."}

    try:
        # Always run both layers (needed for UI details + v2 feature input)
        stats = analyze_statistics(text)
        semantics = analyze_semantics(text)

        # --- Try V2 Model (trained RF classifier) ---
        if is_v2_available():
            v2_result = extract_and_predict(text, stats)
        else:
            v2_result = None

        if v2_result is not None:
            final_score = v2_result["ai_score"]
            model_version = v2_result["model_version"]

            # Determine label from calibrated probability
            if final_score > 70:
                label = "AI-generated"
                reasoning = "Trained classifier detected strong AI patterns across statistical, stylistic, and semantic features."
            elif final_score < 30:
                label = "Original"
                reasoning = "Trained classifier found human-like writing patterns: natural variance, personal voice, and unpredictable structure."
            else:
                label = "Mixed"
                reasoning = "Trained classifier found mixed signals. Content may be partially AI-assisted or paraphrased. Manual review recommended."

            # Confidence from model probability (how far from 0.5)
            prob = v2_result["ai_probability"]
            final_confidence = round(abs(prob - 0.5) * 2, 2)  # 0 at p=0.5, 1 at p=0/1

            decision_basis = "v2_classifier"

            logger.info(
                f"V2 AI Detection complete. Score: {final_score:.2f}%. "
                f"Label: {label}. Prob: {prob:.4f}"
            )

            return {
                "ai_score": round(final_score, 2),
                "label": label,
                "confidence": final_confidence,
                "decision_basis": decision_basis,
                "reasoning": reasoning,
                "model_version": model_version,
                "v2_details": v2_result,
                "layer1_stats": stats,
                "layer2_semantics": semantics,
            }

        # --- Fallback: Legacy Two-Layer Fusion ---
        logger.info("V2 model unavailable. Using legacy two-layer fusion.")

        stat_score = stats["statistical_ai_likelihood"]
        sem_score = semantics["final_ai_likelihood"]

        # Layer 1 is given slightly more weight (60/40)
        final_score = (stat_score * 0.6) + (sem_score * 0.4)

        # Check agreement
        diff = abs(stat_score - sem_score)
        if diff > 40:
            decision_basis = "disagreement"
            label = "Mixed"  # Uncertain
            final_confidence = min(stats["confidence"], semantics["confidence"]) * 0.5
            reasoning = "Strong disagreement between math and meaning. Marked as Uncertain/Mixed."

            # Conservative Bias: Bring score closer to 50
            final_score = 50.0 + ((final_score - 50.0) * 0.5)
        else:
            decision_basis = "agreement"
            final_confidence = (stats["confidence"] + semantics["confidence"]) / 2.0

            if final_score > 70:
                label = "AI-generated"
                reasoning = "Both mathematical patterns and writing style strongly indicate AI generation."
            elif final_score < 30:
                label = "Original"
                reasoning = "Human-like unpredictability and natural phrasing detected."
            else:
                label = "Mixed"
                reasoning = "Content shows mixed signals. Requires manual review."

        # Pattern awareness override
        if (stats["pattern_type"] == "uniform"
                and semantics["signal_alignment"] == "high"
                and stat_score > 80):
            final_score = max(final_score, 85.0)
            label = "AI-generated"
            reasoning = "Highly uniform structure and robotic phrasing strongly suggest AI."

        logger.info(f"Legacy AI Detection complete. Final Score: {final_score:.2f}%. Label: {label}")

        return {
            "ai_score": round(final_score, 2),
            "label": label,
            "confidence": round(final_confidence, 2),
            "decision_basis": decision_basis,
            "reasoning": reasoning,
            "model_version": "v1_legacy_fusion",
            "layer1_stats": stats,
            "layer2_semantics": semantics,
        }

    except Exception as e:
        logger.error(f"AI detection failed: {e}")
        return {"ai_score": 0.0, "label": "Original", "reasoning": "Analysis failed."}
