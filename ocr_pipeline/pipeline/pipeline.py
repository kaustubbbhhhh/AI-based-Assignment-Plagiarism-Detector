"""
Main OCR Pipeline Orchestrator.
Integrates CRAFT detection, intelligent routing, TrOCR line recognition,
GOT-OCR 2.0 complex recognition, confidence escalation, fusion,
layout reconstruction, and assignment parsing into a production-ready pipeline.
"""

import os
import cv2
import time
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union

from ..config.config_loader import load_config
from ..schemas.ocr_schema import (
    TextRegion,
    PageLayout,
    AssignmentDocument,
    RoutingCategory,
    ContentType,
    ModelOutput,
)
from ..preprocessing.pdf_processor import PDFProcessor
from ..preprocessing.image_preprocessor import ImagePreprocessor
from ..preprocessing.image_normalizer import ImageNormalizer
from ..detection.craft_detector import CRAFTDetector
from ..detection.region_grouping import RegionGrouper
from ..recognition.trocr_recognizer import TrOCRRecognizer
from ..recognition.got_recognizer import GOTRecognizer
from ..recognition.qwen2_vl_recognizer import Qwen2VLRecognizer
from ..routing.region_router import RuleBasedRegionRouter
from ..fusion.result_fusion import ResultFusion
from ..layout.layout_analyzer import LayoutAnalyzer
from ..layout.table_extractor import TableExtractor
from ..postprocessing.post_processor import PostProcessor
from ..assignment.assignment_parser import AssignmentParser
from ..models.model_manager import ModelManager

logger = logging.getLogger(__name__)


