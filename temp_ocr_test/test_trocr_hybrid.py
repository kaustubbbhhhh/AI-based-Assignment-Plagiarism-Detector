import os
import sys
import time
import cv2
import numpy as np

# Add backend to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_path)

from services.ocr_service import preprocess_image_for_ocr

def run_hybrid_ocr():
    image_path = r"C:\Users\Kaustubh Raj\.gemini\antigravity\brain\4ca5b735-24f8-43d0-aa1d-b08f653dfc1e\media__1781000999869.jpg"
    print(f"Testing CRAFT (EasyOCR) + Microsoft TrOCR-Base on: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found at {image_path}")
        return

    # 1. Preprocess image using our OpenCV cleanup
    print("Preprocessing image (Shadow Removal + Perspective Correction)...")
    processed_img = preprocess_image_for_ocr(image_path)
    
    # Save a temporary copy of processed image for debug
    cv2.imwrite("temp_processed_ocr.jpg", processed_img)

    # 2. Initialize EasyOCR just for detection (CRAFT)
    print("Initializing EasyOCR for text line detection...")
    import easyocr
    detector = easyocr.Reader(['en'], gpu=False)

    # 3. Initialize Microsoft TrOCR-Base Handwriting Recognizer
    print("Loading Microsoft TrOCR-Base model from Hugging Face...")
    print("NOTE: This model is ~1.3GB. If it's not cached, it will download. Stand by...")
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    from PIL import Image
    
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
    
    # 4. Detect Text bounding boxes
    print("Detecting text bounding boxes...")
    # readtext with detail=1 returns (bbox, text, conf)
    # We will use this to get the crops
    ocr_results = detector.readtext(processed_img)
    
    # Sort bounding boxes top-to-bottom, left-to-right to read in order
    # Each bbox is [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
    # We will sort by y0 primarily, then x0
    ocr_results.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
    
    print(f"Detected {len(ocr_results)} text regions. Running TrOCR on each region...")
    
    h, w = processed_img.shape
    pil_img = Image.fromarray(processed_img).convert("RGB")
    
    extracted_lines = []
    
    start_time = time.time()
    for idx, (bbox, easy_text, easy_conf) in enumerate(ocr_results):
        # Get cropping coordinates
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        xmin, xmax = max(0, int(min(xs) - 4)), min(w, int(max(xs) + 4))
        ymin, ymax = max(0, int(min(ys) - 4)), min(h, int(max(ys) + 4))
        
        if (xmax - xmin) < 5 or (ymax - ymin) < 5:
            continue
            
        # Crop the text line
        cropped_line = pil_img.crop((xmin, ymin, xmax, ymax))
        
        # Recognize with TrOCR
        try:
            pixel_values = processor(images=cropped_line, return_tensors="pt").pixel_values
            generated_ids = model.generate(pixel_values)
            trocr_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            if trocr_text.strip():
                print(f"Line {idx+1:02d} | EasyOCR: '{easy_text}' ({easy_conf*100:.1f}%) | TrOCR: '{trocr_text}'")
                extracted_lines.append(trocr_text)
        except Exception as line_error:
            print(f"Error processing line {idx+1}: {line_error}")
            
    end_time = time.time()
    
    print("\n--- FINAL HYBRID OCR TEXT ---")
    print(" ".join(extracted_lines))
    print("-----------------------------")
    print(f"Recognition completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_hybrid_ocr()
