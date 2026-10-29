"""
Unified OCR Data Schemas.
Provides strictly validated data classes for regions, alternatives, layout,
and higher-level assignment documents.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    TEXT = "text"
    FORMULA = "formula"
    TABLE = "table"
    HEADING = "heading"
    DIAGRAM = "diagram"
    MIXED = "mixed"


class RoutingCategory(str, Enum):
    NORMAL = "normal"          # Clean printed/handwritten line -> TrOCR
    COMPLEX = "complex"        # Formula, table, dense math -> GOT-OCR
    UNCERTAIN = "uncertain"    # TrOCR initially, escalates to GOT if confidence is low


class ModelOutput(BaseModel):
    """Raw output from a specific OCR recognition engine."""
    model: str                 # "trocr", "got", "craft", "fallback"
    text: str
    confidence: float          # 0.0 to 1.0
    latency_ms: Optional[float] = None
    raw_tokens: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DetectionRegion(BaseModel):
    """Initial text detection bounding box and polygon from CRAFT."""
    id: str
    page: int = 1
    bbox: List[int]            # [x1, y1, x2, y2] in pixel coordinates
    polygon: Optional[List[List[int]]] = Field(default_factory=list)  # [[x1, y1], [x2, y2], ...]
    confidence: float = 1.0    # CRAFT heatmap confidence
    area: int = 0
    aspect_ratio: float = 1.0


class TextRegion(BaseModel):
    """Unified OCR representation for a single detected/recognized text region."""
    region_id: str
    page: int = 1
    bbox: List[int]            # [x1, y1, x2, y2]
    polygon: Optional[List[List[int]]] = Field(default_factory=list)
    text: str = ""
    confidence: float = 0.0    # 0.0 to 1.0
    model: str = "fused"       # "trocr", "got", "fused"
    content_type: ContentType = ContentType.TEXT
    routing_category: Optional[RoutingCategory] = None
    alternatives: List[ModelOutput] = Field(default_factory=list)
    raw_craft: Optional[Dict[str, Any]] = None
    raw_trocr: Optional[Dict[str, Any]] = None
    raw_got: Optional[Dict[str, Any]] = None
    needs_review: bool = False
    review_reason: Optional[str] = None
    column_id: int = 0         # 0-indexed column index assigned by layout analyzer
    reading_order_index: int = 0


class PageLayout(BaseModel):
    """Layout analysis output for a single document page."""
    page_number: int
    width: int
    height: int
    num_columns: int = 1
    columns: List[Dict[str, Any]] = Field(default_factory=list)  # [{"col_id": 0, "x_range": [0, 400]}]
    reading_order: List[str] = Field(default_factory=list)       # Ordered list of region IDs
    regions: List[TextRegion] = Field(default_factory=list)
    table_markdown: Optional[str] = None
    table_records: List[Dict[str, Any]] = Field(default_factory=list)


class AssignmentSubpart(BaseModel):
    """Subpart of a question (e.g. 1(a), 1(b))."""
    subpart_id: str            # "a", "b", "i", "ii"
    question_text: str
    answer_text: str = ""
    confidence: float = 1.0


class AssignmentSection(BaseModel):
    """Structured question-answer section of an assignment."""
    section_id: str
    question_number: str       # "1", "2.a", "Q3", "Problem 1"
    question: str
    answer: str
    page: int = 1
    content_type: ContentType = ContentType.TEXT
    subparts: List[AssignmentSubpart] = Field(default_factory=list)
    confidence: float = 1.0
    source_region_ids: List[str] = Field(default_factory=list)


class StudentMetadata(BaseModel):
    """Metadata extracted from assignment header."""
    name: Optional[str] = None
    roll_number: Optional[str] = None
    assignment_number: Optional[str] = None
    subject: Optional[str] = None
    submission_date: Optional[str] = None
    raw_header_text: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Document-level metadata."""
    pages: int = 1
    type: str = "assignment"
    title: Optional[str] = None
    student_info: StudentMetadata = Field(default_factory=StudentMetadata)
    subject: Optional[str] = None
    overall_confidence: float = 0.0


class AssignmentDocument(BaseModel):
    """Top-level structured output of the OCR Assignment Pipeline."""
    document: DocumentMetadata
    sections: List[AssignmentSection] = Field(default_factory=list)
    pages: List[PageLayout] = Field(default_factory=list)
    processing_summary: Dict[str, Any] = Field(default_factory=dict)
