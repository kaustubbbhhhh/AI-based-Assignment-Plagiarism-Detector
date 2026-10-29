"""
Feature Extractor for Region Routing.
Analyzes cropped image patches to extract spatial, morphological,
and visual complexity features used by the Intelligent Router.
"""

import cv2
import numpy as np
from typing import Dict, Any, Tuple


class RegionFeatureExtractor:
    @staticmethod
    def extract_features(
        crop: np.ndarray,
        bbox: list,
        page_shape: Tuple[int, int]
    ) -> Dict[str, Any]:
        """
        Extract spatial and visual features from a cropped region.

        Args:
            crop: BGR or grayscale cropped patch.
            bbox: [x1, y1, x2, y2]
            page_shape: (page_h, page_w)

        Returns:
            Dictionary of computed features.
        """
        if crop is None or crop.size == 0:
            return {
                "aspect_ratio": 1.0,
                "relative_area": 0.0,
                "stroke_density": 0.0,
                "laplacian_var": 0.0,
                "horizontal_lines": 0,
                "vertical_lines": 0,
                "is_table_like": False,
                "is_math_like": False,
            }

        h, w = crop.shape[:2]
        page_h, page_w = page_shape
        page_area = max(1, page_h * page_w)
        crop_area = h * w

        aspect_ratio = float(w / float(max(1, h)))
        relative_area = float(crop_area / float(page_area))

        # Convert to grayscale
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop.copy()

        # 1. Stroke density via Otsu binarization
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        stroke_density = float(np.count_nonzero(binary) / float(max(1, crop_area)))

        # 2. Visual complexity / high-frequency texture (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = float(laplacian.var())

        # 3. Detect horizontal grid lines (tables or long fraction bars)
        min_h_line = max(w // 4, 25)
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_h_line, 1))
        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
        h_contours, _ = cv2.findContours(h_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        num_h_lines = len(h_contours)

        # 4. Detect vertical grid lines (tables)
        min_v_line = max(h // 4, 20)
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_v_line))
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
        v_contours, _ = cv2.findContours(v_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        num_v_lines = len(v_contours)

        # Table-like structure check (grid lines in both directions or multiple horizontal rows)
        is_table_like = (num_h_lines >= 2 and num_v_lines >= 1) or (num_h_lines >= 3)

        # Mathematical expression heuristic:
        # - Has a horizontal division bar or high symbol variance
        # - Aspect ratio is compact or moderate (not an ultra-wide single line paragraph)
        # - Presence of isolated characters or multi-level symbols
        has_fraction_line = (num_h_lines >= 1 and num_v_lines == 0 and 0.6 <= aspect_ratio <= 6.0)
        is_math_like = has_fraction_line or (laplacian_var > 300.0 and 0.7 <= aspect_ratio <= 4.0 and stroke_density > 0.12)

        return {
            "aspect_ratio": round(aspect_ratio, 2),
            "relative_area": round(relative_area, 4),
            "stroke_density": round(stroke_density, 3),
            "laplacian_var": round(laplacian_var, 1),
            "horizontal_lines": num_h_lines,
            "vertical_lines": num_v_lines,
            "is_table_like": is_table_like,
            "is_math_like": is_math_like,
            "width": w,
            "height": h
        }
