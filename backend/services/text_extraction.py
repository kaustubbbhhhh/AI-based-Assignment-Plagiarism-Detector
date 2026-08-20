"""
Text extraction service.
Extracts raw text from uploaded PDF, DOCX, TXT, and Image files (JPG, JPEG, PNG).
Includes a hybrid fallback: if a PDF contains < 20 words, it assumes it is an image-based PDF
and converts the pages to images for OCR extraction.
"""

import os
import logging
import tempfile
from PyPDF2 import PdfReader
from docx import Document
from pdf2image import convert_from_path
from .ocr_service import extract_text_from_image

logger = logging.getLogger(__name__)


def extract_text(filepath: str) -> dict:
    """
    Extract text from a file based on its extension.
    Supported: .pdf, .docx, .doc, .txt, .png, .jpg, .jpeg
    Returns:
        dict: {
            "text": str,
            "visual_hash": Optional[str],
            "ocr_score": float (0-100),
            "ocr_status": str,
            "source": str
        }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".pdf":
            return _extract_pdf_hybrid(filepath)
        elif ext in (".docx", ".doc"):
            return _extract_docx(filepath)
        elif ext == ".txt":
            return _extract_txt(filepath)
        elif ext in (".png", ".jpg", ".jpeg"):
            # Direct image upload (JPG / PNG / JPEG)
            ocr_result = extract_text_from_image(filepath)
            _check_ocr_confidence(ocr_result)
            confidence = round(ocr_result.get("confidence", 0.0), 1)
            return {
                "text": ocr_result["text"],
                "visual_hash": ocr_result.get("visual_hash"),
                "ocr_score": confidence,
                "ocr_status": "Accepted - High Legibility" if confidence >= 65 else "Low Quality",
                "source": ocr_result.get("engine", "ocr_vision")
            }
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Text extraction failed for {filepath}: {e}")
        raise


def _check_ocr_confidence(ocr_result: dict):
    """Rejection gate for low quality images (< 50% confidence with sparse text)."""
    confidence = ocr_result.get("confidence", 0)
    text_words = len(ocr_result.get("text", "").split())
    if confidence < 50 and text_words < 15:
        logger.warning(f"OCR Confidence too low ({confidence:.2f}%). Rejecting submission.")
        raise ValueError(
            f"Image quality/legibility too low (Score: {confidence:.1f}%). "
            f"Threshold is 50%. Please upload a clearer, well-lit photo of your assignment."
        )


def _extract_pdf_hybrid(filepath: str) -> dict:
    """
    Extract text from a PDF. If the digital text is less than 20 words,
    assume it's a scanned/photo PDF and fall back to OCR.
    """
    reader = PdfReader(filepath)
    text_parts = []
    
    # 1. Try digital extraction
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
            
    digital_text = "\n".join(text_parts)
    word_count = len(digital_text.split())
    
    if word_count >= 20:
        logger.info(f"PDF digital extraction successful ({word_count} words).")
        return {
            "text": digital_text,
            "visual_hash": None,
            "ocr_score": 100.0,
            "ocr_status": "Accepted - Digital Verification",
            "source": "pdf_digital"
        }
        
    # 2. Fallback to OCR for Scanned PDFs
    logger.info(f"PDF digital text too low ({word_count} words). Falling back to OCR Vision pipeline.")
    
    ocr_text_parts = []
    confidences = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Try PyMuPDF (fitz) first, fallback to pdf2image
        rendered = False
        try:
            import fitz
            doc = fitz.open(filepath)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=150)
                temp_img_path = os.path.join(temp_dir, f"page_{i}.jpg")
                pix.save(temp_img_path)
                result = extract_text_from_image(temp_img_path)
                if result.get("text"):
                    ocr_text_parts.append(result["text"])
                if "confidence" in result:
                    confidences.append(result["confidence"])
            rendered = True
        except Exception as fitz_err:
            logger.warning(f"PyMuPDF rendering failed ({fitz_err}), falling back to pdf2image.")

        if not rendered:
            images = convert_from_path(filepath, output_folder=temp_dir, fmt="jpeg")
            for i, image in enumerate(images):
                temp_img_path = os.path.join(temp_dir, f"page_{i}.jpg")
                image.save(temp_img_path, "JPEG")
                result = extract_text_from_image(temp_img_path)
                if result.get("text"):
                    ocr_text_parts.append(result["text"])
                if "confidence" in result:
                    confidences.append(result["confidence"])
        
        final_text = "\n\n".join(ocr_text_parts)
        avg_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0
        
        _check_ocr_confidence({"text": final_text, "confidence": avg_confidence})
        
        return {
            "text": final_text,
            "visual_hash": None,
            "ocr_score": avg_confidence,
            "ocr_status": "Accepted - High Legibility" if avg_confidence >= 60 else "Accepted - Scanned Document",
            "source": "pdf_scanned_ocr"
        }


def _extract_docx(filepath: str) -> dict:
    """Extract text from a DOCX file using python-docx."""
    doc = Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return {
        "text": text,
        "visual_hash": None,
        "ocr_score": 100.0,
        "ocr_status": "Accepted - Digital Verification",
        "source": "docx_digital"
    }


def _extract_txt(filepath: str) -> dict:
    """Read a plain text file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return {
        "text": text,
        "visual_hash": None,
        "ocr_score": 100.0,
        "ocr_status": "Accepted - Digital Verification",
        "source": "txt_digital"
    }
