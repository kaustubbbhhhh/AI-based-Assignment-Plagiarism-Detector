"""
Colab GPU Cloud Scanner Client
=================================
Connects your local system to your Google Colab T4 GPU API.
Processes PDF and image assignments in the cloud with zero load on your PC.

Usage:
    python colab_scanner.py path/to/assignment.pdf
    python colab_scanner.py path/to/photo.jpg
"""

import sys
import os
import time
import json
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Default configuration from your live Colab session
DEFAULT_API_URL = os.getenv("COLAB_API_URL", "https://divisibly-drinkable-upside.ngrok-free.dev/api/process-document")
DEFAULT_API_KEY = os.getenv("COLAB_API_KEY", "HgfKr9mcsNFfEfp2gVhGiF0EHAgyqLfw")


def scan_document(
    file_path: str,
    api_url: str = DEFAULT_API_URL,
    api_key: str = DEFAULT_API_KEY,
    output_dir: str = "."
) -> dict:
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return {}

    filename = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    print("\n" + "=" * 70)
    print(">>> PLAGIARISM & OCR SYSTEM - CLOUD GPU SCANNER")
    print("=" * 70)
    print(f"  Target File : {filename} ({file_size_mb:.2f} MB)")
    print(f"  Cloud Server: {api_url.split('/api')[0]}")
    print(f"  GPU Engine  : NVIDIA T4 (15 GB Cloud VRAM)")
    print("=" * 70)

    headers = {
        "X-API-Key": api_key
    }

    t0 = time.time()
    print("\n[1/2] Uploading document to Cloud GPU and running OCR + AI Analysis...")

    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            response = requests.post(api_url, headers=headers, files=files, timeout=600)

        elapsed = time.time() - t0

        if response.status_code != 200:
            print(f"\n[ERROR] Server returned HTTP {response.status_code}: {response.text}")
            return {}

        result = response.json()
        ai = result.get("ai_detection", {})
        extracted_text = result.get("extracted_text", "")

        print(f"[2/2] Processing completed in {elapsed:.2f} seconds!")

        # ── Display Results Dashboard ──
        print("\n" + "─" * 70)
        print("[+] SCAN & DETECTION DASHBOARD")
        print("─" * 70)
        print(f"  Classification Label : {ai.get('label', 'Unknown').upper()}")
        print(f"  AI Likelihood Score  : {ai.get('ai_score', 0)}%")
        print(f"  Detection Reasoning  : {ai.get('reasoning', '')}")

        metrics = ai.get("metrics", {})
        if metrics:
            print("\n  [Stylometric & Mathematical Indicators]")
            print(f"    - Total Words      : {metrics.get('total_words')}")
            print(f"    - Total Sentences  : {metrics.get('total_sentences')}")
            print(f"    - Lexical Richness : {metrics.get('lexical_richness')}")
            print(f"    - Math Density     : {metrics.get('math_density')}")

        print("\n" + "─" * 70)
        print("[*] EXTRACTED OCR TEXT PREVIEW (First 500 characters):")
        print("─" * 70)
        print(extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""))
        print("─" * 70)

        # ── Save Output Files ──
        out_json = os.path.join(output_dir, "colab_scan_report.json")
        out_txt = os.path.join(output_dir, "colab_extracted_text.txt")

        with open(out_json, "w", encoding="utf-8") as f_json:
            json.dump(result, f_json, indent=2, ensure_ascii=False)

        with open(out_txt, "w", encoding="utf-8") as f_txt:
            f_txt.write(extracted_text)

        print(f"\n[OK] Complete scan report saved to : {os.path.abspath(out_json)}")
        print(f"[OK] Full extracted text saved to  : {os.path.abspath(out_txt)}")

        return result

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to Google Colab API.")
        print("Please verify that your Google Colab notebook is currently running and the ngrok tunnel is active.")
        return {}
    except Exception as ex:
        print(f"\n[ERROR] Unexpected error during scan: {ex}")
        return {}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        # Interactive prompt if no file argument is passed
        print("=" * 70)
        print("Plagiarism & OCR Cloud Scanner")
        print("=" * 70)
        target_path = input("Enter path to PDF or Image file: ").strip().strip('"').strip("'")

    if not target_path:
        print("No file specified. Exiting.")
        sys.exit(1)

    scan_document(target_path)
