import sys
import os

# Add backend to path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.text_extraction import extract_text

def run_test(filepath):
    print(f"\n--- Testing Extraction for: {filepath} ---")
    
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return

    try:
        # Run the extraction layer
        result = extract_text(filepath)
        
        text = result.get("text", "")
        visual_hash = result.get("visual_hash")
        word_count = len(text.split())
        
        print(f"[SUCCESS] Extraction Complete!")
        print(f"Words Extracted: {word_count}")
        print(f"Visual Hash: {visual_hash if visual_hash else 'None (Not an image)'}")
        
        print("\n--- Extracted Text Preview (First 500 chars) ---")
        preview = text[:500].strip()
        print(preview + ("..." if len(text) > 500 else ""))
        print("--------------------------------------------------\n")
        
    except ValueError as ve:
         # This catches our Rejection Gate (Confidence < 65%)
         print(f"[REJECTED by System]: {ve}\n")
    except Exception as e:
        print(f"[FAILED] System Error: {e}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        run_test(filepath)
    else:
        print("Usage: python test_extraction.py <path_to_file>")
        print("Example: python test_extraction.py sample_image.jpg")
