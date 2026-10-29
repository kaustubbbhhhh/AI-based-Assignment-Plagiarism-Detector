"""
Base OCR Recognizer Interface.
Defines common contract for text recognition models.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from ..schemas.ocr_schema import ModelOutput


class BaseRecognizer(ABC):
    @abstractmethod
    def recognize(self, image: np.ndarray, **kwargs) -> ModelOutput:
        """
        Recognize text in a cropped image region.

        Args:
            image: Numpy RGB array of the cropped region.

        Returns:
            ModelOutput schema with recognized text and confidence.
        """
        pass

    @abstractmethod
    def recognize_batch(self, images: List[np.ndarray], **kwargs) -> List[ModelOutput]:
        """
        Recognize text across a batch of cropped image regions.
        """
        pass
