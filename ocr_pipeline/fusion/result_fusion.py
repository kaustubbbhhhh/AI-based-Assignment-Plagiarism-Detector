"""
Result Fusion Module.
Reconciles outputs from CRAFT, TrOCR, and GOT-OCR 2.0.
Performs agreement verification, specialization weighting, conflict resolution,
and flags ambiguous regions for human review rather than hallucinating text.
"""

import logging
from typing import Dict, Any, Optional, List

from ..schemas.ocr_schema import (
    TextRegion,
    ModelOutput,
    ContentType,
    RoutingCategory,
)
from .confidence import compute_string_similarity, calibrate_confidence
from ..config.config_loader import get_fusion_config

logger = logging.getLogger(__name__)


class ResultFusion:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_fusion_config()
        self.agreement_threshold = self.config.get("agreement_similarity_threshold", 0.82)
        self.review_threshold = self.config.get("review_threshold", 0.70)
        self.weights = self.config.get("weights", {})

    def fuse_region(
        self,
        region_meta: Dict[str, Any],
        trocr_output: Optional[ModelOutput] = None,
        got_output: Optional[ModelOutput] = None,
        qwen_output: Optional[ModelOutput] = None,
        content_type: ContentType = ContentType.TEXT,
        routing_cat: RoutingCategory = RoutingCategory.NORMAL
    ) -> TextRegion:
        """
        Fuse multi-model outputs for a single region into a unified TextRegion.

        Args:
            region_meta: Detection metadata from CRAFT (id, bbox, polygon, confidence).
            trocr_output: Recognition result from TrOCR (if invoked).
            got_output: Recognition result from GOT-OCR (if invoked).
            qwen_output: Recognition result from Qwen2-VL (if invoked).
            content_type: Classified content type (TEXT, FORMULA, TABLE).
            routing_cat: Initial routing category.

        Returns:
            TextRegion schema populated with final fused text, confidence, and alternatives.
        """
        region_id = region_meta.get("id", "reg_unknown")
        bbox = region_meta.get("bbox", [0, 0, 0, 0])
        polygon = region_meta.get("polygon", [])
        page = region_meta.get("page", 1)

        alternatives: List[ModelOutput] = []
        if trocr_output is not None:
            alternatives.append(trocr_output)
        if got_output is not None:
            alternatives.append(got_output)
        if qwen_output is not None:
            alternatives.append(qwen_output)

        raw_trocr = trocr_output.model_dump() if trocr_output else None
        raw_got = got_output.model_dump() if got_output else None
        raw_craft = region_meta

        # Case 0: Qwen2-VL ran (high accuracy zero-shot multilingual handwriting)
        if qwen_output is not None:
            final_text = qwen_output.text
            final_conf = qwen_output.confidence
            selected_model = "qwen2_vl"
            needs_review = final_conf < self.review_threshold
            review_reason = "Low Qwen2-VL confidence" if needs_review else None

            return TextRegion(
                region_id=region_id,
                page=page,
                bbox=bbox,
                polygon=polygon,
                text=final_text,
                confidence=final_conf,
                model=selected_model,
                content_type=content_type,
                routing_cat=routing_cat,
                alternatives=alternatives,
                raw_craft=raw_craft,
                raw_trocr=raw_trocr,
                raw_got=raw_got,
                needs_review=needs_review,
                review_reason=review_reason,
                column_id=region_meta.get("column_id", 0)
            )

        # Case 1: Only TrOCR ran (Normal clean text)
        if trocr_output is not None and got_output is None:
            final_text = trocr_output.text
            final_conf = trocr_output.confidence
            selected_model = "trocr"
            needs_review = final_conf < self.review_threshold
            review_reason = "Low TrOCR confidence" if needs_review else None

            return TextRegion(
                region_id=region_id,
                page=page,
                bbox=bbox,
                polygon=polygon,
                text=final_text,
                confidence=final_conf,
                model=selected_model,
                content_type=content_type,
                routing_cat=routing_cat,
                alternatives=alternatives,
                raw_craft=raw_craft,
                raw_trocr=raw_trocr,
                raw_got=raw_got,
                needs_review=needs_review,
                review_reason=review_reason,
                column_id=region_meta.get("column_id", 0)
            )

        # Case 2: Only GOT-OCR ran (Direct complex table or equation)
        if got_output is not None and trocr_output is None:
            final_text = got_output.text
            final_conf = got_output.confidence
            selected_model = "got"
            needs_review = final_conf < self.review_threshold
            review_reason = "Low GOT confidence" if needs_review else None

            return TextRegion(
                region_id=region_id,
                page=page,
                bbox=bbox,
                polygon=polygon,
                text=final_text,
                confidence=final_conf,
                model=selected_model,
                content_type=content_type,
                routing_cat=routing_cat,
                alternatives=alternatives,
                raw_craft=raw_craft,
                raw_trocr=raw_trocr,
                raw_got=raw_got,
                needs_review=needs_review,
                review_reason=review_reason,
                column_id=region_meta.get("column_id", 0)
            )

        # Case 3: Both TrOCR and GOT ran (Uncertain region or Escalation)
        if trocr_output is not None and got_output is not None:
            t_text = trocr_output.text.strip()
            g_text = got_output.text.strip()
            t_conf = trocr_output.confidence
            g_conf = got_output.confidence

            similarity = compute_string_similarity(t_text, g_text)

            # Check if one or both models identified specialized structures (LaTeX math or Markdown table)
            has_latex = ("\\" in g_text or "^" in g_text or "_" in g_text or "{" in g_text)
            has_table = ("|" in g_text or "\n---" in g_text)

            needs_review = False
            review_reason = None

            if similarity >= self.agreement_threshold:
                # Agreement! High confidence consensus
                # Prefer TrOCR's exact character casing for text, or GOT if math/table
                if has_latex or has_table or content_type in [ContentType.FORMULA, ContentType.TABLE]:
                    final_text = g_text
                    selected_model = "got"
                else:
                    final_text = t_text if len(t_text) >= len(g_text) else g_text
                    selected_model = "trocr"

                # Agreement boost
                final_conf = calibrate_confidence(max(t_conf, g_conf), similarity, len(final_text), is_specialized=True)
                logger.info(f"[FUSION] Region {region_id}: Agreement ({similarity:.2f}) -> Conf: {final_conf:.2f}")

            else:
                # Disagreement detected
                logger.warning(
                    f"[FUSION] Disagreement on region {region_id} (sim={similarity:.2f}): "
                    f"TrOCR='{t_text[:30]}' vs GOT='{g_text[:30]}'"
                )

                # Evaluate specialization
                if content_type == ContentType.FORMULA or has_latex:
                    final_text = g_text
                    selected_model = "got"
                    final_conf = calibrate_confidence(g_conf, similarity, len(g_text), is_specialized=True)
                elif content_type == ContentType.TABLE or has_table:
                    final_text = g_text
                    selected_model = "got"
                    final_conf = calibrate_confidence(g_conf, similarity, len(g_text), is_specialized=True)
                else:
                    # General text disagreement: choose model with higher confidence
                    if t_conf >= g_conf:
                        final_text = t_text
                        selected_model = "trocr"
                        final_conf = calibrate_confidence(t_conf, similarity, len(t_text), is_specialized=False)
                    else:
                        final_text = g_text
                        selected_model = "got"
                        final_conf = calibrate_confidence(g_conf, similarity, len(g_text), is_specialized=False)

                # Flag for human verification if disagreement is substantial and confidence is borderline
                if similarity < 0.60 or final_conf < self.review_threshold:
                    needs_review = True
                    review_reason = f"OCR Disagreement (sim={similarity:.2f}): TrOCR='{t_text}' vs GOT='{g_text}'"

            return TextRegion(
                region_id=region_id,
                page=page,
                bbox=bbox,
                polygon=polygon,
                text=final_text,
                confidence=final_conf,
                model=selected_model,
                content_type=content_type,
                routing_cat=routing_cat,
                alternatives=alternatives,
                raw_craft=raw_craft,
                raw_trocr=raw_trocr,
                raw_got=raw_got,
                needs_review=needs_review,
                review_reason=review_reason,
                column_id=region_meta.get("column_id", 0)
            )

        # Fallback: neither model ran
        return TextRegion(
            region_id=region_id,
            page=page,
            bbox=bbox,
            polygon=polygon,
            text="",
            confidence=0.0,
            model="none",
            needs_review=True,
            review_reason="No recognition model produced output"
        )
