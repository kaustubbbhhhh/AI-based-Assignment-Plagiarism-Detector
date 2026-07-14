"""
Fusion Engine (Two-Layer AI Detection Architecture)
Combines Statistical (Layer 1) and Semantic (Layer 2) engines.
"""

import logging
from .ml_services.statistical_engine import analyze_statistics
from .ml_services.semantic_engine import analyze_semantics

logger = logging.getLogger(__name__)

def analyze_ai_content(text: str) -> dict:
    """
    Run two-layer analysis on the given text and fuse results.
    Returns final decision JSON.
    """
    if not text or len(text.strip()) < 50:
        return {"ai_score": 0.0, "label": "Original", "reasoning": "Text too short."}

    try:
        # 1. Run Layer 1 (Statistical)
        stats = analyze_statistics(text)
        
        # 2. Run Layer 2 (Semantic)
        semantics = analyze_semantics(text)

        # 3. Fusion Logic
        stat_score = stats["statistical_ai_likelihood"]
        sem_score = semantics["final_ai_likelihood"]
        
        # Layer 1 is given slightly more weight (60/40)
        final_score = (stat_score * 0.6) + (sem_score * 0.4)
        
        # Check agreement
        diff = abs(stat_score - sem_score)
        if diff > 40:
            decision_basis = "disagreement"
            label = "Mixed" # Uncertain
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
        if stats["pattern_type"] == "uniform" and semantics["signal_alignment"] == "high" and stat_score > 80:
            final_score = max(final_score, 85.0)
            label = "AI-generated"
            reasoning = "Highly uniform structure and robotic phrasing strongly suggest AI."

        logger.info(f"Two-Layer AI Detection complete. Final Score: {final_score:.2f}%. Label: {label}")

        return {
            "ai_score": round(final_score, 2),
            "label": label,
            "confidence": round(final_confidence, 2),
            "decision_basis": decision_basis,
            "reasoning": reasoning,
            "layer1_stats": stats,
            "layer2_semantics": semantics
        }

    except Exception as e:
        logger.error(f"Two-Layer AI detection failed: {e}")
        return {"ai_score": 0.0, "label": "Original", "reasoning": "Analysis failed."}
