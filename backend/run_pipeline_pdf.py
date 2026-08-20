"""
Run the full detection pipeline on Scan document20260813_183154.pdf.
Stages:
  1. OCR & Text Extraction (PyMuPDF + Local OCR / EasyOCR + TrOCR)
  2. Subject & Curriculum Relevance Validation
  3. Two-Layer AI Detection Engine (DistilGPT-2 + Stylometrics + Random Forest)
  4. Peer Plagiarism Detection (TF-IDF Cosine Similarity)
  5. Forensic Data Mining Metrics (Stylometrics, Lexical Diversity)
  6. Database Persistence & Submission Status Sync
"""

import sys
import os
import json
import time

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure standard UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from services.text_extraction import extract_text
from services.subject_validation import validate_subject_relevance
from services.ai_detection import analyze_ai_content
from services.plagiarism import check_plagiarism
from services.analytics.data_mining import extract_stylometrics
from core.database import SessionLocal
from models.submission import Submission, SubmissionStatus
from models.report import Report, ContentLabel
from models.user import User


def main():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Scan document20260813_183154.pdf"))
    subject = "Database Management Systems"

    print("\n" + "="*75)
    print("  [START] EXECUTING COMPLETE VERIFICATION PIPELINE ON SCAN PDF")
    print(f"  Target File : {os.path.basename(pdf_path)}")
    print(f"  Subject     : {subject}")
    print("="*75)

    if not os.path.exists(pdf_path):
        print(f"[ERROR] File not found at {pdf_path}")
        return

    # ── STAGE 1: OCR & Multi-page Text Extraction ──────────────────────
    print("\n" + "─"*75)
    print("  [STAGE 1/5] OCR Vision & Multi-Page Text Extraction")
    print("─"*75)
    t0 = time.time()
    extraction = extract_text(pdf_path)
    t1 = time.time()

    text = extraction.get("text", "")
    ocr_score = extraction.get("ocr_score", 0.0)
    ocr_status = extraction.get("ocr_status", "N/A")
    source = extraction.get("source", "N/A")
    words = text.split()
    word_count = len(words)
    sentence_count = len([s for s in text.split('.') if s.strip()])

    print(f"  [OK] Extraction Status     : {ocr_status}")
    print(f"  [METRIC] OCR Score         : {ocr_score:.1f}%")
    print(f"  [METRIC] Total Words       : {word_count}")
    print(f"  [METRIC] Approx Sentences  : {sentence_count}")
    print(f"  [INFO] Extraction Engine   : {source}")
    print(f"  [TIME] Elapsed             : {t1 - t0:.2f}s")
    print("\n  ── Document Text Preview (Sample from Extracted Pages) ──")
    for line in text[:600].splitlines():
        if line.strip():
            print(f"     | {line}")
    if len(text) > 600:
        print(f"     | ... [{len(text) - 600} characters remaining]")
    print(f"     └{'─'*60}")

    # ── STAGE 2: Subject & Curriculum Relevance Validation ─────────────
    print("\n" + "─"*75)
    print(f"  [STAGE 2/5] Semantic Subject Relevance Check ('{subject}')")
    print("─"*75)
    t0 = time.time()
    subj_val = validate_subject_relevance(text, subject)
    t1 = time.time()

    is_valid = subj_val.get("is_valid", True)
    subj_conf = subj_val.get("confidence", 1.0)
    subj_reason = subj_val.get("reason", "")

    print(f"  [OK] Curriculum Match      : {'PASSED' if is_valid else 'FAILED'}")
    print(f"  [METRIC] Confidence        : {subj_conf * 100:.1f}%")
    print(f"  [INFO] Explanation         : {subj_reason}")
    print(f"  [TIME] Elapsed             : {t1 - t0:.2f}s")

    # ── STAGE 3: Two-Layer AI Content Detection ────────────────────────
    print("\n" + "─"*75)
    print("  [STAGE 3/5] Deep Learning AI Content Detection (Two-Layer / V2 RF)")
    print("─"*75)
    t0 = time.time()
    ai_result = analyze_ai_content(text)
    t1 = time.time()

    ai_score = ai_result.get("ai_score", 0.0)
    ai_label = ai_result.get("label", "Unknown")
    ai_conf = ai_result.get("confidence", 0.0)
    decision_basis = ai_result.get("decision_basis", "")
    reasoning = ai_result.get("reasoning", "")
    model_version = ai_result.get("model_version", "v1")

    print(f"  [VERDICT] AI Label         : {ai_label}")
    print(f"  [METRIC] AI Likelihood     : {ai_score:.2f}%")
    print(f"  [METRIC] Confidence        : {ai_conf:.2f}")
    print(f"  [INFO] Model Architecture  : {model_version} ({decision_basis})")
    print(f"  [INFO] Rationale           : {reasoning}")
    print(f"  [TIME] Elapsed             : {t1 - t0:.2f}s")

    l1 = ai_result.get("layer1_stats")
    l2 = ai_result.get("layer2_semantics")
    if l1:
        print("\n     [Layer 1: Statistical Analysis (DistilGPT-2)]")
        print(f"       * Mean Perplexity    : {l1.get('mean_perplexity', 'N/A')}")
        print(f"       * Mean Entropy       : {l1.get('mean_entropy', 'N/A')}")
        print(f"       * Burstiness (Var)   : {l1.get('burstiness', 'N/A')}")
        print(f"       * Stat AI Likelihood : {l1.get('statistical_ai_likelihood', 'N/A')}%")
        print(f"       * Distribution Type  : {l1.get('pattern_type', 'N/A')}")
    if l2:
        print("\n     [Layer 2: Semantic & Stylometric Analysis]")
        print(f"       * Lexical Diversity  : {l2.get('ttr', 'N/A')} (Type-Token Ratio)")
        print(f"       * Generic Phrasing   : {l2.get('generic_phrasing_score', 'N/A')}%")
        print(f"       * Personal Voice     : {l2.get('personal_voice_score', 'N/A')}%")
        print(f"       * Semantic AI Score  : {l2.get('final_ai_likelihood', 'N/A')}%")

    # ── STAGE 4: Plagiarism & Similarity against Database Corpus ───────
    print("\n" + "─"*75)
    print("  [STAGE 4/5] Peer Plagiarism Detection (TF-IDF & N-Gram Cosine Similarity)")
    print("─"*75)
    t0 = time.time()
    db = SessionLocal()
    try:
        other_reports = (
            db.query(Report)
            .join(Submission)
            .filter(Submission.subject == subject)
            .all()
        )
        corpus = [r.processed_text for r in other_reports if r.processed_text]
        plag_result = check_plagiarism(text, corpus)
        t1 = time.time()

        plag_score = plag_result.get("plagiarism_score", 0.0)
        max_sim = plag_result.get("max_similarity", 0.0)
        matches = plag_result.get("matches_found", 0)

        print(f"  [METRIC] Plagiarism Score  : {plag_score:.2f}%")
        print(f"  [METRIC] Peak Similarity   : {max_sim:.4f}")
        print(f"  [INFO] Peer Corpus Count   : {len(corpus)} assignments in '{subject}'")
        print(f"  [INFO] Matches Over Thresh : {matches}")
        print(f"  [TIME] Elapsed             : {t1 - t0:.2f}s")
    finally:
        db.close()

    # ── STAGE 5: Stylometric Forensic Fingerprinting ───────────────────
    print("\n" + "─"*75)
    print("  [STAGE 5/5] Stylometric Forensic Fingerprint")
    print("─"*75)
    fp = extract_stylometrics(text)
    print(f"  * Avg Word Length          : {fp.get('word_length', 0):.2f} characters")
    print(f"  * Avg Sentence Length      : {fp.get('sentence_length', 0):.2f} words")
    print(f"  * Lexical Richness (TTR)   : {fp.get('ttr', 0):.4f}")
    print(f"  * Punctuation Density      : {fp.get('punctuation_density', 0):.4f}")

    # ── STAGE 6: Database Persistence ──────────────────────────────────
    db = SessionLocal()
    try:
        sub = db.query(Submission).filter(
            Submission.filename.like("%Scan document20260813_183154.pdf%"),
            Submission.subject == subject
        ).order_by(Submission.id.desc()).first()

        label_map = {
            "Original": ContentLabel.original,
            "AI-generated": ContentLabel.ai_generated,
            "Mixed": ContentLabel.mixed,
        }
        content_label = label_map.get(ai_label, ContentLabel.original)

        if sub:
            sub.status = SubmissionStatus.completed
            existing_report = db.query(Report).filter(Report.submission_id == sub.id).first()
            if existing_report:
                existing_report.ai_score = ai_score
                existing_report.plagiarism_score = plag_score
                existing_report.ocr_score = ocr_score
                existing_report.ocr_status = ocr_status
                existing_report.label = content_label
                existing_report.processed_text = text[:5000]
                existing_report.word_count = word_count
                existing_report.sentence_count = sentence_count
            else:
                new_rep = Report(
                    submission_id=sub.id,
                    ai_score=ai_score,
                    plagiarism_score=plag_score,
                    ocr_score=ocr_score,
                    ocr_status=ocr_status,
                    label=content_label,
                    processed_text=text[:5000],
                    word_count=word_count,
                    sentence_count=sentence_count,
                )
                db.add(new_rep)
            db.commit()
            print(f"\n  [DATABASE] Synced and updated Submission #{sub.id} (Status: COMPLETED)")
    except Exception as db_err:
        print(f"  [DATABASE NOTE] DB sync note: {db_err}")
    finally:
        db.close()

    # ── FINAL PIPELINE SUMMARY ─────────────────────────────────────────
    print("\n" + "="*75)
    print("  [SUMMARY] FINAL EVALUATION REPORT")
    print("="*75)
    print(f"  File Processed      : {os.path.basename(pdf_path)}")
    print(f"  Subject             : {subject}")
    print(f"  OCR Status          : {ocr_status} (Score: {ocr_score:.1f}%)")
    print(f"  Total Words         : {word_count}")
    print(f"  AI Verdict          : {ai_label} ({ai_score:.2f}%)")
    print(f"  Plagiarism Score    : {plag_score:.2f}%")
    print(f"  Overall Status      : {'ORIGINAL HUMAN WORK' if ai_score < 40 and plag_score < 30 else 'FLAGGED FOR REVIEW'}")
    print("="*75 + "\n")


if __name__ == "__main__":
    main()
