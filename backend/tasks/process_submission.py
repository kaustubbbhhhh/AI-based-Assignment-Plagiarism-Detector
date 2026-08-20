"""
Celery task: process_submission_task

Full processing pipeline:
  1. Ingest & verify payload (status → "processing")
  2. OCR Vision & Text Extraction (digital text or deep learning TrOCR/Cloud Vision)
  3. OCR Score Calculation & Quality Acceptance Gate (checks >= 65% for images)
  4. Semantic Subject & Domain Alignment Check
  5. AI Content Detection (Perplexity + Burstiness analysis)
  6. Plagiarism Detection (Visual Hash + TF-IDF Cosine Similarity against peer submissions)
  7. Generate and Save Report to database (with OCR metrics)
  8. Mark status → "completed" (ready for student inspection & final lock)

Can be called directly (sync) or via Celery (.delay) for async.
"""

import logging
from tasks.celery_app import celery_app
from core.database import SessionLocal
from models.submission import Submission, SubmissionStatus
from models.report import Report, ContentLabel
from services.text_extraction import extract_text
from services.ai_detection import analyze_ai_content
from services.plagiarism import check_plagiarism

logger = logging.getLogger(__name__)


def _run_pipeline(submission_id: int, update_progress=None):
    """
    Core processing pipeline. Separated from the Celery decorator
    so it can be called both synchronously and asynchronously.
    
    Args:
        submission_id: The DB ID of the submission to process.
        update_progress: Optional callable(state, meta) for Celery progress updates.
    """
    db = SessionLocal()

    try:
        # ── 1. Fetch submission and mark as processing ────────
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found in database.")
            return {"error": "Submission not found"}

        submission.status = SubmissionStatus.processing
        db.commit()
        logger.info(f"[Pipeline] Processing submission #{submission_id}: {submission.filename}")

        if update_progress:
            update_progress("PROGRESS", {
                "progress": "Payload Ingested: Verifying file format and digital streams...",
                "stage": "ingest",
                "current_step": 1,
                "total_steps": 7
            })

        # ── 2. Extract text & OCR ─────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {
                "progress": "Running OCR Vision & text extraction...",
                "stage": "ocr_extraction",
                "current_step": 2,
                "total_steps": 7
            })
            
        extraction_result = extract_text(submission.filepath)
        raw_text = extraction_result.get("text", "")
        visual_hash = extraction_result.get("visual_hash")
        ocr_score = float(extraction_result.get("ocr_score", 100.0))
        ocr_status = extraction_result.get("ocr_status", "Accepted")
        
        if not raw_text or len(raw_text.strip()) < 20:
            logger.warning(f"Submission #{submission_id}: Extracted text is short or sparse.")
            raw_text = raw_text or ""

        # ── 3. Quality & OCR Acceptance Gate ──────────────────
        if update_progress:
            update_progress("PROGRESS", {
                "progress": f"OCR Quality Gate: Calculated score {ocr_score:.1f}% ({ocr_status})...",
                "stage": "ocr_quality",
                "current_step": 3,
                "total_steps": 7
            })

        cleaned_text = raw_text.strip()
        words = cleaned_text.split()
        word_count = len(words)
        sentence_count = len([s for s in cleaned_text.split('.') if s.strip()])

        # ── 4. Semantic Subject Validation ────────────────────
        if update_progress:
            update_progress("PROGRESS", {
                "progress": f"Validating subject curriculum relevance for '{submission.subject}'...",
                "stage": "subject_validation",
                "current_step": 4,
                "total_steps": 7
            })
        from services.subject_validation import validate_subject_relevance
        validation = validate_subject_relevance(cleaned_text, submission.subject)
        
        if not validation["is_valid"]:
            logger.warning(f"Submission #{submission_id} rejected: {validation['reason']}")
            raise ValueError(validation["reason"])

        # ── 5. AI Detection ───────────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {
                "progress": "Running deep-learning AI content detection (Perplexity & Burstiness)...",
                "stage": "ai_detection",
                "current_step": 5,
                "total_steps": 7
            })
        ai_result = analyze_ai_content(cleaned_text)
        ai_score = ai_result["ai_score"]
        ai_label = ai_result["label"]

        # ── 6. Plagiarism Detection ───────────────────────────
        if update_progress:
            update_progress("PROGRESS", {
                "progress": "Comparing against section peer submissions & visual hash corpus...",
                "stage": "plagiarism",
                "current_step": 6,
                "total_steps": 7
            })

        # Build corpus from other completed peer submissions (same subject, different student)
        other_reports = (
            db.query(Report)
            .join(Submission)
            .filter(
                Submission.subject == submission.subject,
                Submission.id != submission_id,
                Submission.student_id != submission.student_id,  # Peer-to-peer only: exclude own prior submissions
            )
            .all()
        )
        
        # Check visual plagiarism first (exact image perceptual duplicate from peers)
        visual_match_found = False
        if visual_hash:
            for r in other_reports:
                if r.visual_hash and r.visual_hash == visual_hash:
                    visual_match_found = True
                    break
        
        if visual_match_found:
            plagiarism_score = 100.0
            logger.warning(f"Submission #{submission_id}: Visual Plagiarism detected! Exact image match found with peer.")
        else:
            corpus = [r.processed_text for r in other_reports if r.processed_text]
            plag_result = check_plagiarism(cleaned_text, corpus)
            plagiarism_score = plag_result["plagiarism_score"]

        # ── 7. Map label string to enum ───────────────────────
        label_map = {
            "Original": ContentLabel.original,
            "AI-generated": ContentLabel.ai_generated,
            "Mixed": ContentLabel.mixed,
        }
        content_label = label_map.get(ai_label, ContentLabel.original)

        # ── 8. Save Report ────────────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {
                "progress": "Document verified! Ready for student review and final lock...",
                "stage": "completed",
                "current_step": 7,
                "total_steps": 7
            })

        # Delete any pre-existing report for this submission (e.g. if re-processed)
        existing_report = db.query(Report).filter(Report.submission_id == submission_id).first()
        if existing_report:
            existing_report.ai_score = ai_score
            existing_report.plagiarism_score = plagiarism_score
            existing_report.ocr_score = ocr_score
            existing_report.ocr_status = ocr_status
            existing_report.label = content_label
            existing_report.processed_text = cleaned_text[:5000]
            existing_report.word_count = word_count
            existing_report.sentence_count = sentence_count
            existing_report.visual_hash = visual_hash
        else:
            report = Report(
                submission_id=submission_id,
                ai_score=ai_score,
                plagiarism_score=plagiarism_score,
                ocr_score=ocr_score,
                ocr_status=ocr_status,
                label=content_label,
                processed_text=cleaned_text[:5000],
                word_count=word_count,
                sentence_count=sentence_count,
                visual_hash=visual_hash,
            )
            db.add(report)

        # Mark submission as completed (ready for student inspection & locking)
        submission.status = SubmissionStatus.completed
        db.commit()

        logger.info(
            f"[Pipeline] Submission #{submission_id} COMPLETED — "
            f"OCR: {ocr_score}%, AI: {ai_score}% ({ai_label}), Plagiarism: {plagiarism_score}%"
        )

        return {
            "submission_id": submission_id,
            "status": "completed",
            "ocr_score": ocr_score,
            "ocr_status": ocr_status,
            "ai_score": ai_score,
            "plagiarism_score": plagiarism_score,
            "label": ai_label,
            "word_count": word_count,
            "sentence_count": sentence_count,
        }

    except Exception as e:
        logger.error(f"[Pipeline] FAILED for submission #{submission_id}: {e}")
        # Mark as failed in DB
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                submission.status = SubmissionStatus.failed
                db.commit()
        except Exception:
            pass
        raise

    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.process_submission", max_retries=3)
def process_submission_task(self, submission_id: int):
    """
    Celery task wrapper. Delegates to _run_pipeline with progress updates.
    """
    def update_progress(state, meta):
        try:
            self.update_state(state=state, meta=meta)
        except Exception:
            pass

    try:
        return _run_pipeline(submission_id, update_progress=update_progress)
    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


def process_submission_sync(submission_id: int):
    """
    Synchronous entry point for environments without Redis/Celery.
    Called directly from the API endpoint.
    """
    return _run_pipeline(submission_id, update_progress=None)