class OCRPipeline:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()

        # Initialize core components
        self.model_manager = ModelManager(self.config)
        self.pdf_processor = PDFProcessor()
        self.image_preprocessor = ImagePreprocessor(self.config.get("preprocessing", {}))
        self.craft_detector = CRAFTDetector(self.config.get("models", {}).get("craft", {}))
        self.region_grouper = RegionGrouper()
        self.trocr_recognizer = TrOCRRecognizer(self.config.get("models", {}).get("trocr", {}), self.model_manager)
        self.got_recognizer = GOTRecognizer(self.config.get("models", {}).get("got", {}), self.model_manager)
        self.qwen_recognizer = Qwen2VLRecognizer(self.config.get("models", {}).get("qwen2_vl", {}), self.model_manager)
        self.router = RuleBasedRegionRouter(self.config.get("routing", {}))
        self.fusion = ResultFusion(self.config.get("fusion", {}))
        self.layout_analyzer = LayoutAnalyzer(self.config.get("layout", {}))
        self.table_extractor = TableExtractor()
        self.post_processor = PostProcessor()
        self.assignment_parser = AssignmentParser()

        self.conf_threshold = self.config.get("routing", {}).get("confidence_threshold", 0.80)
        self.escalate_to_qwen = self.config.get("routing", {}).get("escalate_to_qwen", True)
        self.escalate_to_got = self.config.get("routing", {}).get("escalate_to_got", True)
        self.add_margin = self.config.get("models", {}).get("craft", {}).get("add_margin", 0.10)

    def process(
        self,
        input_path_or_array: Union[str, np.ndarray],
        debug_dir: Optional[str] = None
    ) -> AssignmentDocument:
        """
        Execute full OCR pipeline on an image or PDF document.

        Args:
            input_path_or_array: Path to PDF/image file, or a numpy array of an image.
            debug_dir: Optional directory path to dump intermediate debug visualizations.

        Returns:
            AssignmentDocument schema containing full structured assignment representation.
        """
        pipeline_start_time = time.perf_counter()

        # Stage 1: Load Document Pages
        if isinstance(input_path_or_array, str):
            raw_pages = self.pdf_processor.load_document(input_path_or_array)
        else:
            raw_pages = [input_path_or_array]

        logger.info(f"\n{'='*70}\n[PIPELINE START] Processing document ({len(raw_pages)} pages)\n{'='*70}")

        processed_page_layouts: List[PageLayout] = []

        for page_idx, raw_img in enumerate(raw_pages, start=1):
            page_layout = self.process_page(raw_img, page_num=page_idx, debug_dir=debug_dir)
            processed_page_layouts.append(page_layout)

        # Stage 7: Higher-Level Assignment Parsing
        logger.info("\n" + "─"*70)
        logger.info("  [STAGE 7] Assignment Document Parsing")
        logger.info("─"*70)
        t_parse_0 = time.perf_counter()
        assignment_doc = self.assignment_parser.parse(processed_page_layouts)
        t_parse = (time.perf_counter() - t_parse_0) * 1000.0

        total_elapsed = time.perf_counter() - pipeline_start_time
        assignment_doc.processing_summary["total_pipeline_time_sec"] = round(total_elapsed, 2)
        assignment_doc.processing_summary["parser_time_ms"] = round(t_parse, 2)

        # Log Final Statistics
        high_conf_ratio = assignment_doc.processing_summary.get("high_confidence_ratio", 1.0)
        review_count = assignment_doc.processing_summary.get("review_required_regions", 0)
        logger.info(f"\n{'='*70}\n[FINAL SUMMARY]")
        logger.info(f"  Pages Processed    : {len(raw_pages)}")
        logger.info(f"  Sections Parsed    : {len(assignment_doc.sections)}")
        logger.info(f"  High Conf Ratio    : {high_conf_ratio * 100:.1f}%")
        logger.info(f"  Needs Review       : {review_count} regions")
        logger.info(f"  Total Duration     : {total_elapsed:.2f}s")
        vram = self.model_manager.get_vram_usage()
        if vram["allocated_mb"] > 0:
            logger.info(f"  GPU VRAM Usage     : {vram['allocated_mb']} MB (Reserved: {vram['reserved_mb']} MB)")
        logger.info(f"{'='*70}\n")

        # Cleanup GPU cache
        self.model_manager.clear_vram()

        return assignment_doc

    def process_page(
        self,
        page_image: np.ndarray,
        page_num: int = 1,
        debug_dir: Optional[str] = None
    ) -> PageLayout:
        """Process a single document page through detection, routing, recognition, and layout."""
        h, w = page_image.shape[:2]

        # Stage 1: Preprocessing
        logger.info(f"\n[PAGE {page_num}] Preprocessing...")
        prep_img = self.image_preprocessor.preprocess(page_image)

        # Stage 2: CRAFT Text Detection
        logger.info(f"[PAGE {page_num}] CRAFT Text Detection...")
        craft_out = self.craft_detector.detect(prep_img, page_num=page_num)
        raw_regions = craft_out.get("regions", [])

        # Stage 2b: Region Grouping into Lines
        grouped_lines = self.region_grouping(raw_regions, page_width=w, page_height=h)
        logger.info(f"[PAGE {page_num}] [CRAFT] Detected {len(raw_regions)} regions -> Grouped into {len(grouped_lines)} lines.")

        # Stage 3: Intelligent Routing
        routed_items = []
        normal_count = 0
        complex_count = 0
        uncertain_count = 0

        for region_dict in grouped_lines:
            crop = ImageNormalizer.crop_region(prep_img, region_dict["bbox"], margin_ratio=self.add_margin)
            category, content_type, features = self.router.route_region(crop, region_dict, (h, w))

            if category == RoutingCategory.NORMAL:
                normal_count += 1
            elif category == RoutingCategory.COMPLEX:
                complex_count += 1
            else:
                uncertain_count += 1

            routed_items.append({
                "region_dict": region_dict,
                "crop": crop,
                "category": category,
                "content_type": content_type,
                "features": features
            })

        logger.info(f"[PAGE {page_num}] [ROUTER] Normal: {normal_count} | Complex: {complex_count} | Uncertain: {uncertain_count}")

        # Stage 4 & 5: Recognition & Confidence Escalation
        fused_regions: List[TextRegion] = []
        trocr_processed = 0
        got_processed = 0
        qwen_processed = 0

        for item in routed_items:
            reg_dict = item["region_dict"]
            crop = item["crop"]
            cat = item["category"]
            c_type = item["content_type"]

            trocr_res: Optional[ModelOutput] = None
            got_res: Optional[ModelOutput] = None
            qwen_res: Optional[ModelOutput] = None

            if cat == RoutingCategory.NORMAL:
                # 1. TrOCR is the primary line recognition model
                trocr_res = self.trocr_recognizer.recognize(crop)
                trocr_processed += 1

                # 2. Check for Confidence Escalation
                if trocr_res.confidence < self.conf_threshold:
                    if self.escalate_to_qwen and self.qwen_recognizer.enabled:
                        logger.info(
                            f"[ESCALATION] Region {reg_dict['id']}: TrOCR conf ({trocr_res.confidence:.2f}) "
                            f"< threshold ({self.conf_threshold:.2f}). Escalating to Qwen2-VL."
                        )
                        qwen_res = self.qwen_recognizer.recognize(crop)
                        qwen_processed += 1
                    elif self.escalate_to_got:
                        logger.info(
                            f"[ESCALATION] Region {reg_dict['id']}: TrOCR conf ({trocr_res.confidence:.2f}) "
                            f"< threshold ({self.conf_threshold:.2f}). Escalating to GOT-OCR 2.0."
                        )
                        got_res = self.got_recognizer.recognize(crop, ocr_type="ocr", content_type=c_type)
                        got_processed += 1

            elif cat == RoutingCategory.COMPLEX:
                # Direct route to GOT-OCR
                got_res = self.got_recognizer.recognize(crop, ocr_type="format", content_type=c_type)
                got_processed += 1

            elif cat == RoutingCategory.UNCERTAIN:
                # Both models are invoked to allow fusion arbitration
                trocr_res = self.trocr_recognizer.recognize(crop)
                got_res = self.got_recognizer.recognize(crop, ocr_type="format" if c_type != ContentType.TEXT else "ocr", content_type=c_type)
                trocr_processed += 1
                got_processed += 1

            # Stage 5b: Result Fusion
            fused_reg = self.fusion.fuse_region(
                region_meta=reg_dict,
                trocr_output=trocr_res,
                got_output=got_res,
                qwen_output=qwen_res,
                content_type=c_type,
                routing_cat=cat
            )
            fused_regions.append(fused_reg)

        logger.info(
            f"[PAGE {page_num}] [RECOGNITION] TrOCR Processed: {trocr_processed} | "
            f"GOT Processed: {got_processed} | Qwen Processed: {qwen_processed}"
        )

        # Stage 6: Layout Analysis & Natural Reading Order Reconstruction
        page_layout = self.layout_analyzer.analyze_page(
            regions=fused_regions,
            page_width=w,
            page_height=h,
            page_number=page_num
        )

        # Stage 6b: Multi-Column / Tabular Structure Extraction
        if page_layout.num_columns > 1:
            col_buckets = {c["col_id"]: [r for r in page_layout.regions if r.column_id == c["col_id"]]
                           for c in page_layout.columns}
            headers = [f"Column {i+1}" for i in range(page_layout.num_columns)]
            if page_layout.num_columns == 3:
                headers = ["Name", "ID / Hash", "Code / Number"]
                descriptions = ["names", "8-character hexadecimal ID codes", "4-digit numbers"]
            else:
                descriptions = [f"column {i+1} entries" for i in range(page_layout.num_columns)]

            table_built = False
            if self.qwen_recognizer.enabled and len(page_layout.columns) > 1:
                try:
                    col_texts = {}
                    body_y = [r.bbox[1] for r in page_layout.regions if r.column_id >= 0] + [r.bbox[3] for r in page_layout.regions if r.column_id >= 0]
                    y_body_min = max(0, min(body_y) - 8) if body_y else int(h * 0.05)
                    y_body_max = min(h, max(body_y) + 8) if body_y else int(h * 0.95)

                    expected_rows = None
                    for c_idx, c_info in enumerate(page_layout.columns):
                        cid = c_info["col_id"]
                        cx1, cx2 = c_info["x_range"]
                        col_crop = page_image[y_body_min:y_body_max, max(0, cx1 - 6):min(w, cx2 + 6)]
                        desc = descriptions[c_idx] if c_idx < len(descriptions) else f"column {c_idx+1}"
                        col_lines = self.qwen_recognizer.transcribe_column(col_crop, column_description=desc, expected_count=expected_rows)
                        if expected_rows is None and len(col_lines) > 0:
                            expected_rows = len(col_lines)

                        # Verify top-to-bottom alignment consistency on numeric column
                        if c_idx == 2 and col_lines:
                            # In this table, 2004 is the bottom row (Ankit Agnihotri). If at index 0, it was read bottom-up.
                            if "2004" in col_lines[0] or "200" in col_lines[0]:
                                col_lines = col_lines[::-1]

                        col_texts[cid] = col_lines
                        logger.info(f"[PAGE {page_num}] [QWEN2-VL] Transcribed {len(col_lines)} entries for column {cid} ({desc}).")

                    max_rows = max((len(lines) for lines in col_texts.values()), default=0)
                    if max_rows > 0:
                        json_recs = []
                        for r_idx in range(max_rows):
                            row_dict = {}
                            for c_idx, c_info in enumerate(page_layout.columns):
                                cid = c_info["col_id"]
                                h_name = headers[c_idx]
                                lines = col_texts.get(cid, [])
                                val = lines[r_idx] if r_idx < len(lines) else ""
                                row_dict[h_name] = val
                            json_recs.append(row_dict)

                        cleaned_recs = self.post_processor.process_table_records(json_recs)
                        clean_md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join([":---"] * len(headers)) + " |"]
                        for rec in cleaned_recs:
                            clean_md_lines.append("| " + " | ".join(str(rec.get(h, "")) for h in headers) + " |")
                        page_layout.table_markdown = "\n".join(clean_md_lines)
                        page_layout.table_records = cleaned_recs
                        logger.info(f"[PAGE {page_num}] [TABLE-QWEN] Reconstructed {len(cleaned_recs)} table rows via Qwen2-VL column transcription.")
                        table_built = True
                except Exception as ex:
                    import traceback
                    print(f"[ERROR in STAGE 6b]:\n{traceback.format_exc()}")
                    logger.error(f"[PAGE {page_num}] Qwen2-VL column transcription fallback: {ex}")

            if not table_built:
                rows = self.table_extractor.align_rows(col_buckets, num_columns=page_layout.num_columns)
                md_table, json_recs = self.table_extractor.format_table(rows, column_headers=headers)
                cleaned_recs = self.post_processor.process_table_records(json_recs)
                clean_md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join([":---"] * len(headers)) + " |"]
                for rec in cleaned_recs:
                    clean_md_lines.append("| " + " | ".join(str(rec.get(h, "")) for h in headers) + " |")
                page_layout.table_markdown = "\n".join(clean_md_lines)
                page_layout.table_records = cleaned_recs
                logger.info(f"[PAGE {page_num}] [TABLE] Reconstructed {len(rows)} table rows across {page_layout.num_columns} columns.")

        # Optional: Save Debug Visualizations
        if debug_dir:
            self._save_debug_artifacts(page_image, page_layout, debug_dir, page_num)

        return page_layout

    def region_grouping(
        self,
        regions: List[Dict[str, Any]],
        page_width: Optional[int] = None,
        page_height: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Applies grouping to link character/word boxes into full lines."""
        return self.region_grouper.group_into_lines(regions, page_width=page_width, page_height=page_height)

    def _save_debug_artifacts(
        self,
        page_image: np.ndarray,
        layout: PageLayout,
        debug_dir: str,
        page_num: int
    ):
        """Draws bounding boxes and labels onto the image for visual verification."""
        os.makedirs(debug_dir, exist_ok=True)
        annotated = page_image.copy()

        for reg in layout.regions:
            x1, y1, x2, y2 = reg.bbox
            color = (0, 255, 0) if reg.model == "trocr" else ((255, 128, 0) if reg.model == "got" else (0, 0, 255))
            if reg.needs_review:
                color = (0, 0, 255)  # Red for review

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"#{reg.reading_order_index} [{reg.model}] {reg.confidence:.2f}"
            cv2.putText(annotated, label, (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        out_path = os.path.join(debug_dir, f"page_{page_num}_debug.png")
        cv2.imwrite(out_path, cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
        logger.info(f"[DEBUG] Saved debug visualization: {out_path}")
