"""
OCR Service (TrOCR + Neural Vision)
=====================================
Handles image pre-processing using OpenCV and offline text extraction using:
  Primary:  CRAFT text line segmentation + Microsoft TrOCR (trocr-base-handwritten)
  Fallback: EasyOCR end-to-end recognition
  Fallback: Tesseract OCR

Pipeline for handwritten notebook photos:
  1. Preprocessing: perspective correction, deskew, shadow removal, adaptive threshold, denoise
  2. Line detection: CRAFT / morphological + projection profile segmentation
  3. Per-line recognition: TrOCR (GPU-accelerated when available)
"""

import io
import os
import cv2
import math
import numpy as np
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global lazy-loaded models
# ---------------------------------------------------------------------------
_trocr_processor = None
_trocr_model = None
_trocr_device = None
_trocr_initialized = False


# ---------------------------------------------------------------------------
# TrOCR Model Loading
# ---------------------------------------------------------------------------
def get_trocr_model():
    """Lazy-load the TrOCR handwritten model and processor (offline-first)."""
    global _trocr_processor, _trocr_model, _trocr_device, _trocr_initialized

    if _trocr_initialized:
        return _trocr_processor, _trocr_model, _trocr_device

    _trocr_initialized = True

    try:
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        _trocr_device = "cuda" if torch.cuda.is_available() else "cpu"

        # Check for locally fine-tuned model first
        custom_model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "trocr_finetuned")
        if os.path.exists(custom_model_dir) and os.path.exists(os.path.join(custom_model_dir, "config.json")):
            logger.info(f"Loading custom fine-tuned TrOCR model from {custom_model_dir} on {_trocr_device}...")
            _trocr_processor = TrOCRProcessor.from_pretrained(custom_model_dir)
            _trocr_model = VisionEncoderDecoderModel.from_pretrained(custom_model_dir)
        else:
            logger.info(f"Loading base TrOCR handwritten model on {_trocr_device}...")
            try:
                # Try offline cache first to avoid remote HTTP calls
                _trocr_processor = TrOCRProcessor.from_pretrained(
                    "microsoft/trocr-base-handwritten", local_files_only=True
                )
                _trocr_model = VisionEncoderDecoderModel.from_pretrained(
                    "microsoft/trocr-base-handwritten", local_files_only=True
                )
            except Exception:
                # Fallback to online download if cache is empty
                _trocr_processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
                _trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

        _trocr_model.to(_trocr_device)
        _trocr_model.eval()
        logger.info(f"TrOCR handwritten model loaded successfully on {_trocr_device}.")

    except Exception as e:
        logger.error(f"Failed to load TrOCR model: {e}")
        _trocr_processor = None
        _trocr_model = None

    return _trocr_processor, _trocr_model, _trocr_device




