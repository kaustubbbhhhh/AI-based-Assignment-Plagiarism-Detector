"""
End-to-end test: Run handwritten assignment images through the full
OCR → AI Detection pipeline.

Usage:
    python test_pipeline_images.py <image1> [image2] ...
"""

import sys
import os
import json
import time

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env so GOOGLE_APPLICATION_CREDENTIALS is set
from dotenv import load_dotenv
load_dotenv()

from services.text_extraction import extract_text
from services.ai_detection import analyze_ai_content
from services.plagiarism import check_plagiarism
from services.ocr_service import compute_visual_hash


def run_full_pipeline(image_path: str):
    """Run a single image through the complete pipeline."""
    print(f"\n{'='*70}")
    print(f"  PROCESSING: {os.path.basename(image_path)}")
    print(f"{'='*70}")

    if not os.path.exists(image_path):
        print(f"  [ERROR] File not found: {image_path}")
        return None

    result = {
        "file": os.path.basename(image_path),
        "stages": {}
    }

    # ─── STAGE 1: OCR / Text Extraction ───────────────────────────────
    print(f"\n  ── STAGE 1: OCR Text Extraction ──")
    try:
        t0 = time.time()
        extraction = extract_text(image_path)
        t1 = time.time()

        text = extraction.get("text", "")
        visual_hash = extraction.get("visual_hash")
        word_count = len(text.split())

        print(f"     ✅ Extraction PASSED")
        print(f"     Words Extracted : {word_count}")
        print(f"     Visual Hash     : {visual_hash or 'N/A'}")
        print(f"     Time            : {t1 - t0:.2f}s")
        print(f"\n     ── Text Preview (first 600 chars) ──")
        preview = text[:600].strip()
        for line in preview.split('\n'):
            print(f"     │ {line}")
        if len(text) > 600:
            print(f"     │ ... ({len(text) - 600} more chars)")
        print(f"     └{'─'*50}")

        result["stages"]["ocr"] = {
            "status": "PASS",
            "word_count": word_count,
            "visual_hash": visual_hash,
            "time_sec": round(t1 - t0, 2),
            "text_preview": text[:300]
        }

    except ValueError as ve:
        print(f"     ❌ REJECTED by confidence gate: {ve}")
        result["stages"]["ocr"] = {"status": "REJECTED", "reason": str(ve)}
        return result
    except Exception as e:
        print(f"     ❌ FAILED: {e}")
        result["stages"]["ocr"] = {"status": "ERROR", "reason": str(e)}
        return result

    # ─── STAGE 2: AI Content Detection ────────────────────────────────
    print(f"\n  ── STAGE 2: AI Content Detection (Two-Layer) ──")
    try:
        t0 = time.time()
        ai_result = analyze_ai_content(text)
        t1 = time.time()

        ai_score = ai_result.get("ai_score", 0)
        label = ai_result.get("label", "Unknown")
        confidence = ai_result.get("confidence", 0)
        reasoning = ai_result.get("reasoning", "")
        decision_basis = ai_result.get("decision_basis", "")

        # Color-coded label
        if label == "Original":
            status_icon = "🟢"
        elif label == "AI-generated":
            status_icon = "🔴"
        else:
            status_icon = "🟡"

        print(f"     {status_icon} Verdict       : {label}")
        print(f"     AI Score       : {ai_score:.2f}%")
        print(f"     Confidence     : {confidence:.2f}%")
        print(f"     Decision Basis : {decision_basis}")
        print(f"     Reasoning      : {reasoning}")
        print(f"     Time           : {t1 - t0:.2f}s")

        # Show layer details if available
        l1 = ai_result.get("layer1_stats")
        l2 = ai_result.get("layer2_semantics")
        if l1:
            print(f"\n     Layer 1 (Statistical):")
            print(f"       Likelihood  : {l1.get('statistical_ai_likelihood', 'N/A')}%")
            print(f"       Pattern     : {l1.get('pattern_type', 'N/A')}")
            print(f"       Confidence  : {l1.get('confidence', 'N/A')}%")
        if l2:
            print(f"\n     Layer 2 (Semantic):")
            print(f"       Likelihood  : {l2.get('final_ai_likelihood', 'N/A')}%")
            print(f"       Alignment   : {l2.get('signal_alignment', 'N/A')}")
            print(f"       Confidence  : {l2.get('confidence', 'N/A')}%")

        result["stages"]["ai_detection"] = {
            "status": "PASS",
            "label": label,
            "ai_score": ai_score,
            "confidence": confidence,
            "reasoning": reasoning,
            "time_sec": round(t1 - t0, 2)
        }

    except Exception as e:
        print(f"     ❌ FAILED: {e}")
        result["stages"]["ai_detection"] = {"status": "ERROR", "reason": str(e)}

    # ─── STAGE 3: Visual Hash Comparison ──────────────────────────────
    print(f"\n  ── STAGE 3: Visual Hash (Duplicate Image Check) ──")
    hash1 = compute_visual_hash(image_path)
    if hash1:
        print(f"     Hash: {hash1}")
        result["stages"]["visual_hash"] = {"status": "PASS", "hash": hash1}
    else:
        print(f"     ⚠️  Hash computation failed")
        result["stages"]["visual_hash"] = {"status": "WARN", "hash": None}

    return result


def compare_visual_hashes(results):
    """Compare visual hashes between images to detect duplicate submissions."""
    hashes = {}
    for r in results:
        if r and r["stages"].get("visual_hash", {}).get("hash"):
            h = r["stages"]["visual_hash"]["hash"]
            hashes.setdefault(h, []).append(r["file"])

    print(f"\n{'='*70}")
    print(f"  CROSS-IMAGE ANALYSIS")
    print(f"{'='*70}")

    duplicates_found = False
    for h, files in hashes.items():
        if len(files) > 1:
            duplicates_found = True
            print(f"  🔴 DUPLICATE DETECTED! Same visual hash for: {', '.join(files)}")
            print(f"     Hash: {h}")

    if not duplicates_found:
        print(f"  🟢 No visual duplicates detected between images.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline_images.py <image1.jpg> [image2.jpg] ...")
        sys.exit(1)

    image_paths = sys.argv[1:]
    print(f"\n{'#'*70}")
    print(f"  OCR + AI VERIFICATION PIPELINE TEST")
    print(f"  Images to process: {len(image_paths)}")
    print(f"{'#'*70}")

    all_results = []
    for img_path in image_paths:
        result = run_full_pipeline(img_path)
        all_results.append(result)

    # Cross-compare if multiple images
    if len(all_results) > 1:
        compare_visual_hashes(all_results)

    # Summary table
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  {'File':<30} {'OCR':<12} {'Words':<8} {'AI Label':<15} {'AI Score':<10}")
    print(f"  {'─'*28}   {'─'*10}   {'─'*6}   {'─'*13}   {'─'*8}")
    for r in all_results:
        if r is None:
            continue
        fname = r["file"][:28]
        ocr_status = r["stages"].get("ocr", {}).get("status", "N/A")
        words = r["stages"].get("ocr", {}).get("word_count", "-")
        ai_label = r["stages"].get("ai_detection", {}).get("label", "N/A")
        ai_score = r["stages"].get("ai_detection", {}).get("ai_score", "-")
        ai_score_str = f"{ai_score:.1f}%" if isinstance(ai_score, (int, float)) else ai_score
        print(f"  {fname:<30} {ocr_status:<12} {str(words):<8} {ai_label:<15} {ai_score_str:<10}")

    print(f"\n{'#'*70}")
    print(f"  PIPELINE TEST COMPLETE")
    print(f"{'#'*70}\n")
