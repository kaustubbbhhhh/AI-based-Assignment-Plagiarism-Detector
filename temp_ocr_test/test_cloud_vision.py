import os
import sys
import time

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_path)

# Ensure log output is printed
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from services.ocr_service import extract_text_from_image

def main():
    image_path = r"C:\Users\Kaustubh Raj\.gemini\antigravity\brain\4ca5b735-24f8-43d0-aa1d-b08f653dfc1e\media__1781000999869.jpg"
    print(f"Testing OCR service interface: {image_path}")
    print("Checking file existence...")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file does not exist at {image_path}")
        return

    # Check if GCP credentials exist
    gcp_configured = "GOOGLE_APPLICATION_CREDENTIALS" in os.environ
    print(f"Is Google Cloud Vision credentials set in environment? {gcp_configured}")
    if not gcp_configured:
        print("Note: Credentials are NOT set. We expect the pipeline to gracefully fall back to local EasyOCR without throwing errors.")

    print("\nExecuting extract_text_from_image()...")
    start_time = time.time()
    try:
        result = extract_text_from_image(image_path)
        end_time = time.time()
        
        print("\n--- EXTRACTED OCR RESULT ---")
        print(f"Active Engine: {result.get('engine')}")
        print(f"Average Confidence: {result.get('confidence', 0):.2f}%")
        print(f"Visual Hash: {result.get('visual_hash', 'None')}")
        print(f"Total Processing Time: {end_time - start_time:.2f} seconds")
        print("\n--- Extracted Text Preview ---")
        print(result.get("text", "")[:400] + ("..." if len(result.get("text", "")) > 400 else ""))
        print("-----------------------------")
        print("[SUCCESS] The OCR service ran and handled the request properly!")
        
    except Exception as e:
        print(f"[FAILED] The system crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
