"""
Image Preprocessor.
Applies perspective flattening, deskewing, shadow removal, adaptive thresholding,
and bilateral denoising to optimize document images for OCR.
"""

import cv2
import math
import logging
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.deskew_enabled = cfg.get("deskew_enabled", True)
        self.shadow_removal_enabled = cfg.get("shadow_removal_enabled", True)
        self.adaptive_threshold_enabled = cfg.get("adaptive_threshold_enabled", True)
        self.denoise_enabled = cfg.get("denoise_enabled", True)
        self.denoise_diameter = cfg.get("denoise_diameter", 5)
        self.denoise_sigma_color = cfg.get("denoise_sigma_color", 50)
        self.denoise_sigma_space = cfg.get("denoise_sigma_space", 50)
        self.ruled_line_suppression_enabled = cfg.get("ruled_line_suppression_enabled", True)
        self.ruled_line_kernel_ratio = cfg.get("ruled_line_kernel_ratio", 0.04)

    def deskew(self, img: np.ndarray) -> np.ndarray:
        """
        Auto-correct rotation/skew using Hough Line Transform.
        Detects dominant line angles and rotates to straighten.
        """
        if not self.deskew_enabled:
            return img

        # Determine grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if len(img.shape) == 3 else img.copy()

        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        min_line_len = max(gray.shape[1] // 5, 40)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=80,
            minLineLength=min_line_len, maxLineGap=15
        )

        if lines is None or len(lines) == 0:
            return img

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 == 0:
                continue
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            # Text lines generally lie within +/- 30 degrees of horizontal
            if abs(angle) < 30:
                angles.append(angle)

        if not angles:
            return img

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.5:
            return img

        logger.info(f"Deskewing image by {median_angle:.2f} degrees")
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        deskewed = cv2.warpAffine(
            img, rot_mat, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return deskewed

    def remove_shadows(self, gray: np.ndarray) -> np.ndarray:
        """
        Remove uneven lighting and shadows using morphological opening.
        """
        if not self.shadow_removal_enabled:
            return gray

        dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
        bg = cv2.medianBlur(dilated, 21)
        diff = 255 - cv2.absdiff(gray, bg)
        normalized = cv2.normalize(
            diff, None, alpha=0, beta=255,
            norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1
        )
        return normalized

    def adaptive_threshold(self, gray: np.ndarray) -> np.ndarray:
        """
        Enhance faint pencil or pen ink using Gaussian adaptive thresholding.
        """
        if not self.adaptive_threshold_enabled:
            return gray

        return cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=10
        )

    def denoise(self, img: np.ndarray) -> np.ndarray:
        """
        Bilateral filtering: smooths background noise while preserving character stroke edges.
        """
        if not self.denoise_enabled:
            return img

        return cv2.bilateralFilter(
            img,
            self.denoise_diameter,
            self.denoise_sigma_color,
            self.denoise_sigma_space
        )

    def suppress_ruled_lines(self, gray: np.ndarray) -> np.ndarray:
        """
        Suppresses notebook horizontal ruled lines using morphological operations.
        Preserves characters/text strokes while erasing continuous thin horizontal lines.
        """
        if not self.ruled_line_suppression_enabled:
            return gray

        h, w = gray.shape[:2]
        bin_inv = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 10
        )

        kernel_len = max(int(w * self.ruled_line_kernel_ratio), 30)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        line_mask = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
        line_mask = cv2.dilate(line_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2)), iterations=1)

        # Preserve vertical strokes (characters)
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 8))
        vertical_strokes = cv2.morphologyEx(bin_inv, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
        safe_line_mask = cv2.subtract(line_mask, cv2.dilate(vertical_strokes, np.ones((3, 3), np.uint8)))

        if cv2.countNonZero(safe_line_mask) > 100:
            logger.info(f"[PREPROCESS] Suppressing {cv2.countNonZero(safe_line_mask)} ruled line pixels.")
            cleaned = cv2.inpaint(gray, safe_line_mask, inpaintRadius=2, flags=cv2.INPAINT_TELEA)
            return cleaned

        return gray

    def preprocess(self, img: np.ndarray, return_grayscale: bool = False) -> np.ndarray:
        """
        Full document preprocessing pipeline.
        Deskews, normalizes illumination with shadow removal, suppresses notebook lines,
        and enhances ink contrast via CLAHE.
        """
        # 1. Deskew
        corrected = self.deskew(img)

        # 2. Convert to grayscale for illumination & contrast processing
        if len(corrected.shape) == 3:
            gray = cv2.cvtColor(corrected, cv2.COLOR_RGB2GRAY)
        else:
            gray = corrected.copy()

        # 3. Shadow removal (normalize lighting gradient)
        shadow_free = self.remove_shadows(gray)

        # 4. Notebook Ruled-Line Suppression
        line_suppressed = self.suppress_ruled_lines(shadow_free)

        # 5. Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(line_suppressed)

        # 6. Light bilateral denoise to smooth paper grain while preserving stroke edges
        denoised = self.denoise(enhanced)

        if return_grayscale:
            return denoised

        # Return RGB
        return cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
