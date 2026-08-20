"""
Prepare OCR Fine-Tuning Dataset from Existing Submissions and Scans
===================================================================
Extracts line/text crops from unique scanned documents and images.
"""

import os
import glob
import hashlib
import cv2
import fitz  # PyMuPDF
import numpy as np
import pandas as pd
import easyocr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "ocr_dataset")
IMAGES_DIR = os.path.join(DATASET_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

print("Initializing EasyOCR reader for line segmentation & auto-labeling...", flush=True)
reader = easyocr.Reader(['en'], gpu=False)

records = []
line_counter = 0


def get_file_hash(path):
    """Compute MD5 hash to deduplicate uploaded copies."""
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def process_image(img_bgr, source_name):
    global line_counter
    if img_bgr is None or img_bgr.size == 0:
        return

    h, w = img_bgr.shape[:2]

    try:
        results = reader.readtext(img_bgr)
    except Exception as e:
        print(f"  Warning: Error reading image from {source_name}: {e}", flush=True)
        return

    saved_for_this = 0
    for bbox, text, prob in results:
        text_str = text.strip()
        if len(text_str) < 3:
            continue

        (tl, tr, br, bl) = bbox
        x_min = max(0, int(min(tl[0], bl[0])) - 4)
        y_min = max(0, int(min(tl[1], tr[1])) - 4)
        x_max = min(w, int(max(tr[0], br[0])) + 4)
        y_max = min(h, int(max(bl[1], br[1])) + 4)

        crop_w = x_max - x_min
        crop_h = y_max - y_min

        if crop_w > 35 and crop_h > 14:
            crop = img_bgr[y_min:y_max, x_min:x_max]
            line_filename = f"line_{line_counter:05d}.png"
            crop_path = os.path.join(IMAGES_DIR, line_filename)
            cv2.imwrite(crop_path, crop)

            records.append({
                "file_name": f"images/{line_filename}",
                "text": text_str,
                "confidence": round(float(prob), 4),
                "source": source_name
            })
            line_counter += 1
            saved_for_this += 1

    print(f"  --> Extracted {saved_for_this} line crops from {source_name}", flush=True)


def process_pdf(pdf_path):
    print(f"\nProcessing PDF: {os.path.basename(pdf_path)}...", flush=True)
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) if pix.n >= 3 else img_np
            process_image(img_bgr, f"{os.path.basename(pdf_path)}_page_{i+1}")
    except Exception as e:
        print(f"  Error processing PDF {pdf_path}: {e}", flush=True)


def main():
    print("=" * 60, flush=True)
    print("Starting OCR Training Dataset Extraction", flush=True)
    print("=" * 60, flush=True)

    seen_hashes = set()

    # 1. Collect unique PDF files
    pdf_candidates = [
        os.path.join(os.path.dirname(BASE_DIR), "Scan document20260813_183154.pdf"),
        os.path.join(BASE_DIR, "Scan document20260813_183154.pdf"),
    ]
    pdf_candidates.extend(glob.glob(os.path.join(BASE_DIR, "uploads", "*.pdf")))

    for pdf_path in pdf_candidates:
        if os.path.exists(pdf_path):
            f_hash = get_file_hash(pdf_path)
            if f_hash not in seen_hashes:
                seen_hashes.add(f_hash)
                process_pdf(pdf_path)

    # 2. Collect unique Image files
    img_candidates = [
        os.path.join(BASE_DIR, "test_image_1.jpg"),
        os.path.join(BASE_DIR, "test_image_2.jpg"),
        os.path.join(os.path.dirname(BASE_DIR), "temp_processed_ocr.jpg"),
    ]
    img_candidates.extend(glob.glob(os.path.join(BASE_DIR, "uploads", "*.jpg")))
    img_candidates.extend(glob.glob(os.path.join(BASE_DIR, "uploads", "*.jpeg")))
    img_candidates.extend(glob.glob(os.path.join(BASE_DIR, "uploads", "*.png")))

    for img_path in img_candidates:
        if os.path.exists(img_path):
            f_hash = get_file_hash(img_path)
            if f_hash not in seen_hashes:
                seen_hashes.add(f_hash)
                print(f"\nProcessing Image: {os.path.basename(img_path)}...", flush=True)
                img_bgr = cv2.imread(img_path)
                process_image(img_bgr, os.path.basename(img_path))

    # Save to CSV
    if records:
        df = pd.DataFrame(records)
        csv_path = os.path.join(DATASET_DIR, "metadata.csv")
        df.to_csv(csv_path, index=False)
        print("\n" + "=" * 60, flush=True)
        print(f"[SUCCESS] Prepared {len(records)} line crops in: {IMAGES_DIR}", flush=True)
        print(f"[SUCCESS] Metadata saved to: {csv_path}", flush=True)
        print("=" * 60, flush=True)
    else:
        print("\n[WARNING] No images or scanned PDFs found to extract lines from.", flush=True)


if __name__ == "__main__":
    main()
