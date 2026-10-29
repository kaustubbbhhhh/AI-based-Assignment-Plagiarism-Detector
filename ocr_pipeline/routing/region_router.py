"""
Intelligent Region Router.
Routes detected regions to appropriate specialized recognition models (TrOCR, GOT-OCR, or Both).
Architected with an abstract base class so rule-based routing can be replaced with a learned classifier.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np

from ..schemas.ocr_schema import RoutingCategory, ContentType
from .feature_extractor import RegionFeatureExtractor
from ..config.config_loader import get_routing_config

logger = logging.getLogger(__name__)


class BaseRegionRouter(ABC):
    """Abstract interface for region routing."""

    @abstractmethod
    def route_region(
        self,
        crop: np.ndarray,
        region: Dict[str, Any],
        page_shape: Tuple[int, int]
    ) -> Tuple[RoutingCategory, ContentType, Dict[str, Any]]:
        """
        Evaluate a region and return (RoutingCategory, ContentType, features).
        """
        pass


class RuleBasedRegionRouter(BaseRegionRouter):
    """
    Configurable rule-based router that analyzes geometric, morphological,
    and texture features to direct regions to specialized recognition models.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_routing_config()
        self.conf_threshold = self.config.get("confidence_threshold", 0.80)
        self.math_cfg = self.config.get("math", {})
        self.table_cfg = self.config.get("table", {})
        self.uncertain_cfg = self.config.get("uncertain", {})

    def route_region(
        self,
        crop: np.ndarray,
        region: Dict[str, Any],
        page_shape: Tuple[int, int]
    ) -> Tuple[RoutingCategory, ContentType, Dict[str, Any]]:
        """
        Route region based on visual features and CRAFT detection properties.
        """
        bbox = region.get("bbox", [0, 0, 0, 0])
        craft_conf = region.get("confidence", 1.0)

        # Extract geometric & visual features
        features = RegionFeatureExtractor.extract_features(crop, bbox, page_shape)
        features["craft_confidence"] = craft_conf

        # 1. Check for Table Structure
        if features["is_table_like"]:
            logger.info(f"[ROUTER] Region {region.get('id')} -> COMPLEX (TABLE)")
            return RoutingCategory.COMPLEX, ContentType.TABLE, features

        # 2. Check for Mathematical Formulas
        if features["is_math_like"]:
            logger.info(f"[ROUTER] Region {region.get('id')} -> COMPLEX (FORMULA)")
            return RoutingCategory.COMPLEX, ContentType.FORMULA, features

        # 3. Check for Uncertain / Degraded Region
        # CRAFT confidence low, or unusual stroke density, or very small aspect ratio
        min_craft_conf = self.uncertain_cfg.get("min_craft_confidence", 0.60)
        if craft_conf < min_craft_conf or features["stroke_density"] > 0.45 or features["laplacian_var"] < 15.0:
            logger.info(f"[ROUTER] Region {region.get('id')} -> UNCERTAIN (TrOCR + GOT)")
            return RoutingCategory.UNCERTAIN, ContentType.TEXT, features

        # 4. Standard Text Line / Paragraph
        # Default: TrOCR is the preferred specialist for clean line & handwritten text
        logger.info(f"[ROUTER] Region {region.get('id')} -> NORMAL (TrOCR)")
        return RoutingCategory.NORMAL, ContentType.TEXT, features
