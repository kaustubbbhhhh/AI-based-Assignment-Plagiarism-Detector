"""
Multi-Model Assignment OCR Pipeline (CRAFT + TrOCR + GOT-OCR 2.0).
"""

from .pipeline.pipeline import OCRPipeline
from .models.model_manager import ModelManager
from .schemas.ocr_schema import (
    TextRegion,
    PageLayout,
    AssignmentDocument,
    AssignmentSection,
    ContentType,
    RoutingCategory,
)

__version__ = "1.0.0"

__all__ = [
    "OCRPipeline",
    "ModelManager",
    "TextRegion",
    "PageLayout",
    "AssignmentDocument",
    "AssignmentSection",
    "ContentType",
    "RoutingCategory",
]
