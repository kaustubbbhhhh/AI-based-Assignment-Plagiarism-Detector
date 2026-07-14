"""
OCR Service.
Handles image pre-processing using OpenCV (shadow removal, perspective warping)
and text extraction using Google Cloud Vision API with a local EasyOCR fallback.
"""

import io
import os
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Global EasyOCR reader instance (lazy-loaded)
_easyocr_reader = None
# Global Google Cloud Vision client instance (lazy-loaded)
_vision_client = None
_vision_client_initialized = False

def get_easyocr_reader():
    """Lazy-load the EasyOCR Reader on CPU to prevent startup delay."""
    global _easyocr_reader
    if _easyocr_reader is None:
        logger.info("Initializing EasyOCR English Reader (gpu=False)...")
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        logger.info("EasyOCR Reader successfully initialized.")
    return _easyocr_reader

def get_vision_client():
    """Lazy-load the Google Cloud Vision client."""
    global _vision_client, _vision_client_initialized
    if not _vision_client_initialized:
        _vision_client_initialized = True
        # Check if the GCP environment variable is set
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            try:
                logger.info("Initializing Google Cloud Vision Client...")
                from google.cloud import vision
                _vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision Client successfully initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Cloud Vision client: {e}")
                _vision_client = None
        else:
            logger.info("GOOGLE_APPLICATION_CREDENTIALS not found in environment. Cloud Vision is disabled.")
            _vision_client = None
    return _vision_client

def remove_shadows(gray_img: np.ndarray) -> np.ndarray:
    """
    Remove uneven lighting and shadows from a grayscale image.
    Uses morphological opening to estimate background illumination and divides by it.
    """
    logger.debug("Applying shadow removal preprocessing...")
    dilated_img = cv2.dilate(gray_img, np.ones((7, 7), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - cv2.absdiff(gray_img, bg_img)
    normalized_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    return normalized_img

def get_perspective_corrected_image(img: np.ndarray) -> np.ndarray:
    """
    Detect document boundaries and apply a perspective transform to flatten/deskew the page.
    If no clear 4-corner document contour is found, falls back to standard grayscale.
    """
    logger.debug("Checking for document perspective correction...")
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
        logger.debug("No clear 4-corner document contour detected. Returning standard grayscale.")
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
    logger.info("Document contour detected! Applying perspective transform warp.")
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
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    
    return cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

def preprocess_image_for_ocr(image_path: str) -> np.ndarray:
    """
    Apply OpenCV transformations to clean the image before OCR.
    Steps: Perspective Correction -> Shadow Removal -> Bilateral Blur
    """
    logger.info(f"Pre-processing image for OCR: {image_path}")
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image at {image_path}")
        
    gray = get_perspective_corrected_image(img)
    shadow_free = remove_shadows(gray)
    denoised = cv2.bilateralFilter(shadow_free, 9, 75, 75)
    
    return denoised

def extract_text_from_image_local(image_path: str) -> dict:
    """
    Runs the local EasyOCR pipeline on an image file.
    (Used as a local offline fallback).
    """
    logger.info(f"Running local EasyOCR extraction on: {image_path}")
    try:
        processed_img = preprocess_image_for_ocr(image_path)
        reader = get_easyocr_reader()
        data = reader.readtext(processed_img)
        
        text_parts = []
        confidences = []
        
        for item in data:
            if len(item) >= 2:
                text = item[1].strip()
                if text:
                    text_parts.append(text)
                    conf = float(item[2]) * 100.0 if len(item) > 2 and item[2] is not None else 100.0
                    confidences.append(conf)
                    
        extracted_text = " ".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "text": extracted_text,
            "confidence": avg_confidence,
            "engine": "local_easyocr"
        }
    except Exception as e:
        logger.error(f"Local OCR fallback failed: {e}")
        raise

def extract_text_from_image(image_path: str) -> dict:
    """
    Tries to run the Google Cloud Vision API OCR.
    If it fails or if credentials are not configured, falls back to local EasyOCR.
    """
    visual_hash = compute_visual_hash(image_path)
    
    # 1. Attempt Cloud Vision
    client = get_vision_client()
    if client is not None:
        try:
            logger.info(f"Sending image to Google Cloud Vision API: {image_path}")
            
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
                
            from google.cloud import vision
            image = vision.Image(content=content)
            
            # Using document_text_detection (highly optimized for handwriting)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"GCP API Error: {response.error.message}")
                
            annotation = response.full_text_annotation
            extracted_text = annotation.text if annotation else ""
            
            # Extract word confidence scores
            confidences = []
            if annotation:
                for page in annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                confidences.append(word.confidence)
                                
            # Convert float (0.0-1.0) to percentage
            avg_confidence = (sum(confidences) / len(confidences) * 100.0) if confidences else 100.0
            
            logger.info(f"Cloud Vision OCR completed successfully. Avg Confidence: {avg_confidence:.2f}%")
            return {
                "text": extracted_text,
                "confidence": avg_confidence,
                "visual_hash": visual_hash,
                "engine": "google_cloud_vision"
            }
            
        except Exception as cloud_err:
            logger.warning(f"Google Cloud Vision OCR failed: {cloud_err}. Falling back to local EasyOCR.")
            
    # 2. Fallback to Local EasyOCR
    local_result = extract_text_from_image_local(image_path)
    local_result["visual_hash"] = visual_hash
    return local_result

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