# ---------------------------------------------------------------------------
# Image Preprocessing (Enhanced for Handwritten Notebooks)
# ---------------------------------------------------------------------------
def remove_shadows(gray_img: np.ndarray) -> np.ndarray:
    """
    Remove uneven lighting and shadows from a grayscale image.
    Uses morphological opening to estimate background illumination.
    """
    dilated_img = cv2.dilate(gray_img, np.ones((7, 7), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - cv2.absdiff(gray_img, bg_img)
    normalized_img = cv2.normalize(
        diff_img, None, alpha=0, beta=255,
        norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1
    )
    return normalized_img


def deskew_image(gray_img: np.ndarray) -> np.ndarray:
    """
    Auto-correct rotation/skew using Hough Line Transform.
    Detects dominant line angles and rotates to straighten.
    """
    # Edge detection
    edges = cv2.Canny(gray_img, 50, 150, apertureSize=3)

    # Detect lines
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=100,
        minLineLength=gray_img.shape[1] // 4,  # at least 1/4 page width
        maxLineGap=10
    )

    if lines is None or len(lines) == 0:
        return gray_img

    # Calculate angles
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        # Only consider near-horizontal lines (text lines)
        if abs(angle) < 30:
            angles.append(angle)

    if not angles:
        return gray_img

    median_angle = np.median(angles)

    # Only correct if skew is meaningful (> 0.5 degrees)
    if abs(median_angle) < 0.5:
        return gray_img

    logger.info(f"Deskewing image by {median_angle:.1f} degrees")
    h, w = gray_img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(
        gray_img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def get_perspective_corrected_image(img: np.ndarray) -> np.ndarray:
    """
    Detect document boundaries and apply perspective transform to flatten the page.
    Falls back to standard grayscale if no clear 4-corner contour is found.
    """
    h, w = img.shape[:2]
    ratio = h / 500.0
    img_resized = cv2.resize(img, (int(w / ratio), 500))

    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    screen_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            area = cv2.contourArea(c)
            if area > (500 * (w / ratio) * 0.15):
                screen_cnt = approx
                break

    if screen_cnt is None:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    logger.info("Document contour detected. Applying perspective transform.")
    pts = screen_cnt.reshape(4, 2) * ratio

    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0], [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    return cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)


def preprocess_image_for_ocr(image_path: str) -> np.ndarray:
    """
    Full preprocessing pipeline for notebook photos:
      1. Perspective correction (flatten warped pages)
      2. Deskew (straighten rotated text)
      3. Shadow removal (normalize uneven lighting)
      4. Adaptive thresholding (enhance faint pencil/pen)
      5. Bilateral denoise (smooth while preserving edges)
    """
    logger.info(f"Pre-processing image for OCR: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image at {image_path}")

    # 1. Perspective correction
    gray = get_perspective_corrected_image(img)

    # 2. Deskew
    gray = deskew_image(gray)

    # 3. Shadow removal
    shadow_free = remove_shadows(gray)

    # 4. Adaptive threshold (better for handwriting than global threshold)
    # Use Gaussian adaptive — handles uneven ink density well
    adaptive = cv2.adaptiveThreshold(
        shadow_free, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=10
    )

    # 5. Light denoise (preserve handwriting strokes)
    denoised = cv2.bilateralFilter(adaptive, 5, 50, 50)

    return denoised


# ---------------------------------------------------------------------------
# Text Line Detection (for TrOCR)
# ---------------------------------------------------------------------------
def detect_text_lines(processed_img: np.ndarray, min_line_height: int = 15) -> list:
    """
    Detect individual text lines in a preprocessed grayscale/binary image.
    Uses morphological operations + horizontal projection profile.

    Returns:
        List of (y_start, y_end) tuples for each detected line, sorted top-to-bottom.
    """
    h, w = processed_img.shape[:2]

    # Ensure binary (inverted: text=white, background=black)
    _, binary = cv2.threshold(processed_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Dilate horizontally to connect characters into line blobs
    kernel_width = max(w // 8, 30)  # wide horizontal kernel
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
    dilated = cv2.dilate(binary, horizontal_kernel, iterations=2)

    # Small vertical dilation to merge close lines within same text line
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    dilated = cv2.dilate(dilated, vertical_kernel, iterations=1)

    # Horizontal projection profile (sum of white pixels per row)
    projection = np.sum(dilated, axis=1)

    # Threshold: a row is "text" if projection exceeds threshold
    threshold = np.max(projection) * 0.05
    is_text = projection > threshold

    # Find contiguous text regions
    lines = []
    in_line = False
    line_start = 0

    for y in range(h):
        if is_text[y] and not in_line:
            line_start = y
            in_line = True
        elif not is_text[y] and in_line:
            line_end = y
            line_height = line_end - line_start
            if line_height >= min_line_height:
                # Add small padding
                pad = max(3, line_height // 6)
                y_start = max(0, line_start - pad)
                y_end = min(h, line_end + pad)
                lines.append((y_start, y_end))
            in_line = False

    # Handle case where last line extends to bottom
    if in_line:
        line_height = h - line_start
        if line_height >= min_line_height:
            pad = max(3, line_height // 6)
            lines.append((max(0, line_start - pad), h))

    logger.info(f"Detected {len(lines)} text lines.")

    # Fallback: if no lines detected, treat entire image as one line
    if not lines:
        logger.warning("No text lines detected. Using full image as single line.")
        lines = [(0, h)]

    return lines


# ---------------------------------------------------------------------------
# TrOCR Recognition
# ---------------------------------------------------------------------------
def recognize_line_trocr(line_img: np.ndarray) -> tuple:
    """
    Recognize text in a single line image using TrOCR.

    Args:
        line_img: Grayscale/binary image of a single text line.

    Returns:
        (text, confidence) tuple.
    """
    import torch

    processor, model, device = get_trocr_model()
    if processor is None or model is None:
        return ("", 0.0)

    # Convert grayscale to RGB PIL Image (TrOCR expects RGB)
    if len(line_img.shape) == 2:
        line_img_rgb = cv2.cvtColor(line_img, cv2.COLOR_GRAY2RGB)
    else:
        line_img_rgb = line_img

    pil_img = Image.fromarray(line_img_rgb)

    # Process
    pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values
    pixel_values = pixel_values.to(device)

    with torch.no_grad():
        generated = model.generate(
            pixel_values,
            max_new_tokens=128,
            num_beams=4,
            early_stopping=True,
            return_dict_in_generate=True,
            output_scores=True,
        )

    # Decode
    text = processor.batch_decode(generated.sequences, skip_special_tokens=True)[0]
    text = text.strip()

    # Approximate confidence from sequence scores
    if hasattr(generated, 'sequences_scores') and generated.sequences_scores is not None:
        # sequences_scores is log-prob; convert to probability
        log_prob = generated.sequences_scores[0].item()
        confidence = min(100.0, max(0.0, math.exp(log_prob) * 100.0))
    else:
        confidence = 80.0  # default if scores unavailable

    return (text, confidence)


# ---------------------------------------------------------------------------
# Local OCR Pipeline (TrOCR — replaces EasyOCR)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# EasyOCR Reader Loading
# ---------------------------------------------------------------------------
_easyocr_reader = None
_easyocr_initialized = False

def get_easyocr_reader():
    """Lazy-load EasyOCR reader."""
    global _easyocr_reader, _easyocr_initialized
    if not _easyocr_initialized:
        _easyocr_initialized = True
        try:
            import easyocr
            import torch
            use_gpu = torch.cuda.is_available()
            logger.info(f"Initializing EasyOCR reader (GPU: {use_gpu})...")
            _easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
            logger.info("EasyOCR reader initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize EasyOCR: {e}")
            _easyocr_reader = None
    return _easyocr_reader


# ---------------------------------------------------------------------------
# Local OCR Pipeline (Hybrid CRAFT + TrOCR GPU Primary, EasyOCR Fallback)
# ---------------------------------------------------------------------------
def extract_text_from_image_local(image_path: str) -> dict:
    """
    Full local OCR pipeline for handwritten text and scanned documents:
      1. Primary: CRAFT text line segmentation + Microsoft TrOCR GPU recognition
      2. Fallback: EasyOCR end-to-end recognition
      3. Last Resort: Tesseract
    
    Returns:
        {"text": str, "confidence": float, "engine": str, "lines_detected": int}
    """
    logger.info(f"Running local OCR pipeline on: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image at {image_path}")

    h, w = img.shape[:2]
    reader = get_easyocr_reader()

    # ── 1. Primary: CRAFT line detection + Microsoft TrOCR recognition ──
    processor, trocr_model, trocr_device = get_trocr_model()
    if reader is not None and trocr_model is not None and processor is not None:
        try:
            logger.info("Executing Hybrid CRAFT + TrOCR handwritten pipeline...")
            horizontal_list, _ = reader.detect(img)
            bboxes = horizontal_list[0] if horizontal_list else []

            if bboxes:
                # Group and sort bounding boxes into reading lines
                def _group_boxes_into_lines(boxes, y_tol=24):
                    boxes = sorted(boxes, key=lambda b: (b[2], b[0]))
                    grouped = []
                    curr_line = []
                    for b in boxes:
                        if not curr_line:
                            curr_line.append(b)
                        else:
                            prev_y = (curr_line[-1][2] + curr_line[-1][3]) / 2
                            curr_y = (b[2] + b[3]) / 2
                            if abs(curr_y - prev_y) < y_tol:
                                curr_line.append(b)
                            else:
                                curr_line.sort(key=lambda b: b[0])
                                grouped.append(curr_line)
                                curr_line = [b]
                    if curr_line:
                        curr_line.sort(key=lambda b: b[0])
                        grouped.append(curr_line)
                    return grouped

                line_groups = _group_boxes_into_lines(bboxes)
                logger.info(f"CRAFT detected {len(bboxes)} text segments across {len(line_groups)} reading lines.")

                trocr_lines = []
                trocr_confs = []

                for group in line_groups:
                    line_words = []
                    line_word_confs = []
                    for box in group:
                        xmin, xmax, ymin, ymax = box
                        crop = img[max(0, ymin - 4):min(h, ymax + 4), max(0, xmin - 4):min(w, xmax + 4)]
                        if crop.shape[0] < 8 or crop.shape[1] < 8:
                            continue

                        text_str, conf_val = recognize_line_trocr(crop)
                        if text_str:
                            line_words.append(text_str)
                            line_word_confs.append(conf_val)

                    if line_words:
                        trocr_lines.append(" ".join(line_words))
                        if line_word_confs:
                            trocr_confs.append(sum(line_word_confs) / len(line_word_confs))

                extracted_text = "\n".join(trocr_lines)
                avg_confidence = (sum(trocr_confs) / len(trocr_confs)) if trocr_confs else 85.0
                
                if len(extracted_text.split()) >= 15:
                    logger.info(
                        f"TrOCR recognition complete: {len(trocr_lines)} lines, "
                        f"{len(extracted_text.split())} words, confidence: {avg_confidence:.1f}%"
                    )
                    return {
                        "text": extracted_text,
                        "confidence": round(avg_confidence, 1),
                        "engine": "trocr_handwritten",
                        "lines_detected": len(line_groups),
                        "lines_recognized": len(trocr_lines),
                    }
        except Exception as trocr_err:
            logger.warning(f"Hybrid TrOCR pipeline failed: {trocr_err}. Falling back to EasyOCR.")

    # ── 2. Fallback: EasyOCR standalone ───────────────────────────────
    if reader is not None:
        try:
            results = reader.readtext(image_path)
            if results:
                lines = []
                confs = []
                for bbox, text, prob in results:
                    text_str = text.strip()
                    if text_str:
                        lines.append(text_str)
                        confs.append(float(prob))

                extracted_text = "\n".join(lines)
                avg_conf = (sum(confs) / len(confs) * 100.0) if confs else 0.0
                scaled_confidence = min(98.0, max(avg_conf, 65.0 + (avg_conf * 0.35))) if (len(lines) > 5 and avg_conf > 25.0) else avg_conf

                return {
                    "text": extracted_text,
                    "confidence": round(scaled_confidence, 1),
                    "engine": "easyocr_handwritten",
                    "lines_detected": len(results),
                    "lines_recognized": len(lines),
                }
        except Exception as easy_err:
            logger.warning(f"EasyOCR fallback failed: {easy_err}. Trying Tesseract.")

    # ── 3. Last Resort: Tesseract ─────────────────────────────────────
    try:
        import pytesseract
        from PIL import Image
        tess_text = pytesseract.image_to_string(Image.open(image_path))
        return {
            "text": tess_text,
            "confidence": 75.0 if len(tess_text.split()) > 10 else 40.0,
            "engine": "tesseract_fallback",
            "lines_detected": len(tess_text.splitlines()),
            "lines_recognized": len(tess_text.splitlines()),
        }
    except Exception as e:
        raise ValueError(f"All OCR engines failed for {image_path}: {e}")


# ---------------------------------------------------------------------------
# Main Entry Point (Local TrOCR / EasyOCR / Tesseract Pipeline)
# ---------------------------------------------------------------------------
def extract_text_from_image(image_path: str) -> dict:
    """
    Extract text using the local neural OCR pipeline (TrOCR + EasyOCR fallback).
    Computes and attaches perceptual visual hash for duplicate detection.
    """
    visual_hash = compute_visual_hash(image_path)
    result = extract_text_from_image_local(image_path)
    result["visual_hash"] = visual_hash
    return result


# ---------------------------------------------------------------------------
# Visual Hash (unchanged)
# ---------------------------------------------------------------------------
def compute_visual_hash(image_path: str) -> str:
    """
    Compute a perceptual hash (dHash) for an image.
    Used for visual plagiarism detection (detecting identical photos).
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        hash_value = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
        return f"{hash_value:016x}"
    except Exception as e:
        logger.error(f"Visual hashing failed for {image_path}: {e}")
        return None
