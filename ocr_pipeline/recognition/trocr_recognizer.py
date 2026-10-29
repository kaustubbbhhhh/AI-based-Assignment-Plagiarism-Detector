"""
TrOCR Text Recognition Module.
Specializes in clean printed lines, handwriting lines, and individual text segments.
"""

import time
import math
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from PIL import Image

from .base_recognizer import BaseRecognizer
from ..schemas.ocr_schema import ModelOutput
from ..models.model_manager import ModelManager
from ..config.config_loader import get_model_config

logger = logging.getLogger(__name__)


class TrOCRRecognizer(BaseRecognizer):
    def __init__(self, config: Optional[Dict[str, Any]] = None, model_manager: Optional[ModelManager] = None):
        self.config = config or get_model_config("trocr")
        self.model_manager = model_manager or ModelManager()

        self.batch_size = self.config.get("batch_size", 8)
        self.max_new_tokens = self.config.get("max_new_tokens", 128)
        self.num_beams = self.config.get("num_beams", 4)
        self.early_stopping = self.config.get("early_stopping", True)

    def _prepare_pil(self, img: np.ndarray) -> Image.Image:
        """Convert numpy array (grayscale or RGB) to RGB PIL Image."""
        if len(img.shape) == 2:
            return Image.fromarray(img).convert("RGB")
        return Image.fromarray(img)

    def recognize(self, image: np.ndarray, **kwargs) -> ModelOutput:
        """Recognize text in a single cropped line."""
        results = self.recognize_batch([image], **kwargs)
        return results[0] if results else ModelOutput(model="trocr", text="", confidence=0.0)

    def recognize_batch(self, images: List[np.ndarray], **kwargs) -> List[ModelOutput]:
        """
        Batched text recognition using TrOCR.
        Provides significant speedup over sequential inference.
        """
        if not images:
            return []

        import torch

        processor, model = self.model_manager.get_trocr()
        device = self.model_manager.device
        outputs: List[ModelOutput] = []

        # Process in chunks of self.batch_size
        for i in range(0, len(images), self.batch_size):
            batch_imgs = images[i : i + self.batch_size]
            t0 = time.perf_counter()

            pil_batch = [self._prepare_pil(img) for img in batch_imgs]

            try:
                inputs = processor(images=pil_batch, return_tensors="pt")
                pixel_values = inputs.pixel_values.to(device)

                if self.model_manager.device == "cuda" and next(model.parameters()).dtype == torch.float16:
                    pixel_values = pixel_values.half()

                if hasattr(model, "generation_config") and model.generation_config is not None:
                    model.generation_config.max_length = None

                beams = kwargs.get("num_beams", self.num_beams)
                with torch.inference_mode():
                    generated = model.generate(
                        pixel_values,
                        max_new_tokens=self.max_new_tokens,
                        num_beams=beams,
                        early_stopping=self.early_stopping,
                        return_dict_in_generate=True,
                        output_scores=True,
                    )

                decoded_texts = processor.batch_decode(generated.sequences, skip_special_tokens=True)
                latency = (time.perf_counter() - t0) * 1000.0
                per_item_latency = latency / len(batch_imgs)

                # Compute confidence per sequence
                for j, text in enumerate(decoded_texts):
                    clean_text = text.strip()
                    conf = 0.85  # default baseline

                    if hasattr(generated, "sequences_scores") and generated.sequences_scores is not None:
                        log_prob = float(generated.sequences_scores[j].item())
                        # Length penalty normalization
                        seq_len = max(1, len(clean_text.split()))
                        norm_log_prob = log_prob / math.pow(seq_len, 0.7)
                        conf = min(0.99, max(0.20, math.exp(norm_log_prob)))

                    # Sanity check: empty strings have 0 confidence
                    if not clean_text:
                        conf = 0.0

                    outputs.append(ModelOutput(
                        model="trocr",
                        text=clean_text,
                        confidence=round(conf, 3),
                        latency_ms=round(per_item_latency, 2)
                    ))

            except Exception as e:
                logger.error(f"[TrOCR] Error during batch recognition: {e}")
                for _ in batch_imgs:
                    outputs.append(ModelOutput(
                        model="trocr",
                        text="",
                        confidence=0.0,
                        metadata={"error": str(e)}
                    ))

        return outputs
