"""
Text Detection Module.
Locates text regions, bounding boxes, and polygons using high-performance OpenCV morphological analysis.
Responsible ONLY for spatial detection, never for recognition.
"""

import os
import cv2
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from ..schemas.ocr_schema import DetectionRegion
from ..config.config_loader import get_model_config

logger = logging.getLogger(__name__)


class CRAFTDetector:
    """
    Document Text Detector.
    Identifies word and text-line bounding boxes and polygons on document pages.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None, device: str = "auto"):
        self.config = config or get_model_config("craft")

        # Determine compute device
        if device == "auto":
            try:
                import torch
                self.use_gpu = torch.cuda.is_available()
            except ImportError:
                self.use_gpu = False
        else:
            self.use_gpu = (device == "cuda")

        self.text_threshold = self.config.get("text_threshold", 0.7)
        self.link_threshold = self.config.get("link_threshold", 0.4)
        self.low_text = self.config.get("low_text", 0.4)
        self.min_size = self.config.get("min_size", 15)
        self.slope_ths = self.config.get("slope_ths", 0.1)
        self.ycenter_ths = self.config.get("ycenter_ths", 0.5)
        self.height_ths = self.config.get("height_ths", 0.5)
        self.width_ths = self.config.get("width_ths", 0.5)
        self.add_margin = self.config.get("add_margin", 0.1)

        self._initialized = True
        logger.info(f"[TextDetector] OpenCV document text detector initialized (GPU: {self.use_gpu}).")

    def _init_model(self):
        """No external weights or runtime model downloads required."""
        pass

    def detect(self, image: np.ndarray, page_num: int = 1) -> Dict[str, Any]:
        """
        Detect text regions within a document page image.

        Args:
            image: RGB, BGR, or grayscale image array.
            page_num: Page index for region ID generation.

        Returns:
            Dictionary matching the required specification:
            {
                "regions": [
                    {
                        "id": "p1_reg_0001",
                        "page": 1,
                        "bbox": [x1, y1, x2, y2],
                        "polygon": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                        "confidence": 0.95,
                        "area": 2500,
                        "aspect_ratio": 3.5
                    }
                ]
            }
        """
        if image is None or image.size == 0:
            return {"regions": []}

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

        # Enhance contrast and isolate stroke edges
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        grad = cv2.morphologyEx(enhanced, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological horizontal connection to merge character strokes into word/line segments
        kernel_w = max(12, int(w * 0.012))
        kernel_conn = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_w, 3))
        connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_conn)
        contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        raw_boxes = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Filter out noise and page boundary frames
            if bw < self.min_size or bh < 8:
                continue
            if bw > 0.98 * w and bh > 0.95 * h:
                continue
            raw_boxes.append((x, y, bw, bh))

        # Sort top-to-bottom, left-to-right (natural reading order)
        raw_boxes.sort(key=lambda b: (b[1], b[0]))

        # Non-maximum suppression / overlap deduplication
        deduped = []
        for box in raw_boxes:
            x, y, bw, bh = box
            overlap = False
            for ex, ey, ebw, ebh in deduped:
                ix1 = max(x, ex)
                iy1 = max(y, ey)
                ix2 = min(x + bw, ex + ebw)
                iy2 = min(y + bh, ey + ebh)
                if ix2 > ix1 and iy2 > iy1:
                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                    min_area = min(bw * bh, ebw * ebh)
                    if inter_area / float(min_area + 1e-5) > 0.70:
                        overlap = True
                        break
            if not overlap:
                deduped.append(box)

        regions: List[Dict[str, Any]] = []
        region_counter = 1

        for x, y, bw, bh in deduped:
            # Apply configured margin
            mx = int(bw * self.add_margin)
            my = int(bh * self.add_margin)
            x1 = max(0, x - mx)
            y1 = max(0, y - my)
            x2 = min(w, x + bw + mx)
            y2 = min(h, y + bh + my)

            box_w = x2 - x1
            box_h = y2 - y1

            aspect = box_w / float(max(1, box_h))
            confidence = min(0.99, max(0.85, 0.95 - 0.05 * (1.0 if aspect < 0.5 else 0.0)))

            polygon = [
                [x1, y1],
                [x2, y1],
                [x2, y2],
                [x1, y2]
            ]

            region_id = f"p{page_num}_reg_{region_counter:04d}"
            regions.append({
                "id": region_id,
                "page": page_num,
                "bbox": [x1, y1, x2, y2],
                "polygon": polygon,
                "confidence": round(float(confidence), 3),
                "area": box_w * box_h,
                "aspect_ratio": round(float(aspect), 2)
            })
            region_counter += 1

        logger.info(f"[TextDetector] Detected {len(regions)} valid text regions on page {page_num}.")
        return {"regions": regions}


# Backward compatibility alias
TextDetector = CRAFTDetector
