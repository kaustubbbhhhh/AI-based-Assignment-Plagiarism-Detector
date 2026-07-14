"""
Text extraction service.
Extracts raw text from uploaded PDF, DOCX, TXT, and Image files.
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
            # Direct image upload
            ocr_result = extract_text_from_image(filepath)
            _check_ocr_confidence(ocr_result)
            return {"text": ocr_result["text"], "visual_hash": ocr_result.get("visual_hash")}
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Text extraction failed for {filepath}: {e}")
        raise


def _check_ocr_confidence(ocr_result: dict):
    """Rejection gate for low quality images."""
    confidence = ocr_result.get("confidence", 0)
    if confidence < 65 and len(ocr_result.get("text", "").split()) > 10:
        logger.warning(f"OCR Confidence too low ({confidence:.2f}%). Rejecting submission.")
        raise ValueError(f"Image quality too low (Confidence: {confidence:.2f}%). Please upload a clearer photo.")


def _extract_pdf_hybrid(filepath: str) -> str:
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
        return {"text": digital_text, "visual_hash": None}
        
    # 2. Fallback to OCR for Scanned PDFs
    logger.info(f"PDF digital text too low ({word_count} words). Falling back to OCR Vision pipeline.")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Convert PDF pages to images
        images = convert_from_path(filepath, output_folder=temp_dir, fmt="jpeg")
        
        ocr_text_parts = []
        confidences = []
        
        for i, image in enumerate(images):
            # Save the image temporarily so OpenCV can read it
            temp_img_path = os.path.join(temp_dir, f"page_{i}.jpg")
            image.save(temp_img_path, "JPEG")
            
            # Run OCR
            result = extract_text_from_image(temp_img_path)
            ocr_text_parts.append(result["text"])
            confidences.append(result["confidence"])
            
        final_text = "\n".join(ocr_text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        _check_ocr_confidence({"text": final_text, "confidence": avg_confidence})
        
        # We can't easily hash a multi-page PDF visually into one hash, so we omit it or hash first page.
        # For now, visual hash is primarily for single image uploads.
        return {"text": final_text, "visual_hash": None}


def _extract_docx(filepath: str) -> dict:
    """Extract text from a DOCX file using python-docx."""
    doc = Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return {"text": text, "visual_hash": None}


def _extract_txt(filepath: str) -> dict:
    """Read a plain text file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return {"text": text, "visual_hash": None}
