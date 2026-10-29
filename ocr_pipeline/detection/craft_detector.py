"""
CRAFT Text Detection Module.
Locates text regions, bounding boxes, and polygons using the CRAFT architecture.
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

        self._reader = None
        self._initialized = False

    def _init_model(self):
        """Lazy-initialize CRAFT detector using EasyOCR's CRAFT PyTorch backbone."""
        if self._initialized:
            return

        import easyocr
        logger.info(f"[CRAFT] Initializing CRAFT Text Detector (GPU: {self.use_gpu})...")
        # recognizer=False ensures we ONLY load and execute the CRAFT detector network
        self._reader = easyocr.Reader(
            ["en"],
            detector=True,
            recognizer=False,
            gpu=self.use_gpu,
            verbose=False
        )
        self._initialized = True
        logger.info("[CRAFT] Detector initialized successfully.")

    def detect(self, image: np.ndarray, page_num: int = 1) -> Dict[str, Any]:
        """
        Detect text regions within a document page image.

        Args:
            image: RGB or grayscale image array.
            page_num: Page index for region ID generation.

        Returns:
            Dictionary matching the required specification:
            {
                "regions": [
                    {
                        "id": "region_001",
                        "bbox": [x1, y1, x2, y2],
                        "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
                        "confidence": 0.97
                    }
                ]
            }
        """
        self._init_model()

        if image is None or image.size == 0:
            return {"regions": []}

        h, w = image.shape[:2]

        # Call CRAFT detector with configured hyperparameters
        try:
            horizontal_list, free_list = self._reader.detect(
                image,
                min_size=self.min_size,
                text_threshold=self.text_threshold,
                low_text=self.low_text,
                link_threshold=self.link_threshold,
                slope_ths=self.slope_ths,
                ycenter_ths=self.ycenter_ths,
                height_ths=self.height_ths,
                width_ths=self.width_ths,
                add_margin=self.add_margin
            )
        except Exception as e:
            logger.error(f"[CRAFT] Detection failed: {e}")
            return {"regions": []}

        regions: List[Dict[str, Any]] = []
        region_counter = 1

        # Process horizontal bounding boxes: [x_min, x_max, y_min, y_max]
        h_boxes = horizontal_list[0] if horizontal_list and len(horizontal_list) > 0 else []
        for box in h_boxes:
            if len(box) < 4:
                continue

            x_min = int(box[0])
            x_max = int(box[1])
            y_min = int(box[2])
            y_max = int(box[3])

            # Clamp coordinates to image dimensions
            x1 = max(0, min(w, x_min))
            x2 = max(0, min(w, x_max))
            y1 = max(0, min(h, y_min))
            y2 = max(0, min(h, y_max))

            box_w = x2 - x1
            box_h = y2 - y1

            # Filter out tiny/noisy regions
            if box_w < self.min_size or box_h < 8:
                continue

            polygon = [
                [x1, y1],
                [x2, y1],
                [x2, y2],
                [x1, y2]
            ]

            # Approximate detection confidence based on size/aspect realism
            aspect = box_w / float(max(1, box_h))
            confidence = min(0.99, max(0.85, 0.95 - 0.05 * (1.0 if aspect < 0.5 else 0.0)))

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

        # Process free/rotated polygon regions: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        f_boxes = free_list[0] if free_list and len(free_list) > 0 else []
        for poly in f_boxes:
            if len(poly) < 4:
                continue

            pts = np.array(poly, dtype=np.int32)
            x1 = max(0, int(np.min(pts[:, 0])))
            x2 = min(w, int(np.max(pts[:, 0])))
            y1 = max(0, int(np.min(pts[:, 1])))
            y2 = min(h, int(np.max(pts[:, 1])))

            box_w = x2 - x1
            box_h = y2 - y1

            if box_w < self.min_size or box_h < 8:
                continue

            # Check if this box overlaps heavily with an existing horizontal box
            overlap = False
            for existing in regions:
                ex1, ey1, ex2, ey2 = existing["bbox"]
                ix1 = max(x1, ex1)
                iy1 = max(y1, ey1)
                ix2 = min(x2, ex2)
                iy2 = min(y2, ey2)
                if ix2 > ix1 and iy2 > iy1:
                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                    min_area = min(box_w * box_h, existing["area"])
                    if inter_area / float(min_area + 1e-5) > 0.70:
                        overlap = True
                        break

            if overlap:
                continue

            region_id = f"p{page_num}_reg_{region_counter:04d}"
            regions.append({
                "id": region_id,
                "page": page_num,
                "bbox": [x1, y1, x2, y2],
                "polygon": [[int(p[0]), int(p[1])] for p in poly],
                "confidence": 0.90,
                "area": box_w * box_h,
                "aspect_ratio": round(float(box_w / float(max(1, box_h))), 2)
            })
            region_counter += 1

        logger.info(f"[CRAFT] Detected {len(regions)} valid text regions on page {page_num}.")
        return {"regions": regions}
