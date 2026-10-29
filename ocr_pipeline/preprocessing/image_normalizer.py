"""
Image Normalizer.
Provides coordinate-aware cropping with margin expansion, aspect ratio normalization,
and image formatting for downstream neural recognition models.
"""

import cv2
import numpy as np
from typing import List, Tuple, Union


class ImageNormalizer:
    @staticmethod
    def crop_region(
        img: np.ndarray,
        bbox: List[int],
        margin_ratio: float = 0.10
    ) -> np.ndarray:
        """
        Crop a subregion from an image using [x1, y1, x2, y2] coordinates,
        adding a margin percentage while safely clamping to image boundaries.

        Args:
            img: Source image (H, W) or (H, W, 3).
            bbox: [x1, y1, x2, y2] bounding box coordinates.
            margin_ratio: Percentage of width/height to add as margin padding.

        Returns:
            Cropped numpy array.
        """
        h, w = img.shape[:2]
        x1, y1, x2, y2 = bbox

        box_w = max(1, x2 - x1)
        box_h = max(1, y2 - y1)

        pad_x = int(box_w * margin_ratio)
        pad_y = int(box_h * margin_ratio)

        clamped_x1 = max(0, x1 - pad_x)
        clamped_y1 = max(0, y1 - pad_y)
        clamped_x2 = min(w, x2 + pad_x)
        clamped_y2 = min(h, y2 + pad_y)

        # Fallback if inverted or empty box
        if clamped_x2 <= clamped_x1 or clamped_y2 <= clamped_y1:
            return img[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

        return img[clamped_y1:clamped_y2, clamped_x1:clamped_x2].copy()

    @staticmethod
    def resize_with_aspect_ratio(
        img: np.ndarray,
        target_height: int = 384,
        max_width: int = 1536
    ) -> np.ndarray:
        """
        Resize image to a fixed height while preserving aspect ratio,
        capping maximum width to prevent memory explosion.
        """
        h, w = img.shape[:2]
        if h == 0 or w == 0:
            return img

        aspect = w / float(h)
        new_w = min(max_width, max(32, int(target_height * aspect)))
        return cv2.resize(img, (new_w, target_height), interpolation=cv2.INTER_LANCZOS4)

    @staticmethod
    def ensure_rgb(img: np.ndarray) -> np.ndarray:
        """Convert grayscale or BGRA to standard 3-channel RGB."""
        if len(img.shape) == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        elif len(img.shape) == 3 and img.shape[2] == 4:
            return cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        elif len(img.shape) == 3 and img.shape[2] == 3:
            return img
        return img

    @staticmethod
    def ensure_grayscale(img: np.ndarray) -> np.ndarray:
        """Convert RGB to single-channel Grayscale."""
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return img
