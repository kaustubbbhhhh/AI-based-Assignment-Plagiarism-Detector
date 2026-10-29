"""
Region Grouping Module.
Groups nearby character and word bounding boxes detected by CRAFT into
coherent text lines and structural blocks while preserving page coordinates.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class RegionGrouper:
    def __init__(
        self,
        line_y_overlap_ratio: float = 0.50,
        max_horizontal_gap_ratio: float = 1.8,
        min_line_height: int = 10
    ):
        self.line_y_overlap_ratio = line_y_overlap_ratio
        self.max_horizontal_gap_ratio = max_horizontal_gap_ratio
        self.min_line_height = min_line_height

    def group_into_lines(
        self,
        regions: List[Dict[str, Any]],
        page_width: int = None,
        page_height: int = None
    ) -> List[Dict[str, Any]]:
        """
        Groups fragmented word/character bounding boxes into unified horizontal text lines.
        If page_width and page_height are provided and multi-column layout is detected,
        groups boxes independently within each column to prevent multi-column line smearing.

        Args:
            regions: List of region dicts from CRAFT detector.
            page_width: Optional page pixel width for gutter detection.
            page_height: Optional page pixel height for gutter detection.

        Returns:
            List of merged region dicts representing full text lines.
        """
        if not regions:
            return []

        # Check for multi-column layout if page dimensions are available
        if page_width and page_height and len(regions) >= 8:
            from ..layout.table_extractor import TableExtractor
            te = TableExtractor()
            columns = te.detect_column_boundaries(regions, page_width, page_height)
            if len(columns) > 1:
                col_buckets = te.assign_to_columns(regions, columns)
                all_merged_regions = []
                line_counter = 1
                page_num = regions[0].get("page", 1)

                for col_idx in sorted(col_buckets.keys()):
                    col_regs = col_buckets[col_idx]
                    if not col_regs:
                        continue
                    col_merged = self._group_single_column(
                        col_regs, page_num, start_line_idx=line_counter, column_id=col_idx
                    )
                    line_counter += len(col_merged)
                    all_merged_regions.extend(col_merged)

                logger.info(
                    f"[GROUPER] Column-aware grouping: Partitioned {len(regions)} boxes across "
                    f"{len(columns)} columns -> {len(all_merged_regions)} independent line regions."
                )
                return all_merged_regions

        page_num = regions[0].get("page", 1)
        return self._group_single_column(regions, page_num, start_line_idx=1)

    def _group_single_column(
        self,
        regions: List[Dict[str, Any]],
        page_num: int,
        start_line_idx: int = 1,
        column_id: int = 0
    ) -> List[Dict[str, Any]]:
        """Groups bounding boxes into lines within a single column partition."""
        if not regions:
            return []

        # Split multi-line boxes that vertically span across lines
        median_h = float(np.median([r["bbox"][3] - r["bbox"][1] for r in regions])) if regions else 26.0
        expanded_regions = []
        for r in regions:
            bx1, by1, bx2, by2 = r["bbox"]
            bh = by2 - by1
            if bh > 1.8 * median_h:
                split_y = by1 + bh // 2
                r1 = dict(r)
                r1["bbox"] = [bx1, by1, bx2, split_y]
                r2 = dict(r)
                r2["bbox"] = [bx1, split_y, bx2, by2]
                expanded_regions.extend([r1, r2])
            else:
                expanded_regions.append(r)

        # Sort primarily by vertical center, secondarily by left X
        sorted_regions = sorted(
            expanded_regions,
            key=lambda r: ((r["bbox"][1] + r["bbox"][3]) / 2.0, r["bbox"][0])
        )

        lines: List[List[Dict[str, Any]]] = []

        for region in sorted_regions:
            x1, y1, x2, y2 = region["bbox"]
            height = y2 - y1
            y_mid = (y1 + y2) / 2.0

            matched_line_idx = None
            best_diff = float("inf")

            for idx, line in enumerate(lines):
                line_ymids = [(b["bbox"][1] + b["bbox"][3]) / 2.0 for b in line]
                line_y_mid = float(np.mean(line_ymids))
                diff = abs(y_mid - line_y_mid)

                # Rule 1: Vertical center threshold (words on the same line share baseline)
                if diff > max(10, 0.40 * median_h):
                    continue

                # Rule 2: In a single horizontal line, words cannot overlap horizontally
                has_h_overlap = False
                for b in line:
                    bx1, by1, bx2, by2 = b["bbox"]
                    if max(0, min(x2, bx2) - max(x1, bx1)) > 8:
                        has_h_overlap = True
                        break
                if has_h_overlap:
                    continue

                # Rule 3: Restrict maximum line bounding box height expansion
                line_y1 = min(b["bbox"][1] for b in line)
                line_y2 = max(b["bbox"][3] for b in line)
                line_height = line_y2 - line_y1
                new_h = max(line_y2, y2) - min(line_y1, y1)
                if new_h > 1.6 * max(height, line_height, median_h):
                    continue

                # Rule 4: Check horizontal proximity
                line_x2 = max(b["bbox"][2] for b in line)
                h_gap = x1 - line_x2
                if h_gap > (self.max_horizontal_gap_ratio * max(height, line_height)):
                    continue

                if diff < best_diff:
                    best_diff = diff
                    matched_line_idx = idx

            if matched_line_idx is not None:
                lines[matched_line_idx].append(region)
            else:
                lines.append([region])

        merged_regions: List[Dict[str, Any]] = []
        for line_offset, line in enumerate(lines):
            line_idx = start_line_idx + line_offset
            line = sorted(line, key=lambda r: r["bbox"][0])

            x1 = min(r["bbox"][0] for r in line)
            y1 = min(r["bbox"][1] for r in line)
            x2 = max(r["bbox"][2] for r in line)
            y2 = max(r["bbox"][3] for r in line)

            avg_conf = float(np.mean([r["confidence"] for r in line]))
            w = x2 - x1
            h = y2 - y1

            merged_regions.append({
                "id": f"p{page_num}_line_{line_idx:04d}",
                "page": page_num,
                "column_id": column_id,
                "bbox": [x1, y1, x2, y2],
                "polygon": [
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2]
                ],
                "confidence": round(avg_conf, 3),
                "area": w * h,
                "aspect_ratio": round(float(w / float(max(1, h))), 2),
                "child_box_count": len(line)
            })

        return merged_regions
