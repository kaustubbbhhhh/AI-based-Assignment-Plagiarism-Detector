"""
Layout Analyzer & Reading Order Reconstruction.
Analyzes document layout, discovers column boundaries, and reconstructs
natural reading order, preventing interleaved multi-column errors.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from ..schemas.ocr_schema import TextRegion, PageLayout
from ..config.config_loader import get_layout_config

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_layout_config()
        self.max_columns = self.config.get("max_columns", 3)
        self.column_gap_ratio = self.config.get("column_gap_ratio", 0.035)
        self.line_y_overlap = self.config.get("line_y_overlap_ratio", 0.45)
        self.header_zone_ratio = self.config.get("header_zone_ratio", 0.18)

    def analyze_page(
        self,
        regions: List[TextRegion],
        page_width: int,
        page_height: int,
        page_number: int = 1
    ) -> PageLayout:
        """
        Analyze page layout and sort regions into true reading order.

        Args:
            regions: List of recognized TextRegion objects.
            page_width: Pixel width of page image.
            page_height: Pixel height of page image.
            page_number: Page index.

        Returns:
            PageLayout schema containing ordered regions and column metadata.
        """
        if not regions:
            return PageLayout(
                page_number=page_number,
                width=page_width,
                height=page_height,
                num_columns=1,
                columns=[{"col_id": 0, "x_range": [0, page_width]}],
                reading_order=[],
                regions=[]
            )

        # 1. Identify Spanning Headers and Footers
        header_y_limit = int(page_height * self.header_zone_ratio)
        footer_y_limit = int(page_height * 0.92)

        header_regions: List[TextRegion] = []
        footer_regions: List[TextRegion] = []
        body_regions: List[TextRegion] = []

        top_margin_limit = max(45, int(page_height * 0.05))

        for reg in regions:
            x1, y1, x2, y2 = reg.bbox
            width = x2 - x1
            is_spanning = (width / float(page_width)) > 0.55

            if (y2 <= top_margin_limit) or (y2 <= header_y_limit and is_spanning):
                reg.column_id = -1
                header_regions.append(reg)
            elif y1 >= footer_y_limit and is_spanning:
                reg.column_id = -1
                footer_regions.append(reg)
            else:
                body_regions.append(reg)

        # 2. Detect Columns in Body Area
        columns, body_by_column = self._detect_and_partition_columns(body_regions, page_width)

        # 3. Sort each partition top-to-bottom
        sorted_headers = self._sort_vertical_reading_order(header_regions)
        sorted_footers = self._sort_vertical_reading_order(footer_regions)

        ordered_body: List[TextRegion] = []
        for col_id in sorted(body_by_column.keys()):
            col_regions = body_by_column[col_id]
            sorted_col = self._sort_vertical_reading_order(col_regions)
            for r in sorted_col:
                r.column_id = col_id
                ordered_body.append(r)

        # 4. Combine in natural flow: Headers -> Column 1 -> Column 2 -> Footers
        final_ordered_regions: List[TextRegion] = []
        final_ordered_regions.extend(sorted_headers)
        final_ordered_regions.extend(ordered_body)
        final_ordered_regions.extend(sorted_footers)

        # Assign reading order index
        reading_order_ids: List[str] = []
        for idx, reg in enumerate(final_ordered_regions, start=1):
            reg.reading_order_index = idx
            reading_order_ids.append(reg.region_id)

        num_cols = max(1, len(columns))
        logger.info(f"[LAYOUT] Page {page_number}: Reconstructed {num_cols}-column reading order ({len(final_ordered_regions)} regions).")

        return PageLayout(
            page_number=page_number,
            width=page_width,
            height=page_height,
            num_columns=num_cols,
            columns=columns,
            reading_order=reading_order_ids,
            regions=final_ordered_regions
        )

    def _detect_and_partition_columns(
        self,
        regions: List[TextRegion],
        page_width: int
    ) -> Tuple[List[Dict[str, Any]], Dict[int, List[TextRegion]]]:
        """
        Detects if body regions form single or multi-column layout,
        and assigns each region to a column bucket. Supports arbitrary N-columns.
        """
        if not regions:
            return ([{"col_id": 0, "x_range": [0, page_width]}], {0: []})

        # 1. Check if regions already carry distinct column_id assignments from RegionGrouper
        unique_cols = sorted(list(set(r.column_id for r in regions if hasattr(r, "column_id"))))
        if len(unique_cols) > 1:
            col_map = {old_c: new_c for new_c, old_c in enumerate(unique_cols)}
            for r in regions:
                if hasattr(r, "column_id"):
                    r.column_id = col_map.get(r.column_id, 0)
            unique_cols = list(range(len(unique_cols)))

            body_by_col = {c: [r for r in regions if r.column_id == c] for c in unique_cols}

            # Compute column spans using gutter midpoints to avoid clipping marginal characters/digits
            col_bounds = []
            for c in unique_cols:
                col_regs = body_by_col[c]
                x1 = min((r.bbox[0] for r in col_regs), default=0)
                x2 = max((r.bbox[2] for r in col_regs), default=page_width)
                col_bounds.append((x1, x2))

            columns = []
            for c in unique_cols:
                # Left bound: midpoint with previous column (with at least 20px lead-in), or 0
                if c == 0:
                    left_x = 0
                else:
                    mid_gutter = (col_bounds[c-1][1] + col_bounds[c][0]) // 2
                    left_x = max(0, min(mid_gutter, col_bounds[c][0] - 22))

                # Right bound: midpoint with next column, or page_width
                if c == len(unique_cols) - 1:
                    right_x = page_width
                else:
                    mid_gutter = (col_bounds[c][1] + col_bounds[c+1][0]) // 2
                    right_x = min(page_width, max(mid_gutter, col_bounds[c][1] + 15))

                columns.append({"col_id": c, "x_range": [left_x, right_x]})
            return (columns, body_by_col)

        # 2. Fallback: Dynamic TableExtractor Gutter Analysis
        from .table_extractor import TableExtractor
        te = TableExtractor()
        col_ranges = te.detect_column_boundaries(regions, page_width, page_height=int(page_width * 1.5))
        if len(col_ranges) > 1:
            col_buckets = te.assign_to_columns(regions, col_ranges)
            columns = [{"col_id": idx, "x_range": [c[0], c[1]]} for idx, c in enumerate(col_ranges)]
            return (columns, col_buckets)

        # Single-column fallback
        return ([{"col_id": 0, "x_range": [0, page_width]}], {0: regions})

    def _sort_vertical_reading_order(self, regions: List[TextRegion]) -> List[TextRegion]:
        """
        Sort regions in top-to-bottom reading order with left-to-right tie-breaking.
        """
        if not regions:
            return []

        # Sort primarily by Y1 (top), secondarily by X1 (left)
        return sorted(regions, key=lambda r: (r.bbox[1], r.bbox[0]))
