import os
import sys

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_path)

from services.ocr_service import extract_text_from_image

def main():
    image_path = r"C:\Users\Kaustubh Raj\.gemini\antigravity\brain\4ca5b735-24f8-43d0-aa1d-b08f653dfc1e\media__1781000999869.jpg"
    print(f"Testing OCR on image: {image_path}")
    print("Checking file existence...")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file does not exist at {image_path}")
        return

    print("Running OCR Pipeline (OpenCV Preprocessing -> PyTesseract -> Visual Hash)...")
    try:
        result = extract_text_from_image(image_path)
        print("\n--- OCR RESULTS ---")
        print(f"Average Confidence: {result.get('confidence', 0):.2f}%")
        print(f"Visual Hash: {result.get('visual_hash', 'None')}")
        print("\n--- Extracted Text ---")
        print(result.get("text", ""))
        print("----------------------")
    except Exception as e:
        print(f"[ERROR] OCR execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
