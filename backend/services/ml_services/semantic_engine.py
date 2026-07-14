"""
Layer 2: Semantic Analysis Engine (Context & Style Analysis)
Evaluates writing style, personal voice, and structural coherence without relying on pure statistics.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Heuristic patterns expanded for modern LLMs
AI_TRANSITIONS = [
    r"\bfurthermore\b", r"\bmoreover\b", r"\bin conclusion\b", r"\bconsequently\b",
    r"\badditionally\b", r"\bhowever\b", r"\btherefore\b", r"\bthus\b",
    r"\bto summarize\b", r"\bultimately\b", r"\bfirstly\b", r"\bsecondly\b",
    r"\bdelving into\b", r"\bit is important to note\b", r"\bcrucially\b",
    r"\bin essence\b", r"\bat its core\b", r"\ball in all\b", r"\btaking everything into consideration\b",
    r"\bit is worth noting that\b", r"\bone could argue\b", r"\bto begin with\b",
    r"\bin this essay\b", r"\bwe will explore\b", r"\bthe landscape of\b",
    r"\bthe realm of\b", r"\bnavigating the complexities\b", r"\bmultifaceted\b",
    r"\ba critical aspect of\b", r"\bprior to\b", r"\bsubsequently\b"
]

PERSONAL_VOICE = [
    r"\bi\b", r"\bmy\b", r"\bme\b", r"\bmine\b", r"\bwe\b", r"\bour\b", r"\bus\b",
    r"\bexperience\b", r"\bfelt\b", r"\bthink\b", r"\bbelieve\b", r"\bnotice\b",
    r"\bremember\b", r"\bguess\b", r"\bmaybe\b", r"\bprobably\b", r"\bhonestly\b",
    r"\bhopefully\b", r"\bpersonally\b", r"\bactually\b", r"\bliterally\b", r"\bkind of\b", r"\bbasically\b"
]

GENERIC_PHRASES = [
    r"\bcan be defined as\b", r"\bplays a crucial role\b", r"\bis a multifaceted\b",
    r"\bhas garnered significant attention\b", r"\blandscape of\b", r"\brealm of\b",
    r"\blet's dive in\b", r"\bin today's fast-paced\b", r"\ba testament to\b",
    r"\bever-evolving\b", r"\brapidly changing\b", r"\btechnological advancements\b",
    r"\bsignificant impact\b", r"\bprofound effect\b", r"\bvital component\b",
    r"\bnot merely\b", r"\bbut also\b", r"\bstands as a\b", r"\bshed light on\b",
    r"\bdelve deeper\b", r"\buncover\b", r"\btransformative\b", r"\bseamless\b"
]

def analyze_semantics(text: str) -> dict:
    """
    Computes semantic signals of AI generation from text content.
    Returns scores for generic phrasing, lack of personal voice, etc.
    """
    if not text or len(text.strip()) < 50:
        return _fallback_semantics()

    try:
        lower_text = text.lower()
        words = re.findall(r'\w+', lower_text)
        word_count = len(words)
        if word_count == 0:
            return _fallback_semantics()

        # 1. Generic Phrasing
        generic_count = sum(len(re.findall(p, lower_text)) for p in GENERIC_PHRASES)
        generic_phrasing = min(1.0, (generic_count * 10) / word_count)

        # 2. Lack of Personal Voice
        personal_count = sum(len(re.findall(p, lower_text)) for p in PERSONAL_VOICE)
        # High personal count -> low lack of personal voice (score closer to 0)
        lack_of_personal_voice = max(0.0, 1.0 - ((personal_count * 5) / word_count))

        # 3. Over-Structured Coherence
        transition_count = sum(len(re.findall(p, lower_text)) for p in AI_TRANSITIONS)
        over_structured_coherence = min(1.0, (transition_count * 15) / word_count)

        # 4. Repetitiveness (Unique words ratio)
        unique_words = len(set(words))
        lexical_diversity = unique_words / word_count
        # AI often has lower lexical diversity for long essays, but can be highly diverse.
        # We use a simple metric here.
        repetitiveness = max(0.0, 1.0 - lexical_diversity)

        # Semantic Predictability & Conceptual Shallowness (Approximated)
        semantic_predictability = (generic_phrasing + over_structured_coherence) / 2.0
        conceptual_shallowness = generic_phrasing

        # Final AI Likelihood based on semantics
        # Increased if high generic, high structure, low personal voice
        final_ai_likelihood = (generic_phrasing * 0.3) + (lack_of_personal_voice * 0.3) + (over_structured_coherence * 0.4)
        
        # Confidence
        # High confidence if signals strongly agree
        variance = max([generic_phrasing, lack_of_personal_voice, over_structured_coherence]) - min([generic_phrasing, lack_of_personal_voice, over_structured_coherence])
        confidence = max(0.1, 1.0 - variance)

        signal_alignment = "high" if variance < 0.3 else "medium" if variance < 0.6 else "low"
        risk_level = "high" if final_ai_likelihood > 0.7 else "moderate" if final_ai_likelihood > 0.4 else "low"
        
        reasoning = f"Semantic alignment is {signal_alignment}. "
        if lack_of_personal_voice > 0.7: reasoning += "Lacks personal voice. "
        if over_structured_coherence > 0.7: reasoning += "Highly structured transitions detected. "

        return {
            "generic_phrasing": round(generic_phrasing, 2),
            "lack_of_personal_voice": round(lack_of_personal_voice, 2),
            "over_structured_coherence": round(over_structured_coherence, 2),
            "repetitiveness": round(repetitiveness, 2),
            "semantic_predictability": round(semantic_predictability, 2),
            "conceptual_shallowness": round(conceptual_shallowness, 2),
            "final_ai_likelihood": round(final_ai_likelihood * 100, 2),
            "confidence": round(confidence, 2),
            "signal_alignment": signal_alignment,
            "risk_level": risk_level,
            "reasoning": reasoning.strip()
        }

    except Exception as e:
        logger.error(f"Semantic analysis failed: {e}")
        return _fallback_semantics()


def _fallback_semantics():
    return {
        "generic_phrasing": 0.5,
        "lack_of_personal_voice": 0.5,
        "over_structured_coherence": 0.5,
        "repetitiveness": 0.5,
        "semantic_predictability": 0.5,
        "conceptual_shallowness": 0.5,
        "final_ai_likelihood": 50.0,
        "confidence": 0.1,
        "signal_alignment": "low",
        "risk_level": "moderate",
        "reasoning": "Fallback used due to insufficient text or processing failure."
    }
