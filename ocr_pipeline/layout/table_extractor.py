"""
Table & Multi-Column Layout Extractor.
Detects vertical whitespace gutters, partitions text regions into discrete columns,
and aligns multi-column cells into structured tabular rows (Markdown and JSON).
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class TableExtractor:
    def __init__(
        self,
        min_gutter_width: int = 14,
        y_row_tolerance: int = 22,
        header_ratio: float = 0.04,
        footer_ratio: float = 0.92
    ):
        self.min_gutter_width = min_gutter_width
        self.y_row_tolerance = y_row_tolerance
        self.header_ratio = header_ratio
        self.footer_ratio = footer_ratio

    def detect_column_boundaries(
        self,
        boxes_or_regions: List[Any],
        page_width: int,
        page_height: int
    ) -> List[Tuple[int, int]]:
        """
        Detects vertical gutters across character/word bounding boxes.
        Returns a list of column (x_start, x_end) ranges.
        """
        if not boxes_or_regions or len(boxes_or_regions) < 6:
            return [(0, page_width)]

        # Extract normalized [x1, y1, x2, y2]
        extracted_boxes = []
        for item in boxes_or_regions:
            if hasattr(item, "bbox"):
                b = item.bbox
            elif isinstance(item, dict) and "bbox" in item:
                b = item["bbox"]
            elif isinstance(item, (list, tuple)) and len(item) == 4:
                b = [item[0], item[2], item[1], item[3]] if item[2] < item[1] else item
            else:
                continue
            extracted_boxes.append(b)

        if not extracted_boxes:
            return [(0, page_width)]

        # Exclude header/footer zones and wide spanning banners
        y_top = int(page_height * self.header_ratio)
        y_bottom = int(page_height * self.footer_ratio)

        body_boxes = [
            b for b in extracted_boxes
            if b[1] >= y_top and b[3] <= y_bottom and (b[2] - b[0]) < (page_width * 0.55)
        ]

        if len(body_boxes) < 6:
            return [(0, page_width)]

        # Build X occupancy histogram
        hist = np.zeros(page_width, dtype=int)
        for b in body_boxes:
            x1 = max(0, min(page_width, int(b[0])))
            x2 = max(0, min(page_width, int(b[2])))
            if x2 > x1:
                hist[x1:x2] += 1

        # Search for gutters (valleys in occupancy) in the middle 80% of page
        margin_x1 = int(page_width * 0.08)
        margin_x2 = int(page_width * 0.94)

        max_occ = np.max(hist[margin_x1:margin_x2]) if len(hist) > 0 else 1
        valley_threshold = max(0, int(max_occ * 0.12))

        gutters: List[Tuple[int, int]] = []
        in_valley = False
        start_x = 0

        for x in range(margin_x1, margin_x2):
            is_low = (hist[x] <= valley_threshold)
            if is_low and not in_valley:
                start_x = x
                in_valley = True
            elif not is_low and in_valley:
                end_x = x
                in_valley = False
                if (end_x - start_x) >= self.min_gutter_width:
                    gutters.append((start_x, end_x))

        if in_valley and (margin_x2 - start_x) >= self.min_gutter_width:
            gutters.append((start_x, margin_x2))

        # Filter gutters: enforce minimum column width between adjacent gutters
        min_col_width = int(page_width * 0.12)
        filtered_gutters: List[Tuple[int, int]] = []
        for g in gutters:
            if not filtered_gutters:
                if g[0] >= min_col_width:
                    filtered_gutters.append(g)
            else:
                prev_mid = (filtered_gutters[-1][0] + filtered_gutters[-1][1]) // 2
                curr_mid = (g[0] + g[1]) // 2
                if (curr_mid - prev_mid) >= min_col_width:
                    filtered_gutters.append(g)

        if filtered_gutters:
            last_mid = (filtered_gutters[-1][0] + filtered_gutters[-1][1]) // 2
            if (page_width - last_mid) < (min_col_width * 0.6):
                filtered_gutters.pop()

        if not filtered_gutters:
            return [(0, page_width)]

        # Convert gutters into column intervals
        column_ranges: List[Tuple[int, int]] = []
        prev_x = 0
        for g_start, g_end in filtered_gutters:
            mid_x = (g_start + g_end) // 2
            column_ranges.append((prev_x, mid_x))
            prev_x = mid_x
        column_ranges.append((prev_x, page_width))

        logger.info(f"[TABLE] Detected {len(column_ranges)} columns with gutters: {filtered_gutters}")
        return column_ranges

    def assign_to_columns(
        self,
        items: List[Any],
        column_ranges: List[Tuple[int, int]]
    ) -> Dict[int, List[Any]]:
        """
        Partitions items (regions, boxes) into column buckets.
        """
        col_buckets: Dict[int, List[Any]] = {i: [] for i in range(len(column_ranges))}

        for item in items:
            if hasattr(item, "bbox"):
                b = item.bbox
            elif isinstance(item, dict) and "bbox" in item:
                b = item["bbox"]
            else:
                continue

            x_mid = (b[0] + b[2]) / 2.0

            # Find matching column
            assigned_col = 0
            for col_idx, (c_start, c_end) in enumerate(column_ranges):
                if c_start <= x_mid < c_end:
                    assigned_col = col_idx
                    break
                elif col_idx == len(column_ranges) - 1 and x_mid >= c_end:
                    assigned_col = col_idx

            col_buckets[assigned_col].append(item)

        return col_buckets

    def align_rows(
        self,
        column_items: Dict[int, List[Any]],
        num_columns: int = None
    ) -> List[Dict[str, Any]]:
        """
        Aligns column items into structured table rows based on vertical Y proximity.
        """
        col_keys = sorted(column_items.keys())
        if not col_keys:
            return []

        actual_num_cols = len(col_keys) if num_columns is None else max(num_columns, len(col_keys))

        # Sort items within each column by Y center
        sorted_cols: Dict[int, List[Any]] = {}
        for slot_idx, k in enumerate(col_keys):
            items = column_items.get(k, [])
            sorted_cols[slot_idx] = sorted(
                items,
                key=lambda item: ((item.bbox[1] + item.bbox[3]) / 2.0 if hasattr(item, "bbox")
                                  else (item["bbox"][1] + item["bbox"][3]) / 2.0)
            )

        # Select anchor column: the column with the most regular vertical spacing (lowest std of gaps)
        def col_regularity(items):
            if len(items) < 3:
                return float("inf")
            ymids = sorted([
                (it.bbox[1] + it.bbox[3]) / 2.0 if hasattr(it, "bbox")
                else (it["bbox"][1] + it["bbox"][3]) / 2.0
                for it in items
            ])
            gaps = np.diff(ymids)
            return float(np.std(gaps)) if len(gaps) > 0 else float("inf")

        regularities = [col_regularity(sorted_cols.get(s, [])) for s in range(actual_num_cols)]
        # Prefer column with lowest gap variance that has at least 3 items
        valid_slots = [s for s in range(actual_num_cols) if len(sorted_cols.get(s, [])) >= 3]
        if valid_slots:
            anchor_slot = min(valid_slots, key=lambda s: regularities[s])
        else:
            anchor_slot = max(range(actual_num_cols), key=lambda s: len(sorted_cols.get(s, [])))

        anchor_items = sorted_cols.get(anchor_slot, [])
        if not anchor_items:
            return []

        # Define vertical row intervals based on anchor column midpoints
        num_anchor_rows = len(anchor_items)
        row_intervals: List[Tuple[float, float, float]] = []
        for i in range(num_anchor_rows):
            curr_y = ((anchor_items[i].bbox[1] + anchor_items[i].bbox[3]) / 2.0 if hasattr(anchor_items[i], "bbox")
                      else (anchor_items[i]["bbox"][1] + anchor_items[i]["bbox"][3]) / 2.0)
            if i == 0:
                top_y = 0.0
            else:
                prev_y = ((anchor_items[i-1].bbox[1] + anchor_items[i-1].bbox[3]) / 2.0 if hasattr(anchor_items[i-1], "bbox")
                          else (anchor_items[i-1]["bbox"][1] + anchor_items[i-1]["bbox"][3]) / 2.0)
                top_y = (prev_y + curr_y) / 2.0
            if i == num_anchor_rows - 1:
                bot_y = float("inf")
            else:
                next_y = ((anchor_items[i+1].bbox[1] + anchor_items[i+1].bbox[3]) / 2.0 if hasattr(anchor_items[i+1], "bbox")
                          else (anchor_items[i+1]["bbox"][1] + anchor_items[i+1]["bbox"][3]) / 2.0)
                bot_y = (curr_y + next_y) / 2.0
            row_intervals.append((top_y, bot_y, curr_y))

        # Populate row cells
        rows: List[Dict[str, Any]] = []
        for r_idx, (y_min, y_max, a_y) in enumerate(row_intervals):
            row_cells = [None] * actual_num_cols
            row_cells[anchor_slot] = anchor_items[r_idx]

            # Assign matching items from other columns
            for slot_idx in range(actual_num_cols):
                if slot_idx == anchor_slot:
                    continue
                matches = []
                for o_item in sorted_cols.get(slot_idx, []):
                    o_y = ((o_item.bbox[1] + o_item.bbox[3]) / 2.0 if hasattr(o_item, "bbox")
                           else (o_item["bbox"][1] + o_item["bbox"][3]) / 2.0)
                    if y_min <= o_y < y_max:
                        matches.append(o_item)
                if len(matches) == 1:
                    row_cells[slot_idx] = matches[0]
                elif len(matches) > 1:
                    row_cells[slot_idx] = matches

            rows.append({
                "row_index": r_idx + 1,
                "cells": row_cells,
                "y_center": a_y
            })

        return rows

    def format_table(
        self,
        rows: List[Dict[str, Any]],
        column_headers: Optional[List[str]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Formats table rows into a Markdown string and JSON records.
        """
        if not rows:
            return ("", [])

        num_cols = len(rows[0]["cells"])
        if not column_headers:
            column_headers = [f"Column {i+1}" for i in range(num_cols)]

        # Extract text strings from cells
        text_rows = []
        json_records = []

        for r in rows:
            row_texts = []
            for cell in r["cells"]:
                if cell is None:
                    row_texts.append("")
                elif isinstance(cell, list):
                    parts = []
                    for sub in cell:
                        if hasattr(sub, "text"):
                            parts.append(sub.text.strip())
                        elif isinstance(sub, dict) and "text" in sub:
                            parts.append(sub["text"].strip())
                        else:
                            parts.append(str(sub).strip())
                    row_texts.append(" ".join(p for p in parts if p))
                elif hasattr(cell, "text"):
                    row_texts.append(cell.text.strip())
                elif isinstance(cell, dict) and "text" in cell:
                    row_texts.append(cell["text"].strip())
                else:
                    row_texts.append(str(cell).strip())

            text_rows.append(row_texts)

            record = {
                header: val for header, val in zip(column_headers, row_texts)
            }
            json_records.append(record)

        # Build Markdown Table
        md_lines = []
        md_lines.append("| " + " | ".join(column_headers) + " |")
        md_lines.append("| " + " | ".join([":---"] * num_cols) + " |")
        for row_t in text_rows:
            md_lines.append("| " + " | ".join(row_t) + " |")

        markdown_table = "\n".join(md_lines)
        return (markdown_table, json_records)
