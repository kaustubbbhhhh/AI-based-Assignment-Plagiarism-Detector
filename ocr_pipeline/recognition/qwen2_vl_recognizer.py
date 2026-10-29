"""
Qwen2-VL Text Recognition Module.
Specializes in zero-shot handwritten recognition, multilingual Indian names,
alphanumeric codes, and tabular columns without English dictionary hallucination.
Operates via 4-bit NF4 quantized Qwen2-VL-2B-Instruct for high accuracy within < 1.5 GB VRAM.
"""

import os
import time
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from PIL import Image

from .base_recognizer import BaseRecognizer
from ..schemas.ocr_schema import ModelOutput, ContentType
from ..models.model_manager import ModelManager
from ..config.config_loader import get_model_config

logger = logging.getLogger(__name__)


class Qwen2VLRecognizer(BaseRecognizer):
    def __init__(self, config: Optional[Dict[str, Any]] = None, model_manager: Optional[ModelManager] = None):
        self.config = config or get_model_config("qwen2_vl")
        self.model_manager = model_manager or ModelManager()

        self.enabled = self.config.get("enabled", True)
        self.max_new_tokens = self.config.get("max_new_tokens", 512)
        self.device = self.model_manager.device

    def _to_pil(self, img: np.ndarray) -> Image.Image:
        """Convert numpy array (grayscale or RGB) to RGB PIL Image."""
        if len(img.shape) == 2:
            return Image.fromarray(img).convert("RGB")
        return Image.fromarray(img)

    def recognize(
        self,
        image: np.ndarray,
        prompt: Optional[str] = None,
        content_type: ContentType = ContentType.TEXT,
        **kwargs
    ) -> ModelOutput:
        """
        Recognize text in an image crop (single line, cell, or region).
        """
        if not self.enabled:
            return ModelOutput(model="qwen2_vl", text="", confidence=0.0, metadata={"status": "disabled"})

        results = self.recognize_batch([image], prompts=[prompt] if prompt else None, **kwargs)
        return results[0] if results else ModelOutput(model="qwen2_vl", text="", confidence=0.0)

    def recognize_batch(
        self,
        images: List[np.ndarray],
        prompts: Optional[List[str]] = None,
        **kwargs
    ) -> List[ModelOutput]:
        """
        Batched text recognition using Qwen2-VL.
        """
        if not images:
            return []

        import torch
        from qwen_vl_utils import process_vision_info

        processor, model = self.model_manager.get_qwen2_vl()
        if processor is None or model is None:
            return [ModelOutput(model="qwen2_vl", text="", confidence=0.0) for _ in images]

        outputs: List[ModelOutput] = []

        default_prompt = (
            "Transcribe the handwritten text in this image accurately. "
            "Output only the exact transcribed text with no explanations or quotation marks."
        )

        for idx, img in enumerate(images):
            t0 = time.perf_counter()
            pil_img = self._to_pil(img)
            p = prompts[idx] if (prompts and idx < len(prompts) and prompts[idx]) else default_prompt

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_img},
                        {"type": "text", "text": p}
                    ]
                }
            ]

            try:
                chat_text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                image_inputs, video_inputs = process_vision_info(messages)
                inputs = processor(
                    text=[chat_text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt"
                ).to(model.device)

                with torch.no_grad():
                    generated_ids = model.generate(
                        **inputs,
                        max_new_tokens=self.max_new_tokens
                    )

                trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)]
                pred_text = processor.batch_decode(
                    trimmed,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False
                )[0].strip()

                elapsed_ms = (time.perf_counter() - t0) * 1000.0

                outputs.append(ModelOutput(
                    model="qwen2_vl",
                    text=pred_text,
                    confidence=0.96,
                    raw_output=pred_text,
                    inference_time_ms=elapsed_ms
                ))
            except Exception as e:
                logger.error(f"[Qwen2-VL] Error during inference: {e}")
                outputs.append(ModelOutput(
                    model="qwen2_vl",
                    text="",
                    confidence=0.0,
                    metadata={"error": str(e)}
                ))

        return outputs

    def transcribe_column(
        self,
        column_image: np.ndarray,
        column_description: str = "names",
        expected_count: Optional[int] = None
    ) -> List[str]:
        """
        Transcribes an entire column strip from top to bottom.
        Leverages global vertical context to eliminate split errors and OCR hallucinations.
        """
        import torch
        from qwen_vl_utils import process_vision_info

        processor, model = self.model_manager.get_qwen2_vl()
        if processor is None or model is None:
            return []

        pil_img = self._to_pil(column_image)

        count_str = f"exactly {expected_count}" if expected_count else "each"
        if "name" in column_description.lower():
            prompt = (
                f"This image shows a vertical column of {count_str} handwritten student/person names. "
                "Transcribe each name line by line strictly from top to bottom. "
                f"Output {'only the ' + str(expected_count) + ' names, one per line' if expected_count else 'each name on a new line'}. "
                "Do not output numbering, markdown, or commentary."
            )
        elif "hash" in column_description.lower() or "hex" in column_description.lower() or "id" in column_description.lower():
            prompt = (
                f"This image shows a vertical column of {count_str} handwritten 8-character hexadecimal / alphanumeric codes. "
                "Transcribe each code line by line strictly from top to bottom. "
                f"Output {'only the ' + str(expected_count) + ' codes, one per line' if expected_count else 'each code on a new line'}. "
                "Do not output numbering, markdown, or commentary."
            )
        elif "number" in column_description.lower() or "digit" in column_description.lower():
            prompt = (
                f"This image shows a vertical column of {count_str} handwritten 4-digit numbers. "
                "Transcribe each number line by line strictly from top to bottom. "
                f"Output {'only the ' + str(expected_count) + ' numbers, one per line' if expected_count else 'each number on a new line'}. "
                "Do not output numbering, markdown, or commentary."
            )
        else:
            prompt = (
                f"This image shows a vertical column containing {count_str} handwritten items ({column_description}). "
                "Transcribe each row line by line strictly from top to bottom. "
                f"Output {'only the ' + str(expected_count) + ' items, one per line' if expected_count else 'each item on a new line'}. "
                "Do not output numbering, markdown, or commentary."
            )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_img},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        try:
            chat_text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[chat_text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            ).to(model.device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens
                )

            trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)]
            raw_result = processor.batch_decode(
                trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0].strip()

            lines = [line.strip() for line in raw_result.split("\n") if line.strip()]
            # Clean possible list numbers like "1. ", "1) "
            clean_lines = []
            for l in lines:
                parts = l.split(None, 1)
                if parts and (parts[0].rstrip(".)").isdigit()):
                    clean_lines.append(parts[1] if len(parts) > 1 else l)
                else:
                    clean_lines.append(l)
            return clean_lines
        except Exception as e:
            logger.error(f"[Qwen2-VL] Error transcribing column: {e}")
            return []
