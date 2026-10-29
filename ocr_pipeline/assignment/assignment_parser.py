"""
Assignment Parser.
Converts layout-ordered TextRegions into structured Assignment documents,
extracting student metadata, subject, question numbers, prompts, and answers.
"""

import re
import logging
from typing import List, Dict, Any, Optional

from ..schemas.ocr_schema import (
    TextRegion,
    PageLayout,
    AssignmentDocument,
    DocumentMetadata,
    StudentMetadata,
    AssignmentSection,
    AssignmentSubpart,
    ContentType,
)

logger = logging.getLogger(__name__)


class AssignmentParser:
    # Regex patterns for header & metadata discovery
    NAME_PATTERNS = [
        re.compile(r"(?:Name|Student\s*Name)\s*[:\-]\s*([A-Za-z\s\.\,\'\-]+)", re.IGNORECASE),
        re.compile(r"^Name\s+([A-Za-z\s\.\'\-]+)", re.IGNORECASE),
    ]
    ID_PATTERNS = [
        re.compile(r"(?:Roll\s*(?:No|Num|Number)?|Student\s*ID|Reg\s*(?:No)?|ID)\s*[:\-]\s*([A-Za-z0-9\-_/]+)", re.IGNORECASE),
    ]
    SUBJECT_PATTERNS = [
        re.compile(r"(?:Subject|Course|Module)\s*[:\-]\s*([A-Za-z0-9\s\-_]+)", re.IGNORECASE),
    ]
    TITLE_PATTERNS = [
        re.compile(r"(Assignment\s*[-#:]?\s*\d+|Homework\s*[-#:]?\s*\d+|Problem\s*Set\s*[-#:]?\s*\d+|Lab\s*Report\s*[-#:]?\s*\d+)", re.IGNORECASE),
    ]

    # Regex patterns for Question boundaries
    QUESTION_PATTERNS = [
        # "Question 1:", "Ques 1.", "Q.1", "Q1)", "Problem 2."
        re.compile(r"^[\#\*\s]*(?:Question|Ques|Q\.?|Problem)\s*([0-9]+|[A-Z])\s*[\.\:\-\)]?\s*(.*)", re.IGNORECASE),
        re.compile(r"^[\#\*\s]*(?:Question|Ques|Q\.?|Problem)\s*([0-9]+|[A-Z])\s*$", re.IGNORECASE),
        # Numbered list: "1. What is...", "2) Explain..."
        re.compile(r"^[\#\*\s]*([0-9]{1,2})\s*[\.\:\)]\s+(.*)"),
        # Subquestion or bracketed prefix: "[a]", "(a)", "a)"
        re.compile(r"^[\#\*\s]*\[?([0-9]+|[a-zA-Z])\]?\s*[\.\:\)]\s+(.*)"),
    ]

    # Subquestion patterns: "(a)", "(b)", "i)", "ii.", "[a]"
    SUBPART_PATTERNS = [
        re.compile(r"^[\#\*\s]*\(([a-zA-Z]|[ivxIVX]+)\)\s*(.*)"),
        re.compile(r"^[\#\*\s]*\[([a-zA-Z]|[ivxIVX]+)\]\s*(.*)"),
        re.compile(r"^[\#\*\s]*([a-zA-Z]|[ivxIVX]+)\)\s+(.*)"),
    ]

    # Explicit Answer indicators
    ANSWER_PREFIX_PATTERNS = [
        re.compile(r"^(?:Ans(?:wer)?|Solution|Soln)\s*[:\-]\s*(.*)", re.IGNORECASE),
    ]

    def parse(self, pages: List[PageLayout]) -> AssignmentDocument:
        """
        Parse multi-page document layout into a structured AssignmentDocument.

        Args:
            pages: List of PageLayout objects ordered by page number.

        Returns:
            AssignmentDocument schema.
        """
        all_regions: List[TextRegion] = []
        for page in pages:
            all_regions.extend(page.regions)

        # 1. Extract metadata from header/top regions
        metadata = self._extract_metadata(all_regions, total_pages=len(pages))

        # 2. Extract Question & Answer sections
        sections = self._extract_sections(all_regions)

        # 3. Overall confidence score
        if sections:
            overall_conf = round(float(sum(s.confidence for s in sections) / len(sections)), 3)
        elif all_regions:
            overall_conf = round(float(sum(r.confidence for r in all_regions) / len(all_regions)), 3)
        else:
            overall_conf = 0.0

        metadata.overall_confidence = overall_conf

        doc = AssignmentDocument(
            document=metadata,
            sections=sections,
            pages=pages,
            processing_summary={
                "total_pages": len(pages),
                "total_regions": len(all_regions),
                "sections_extracted": len(sections),
                "high_confidence_ratio": round(
                    float(sum(1 for r in all_regions if r.confidence >= 0.80) / max(1, len(all_regions))), 2
                ),
                "review_required_regions": sum(1 for r in all_regions if r.needs_review)
            }
        )

        logger.info(f"[PARSER] Completed assignment parsing: {len(sections)} sections identified.")
        return doc

    def _extract_metadata(self, regions: List[TextRegion], total_pages: int) -> DocumentMetadata:
        """Extract title, student name, ID, and subject from initial document regions."""
        doc_meta = DocumentMetadata(pages=total_pages, type="assignment")
        student = StudentMetadata()

        # Inspect regions from the top portion of the first page
        top_regions = [r for r in regions if r.page == 1][:8]

        for reg in top_regions:
            text = reg.text.strip()
            if not text:
                continue

            # Student Name
            if not student.name:
                for pat in self.NAME_PATTERNS:
                    match = pat.search(text)
                    if match:
                        student.name = match.group(1).strip()
                        break

            # Roll / Student ID
            if not student.roll_number:
                for pat in self.ID_PATTERNS:
                    match = pat.search(text)
                    if match:
                        student.roll_number = match.group(1).strip()
                        break

            # Subject
            if not student.subject:
                for pat in self.SUBJECT_PATTERNS:
                    match = pat.search(text)
                    if match:
                        student.subject = match.group(1).strip()
                        doc_meta.subject = student.subject
                        break

            # Assignment Title
            if not doc_meta.title:
                for pat in self.TITLE_PATTERNS:
                    match = pat.search(text)
                    if match:
                        doc_meta.title = match.group(1).strip()
                        break

        # Fallback title if top line is prominent
        if not doc_meta.title and top_regions:
            first_text = top_regions[0].text.strip()
            if len(first_text) < 50 and not any(kw in first_text.lower() for kw in ["name", "roll", "date"]):
                doc_meta.title = first_text

        doc_meta.student_info = student
        return doc_meta

    def _extract_sections(self, regions: List[TextRegion]) -> List[AssignmentSection]:
        """Group regions into coherent Question and Answer sections."""
        sections: List[AssignmentSection] = []
        current_section: Optional[AssignmentSection] = None
        in_answer = False
        section_idx = 1

        for reg in regions:
            text = reg.text.strip()
            if not text:
                continue

            # Check if this text begins a new Question
            matched_q_num = None
            q_prompt = None

            for pat in self.QUESTION_PATTERNS:
                m = pat.match(text)
                if m:
                    matched_q_num = m.group(1)
                    q_prompt = m.group(2).strip() if len(m.groups()) > 1 else ""
                    break

            if matched_q_num is not None:
                # Finalize previous section if existing
                if current_section is not None:
                    current_section.answer = current_section.answer.strip()
                    sections.append(current_section)

                # Start new section
                current_section = AssignmentSection(
                    section_id=f"sec_{section_idx:03d}",
                    question_number=str(matched_q_num),
                    question=q_prompt or text,
                    answer="",
                    page=reg.page,
                    content_type=reg.content_type,
                    confidence=reg.confidence,
                    source_region_ids=[reg.region_id]
                )
                in_answer = bool(q_prompt and len(q_prompt) > 20)  # If prompt already captured, next text is answer
                section_idx += 1
                continue

            # Check if text is an explicit answer starter ("Ans: ...")
            matched_ans = False
            for pat in self.ANSWER_PREFIX_PATTERNS:
                m = pat.match(text)
                if m:
                    matched_ans = True
                    ans_text = m.group(1).strip()
                    if current_section is not None:
                        in_answer = True
                        if ans_text:
                            current_section.answer += (ans_text + "\n")
                        current_section.source_region_ids.append(reg.region_id)
                    break

            if matched_ans:
                continue

            # Check for subquestions: "(a)", "1(b)"
            for sub_pat in self.SUBPART_PATTERNS:
                m = sub_pat.match(text)
                if m and current_section is not None:
                    sub_id = m.group(1)
                    sub_text = m.group(2).strip()
                    current_section.subparts.append(AssignmentSubpart(
                        subpart_id=sub_id,
                        question_text=sub_text or text,
                        confidence=reg.confidence
                    ))
                    break

            # If inside an existing section, append text to question or answer
            if current_section is not None:
                current_section.source_region_ids.append(reg.region_id)
                # Combine confidences
                current_section.confidence = round((current_section.confidence + reg.confidence) / 2.0, 3)

                if in_answer:
                    # Append to answer body
                    if reg.content_type in [ContentType.FORMULA, ContentType.TABLE]:
                        current_section.answer += f"\n{text}\n"
                    else:
                        current_section.answer += f"{text} "
                else:
                    # Still expanding question prompt
                    if len(current_section.question) < 120 and not text.endswith("?"):
                        current_section.question += f" {text}"
                    else:
                        in_answer = True
                        current_section.answer += f"{text} "
            else:
                # Pre-question text (e.g. general assignment instructions or unnumbered content)
                pass

        # Append final section
        if current_section is not None:
            current_section.answer = current_section.answer.strip()
            sections.append(current_section)

        # Fallback: If no explicit question headers were matched, package content into a default section
        if not sections and regions:
            body_regions = [r for r in regions if r.text.strip()]
            if body_regions:
                combined_text = "\n".join(r.text.strip() for r in body_regions)
                sections.append(AssignmentSection(
                    section_id="sec_001",
                    question_number="1",
                    question=body_regions[0].text.strip()[:100],
                    answer=combined_text,
                    page=body_regions[0].page,
                    content_type=body_regions[0].content_type,
                    confidence=round(sum(r.confidence for r in body_regions) / len(body_regions), 3),
                    source_region_ids=[r.region_id for r in body_regions]
                ))

        return sections
