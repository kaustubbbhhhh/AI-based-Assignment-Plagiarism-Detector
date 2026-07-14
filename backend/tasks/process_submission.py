"""
Celery task: process_submission_task

Full processing pipeline:
  1. Update status → "processing"
  2. Extract text from uploaded file
  3. Run AI content detection (perplexity + burstiness)
  4. Run plagiarism check (TF-IDF cosine similarity)
  5. Save Report to database
  6. Update status → "completed"

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

        # ── 2. Extract text ───────────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {"progress": "Extracting text..."})
            
        extraction_result = extract_text(submission.filepath)
        raw_text = extraction_result.get("text", "")
        visual_hash = extraction_result.get("visual_hash")
        
        if not raw_text or len(raw_text.strip()) < 20:
            logger.warning(f"Submission #{submission_id}: Extracted text is too short.")
            raw_text = raw_text or ""

        # ── 3. Preprocess text ────────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {"progress": "Preprocessing text..."})
        cleaned_text = raw_text.strip()
        words = cleaned_text.split()
        word_count = len(words)
        sentence_count = len([s for s in cleaned_text.split('.') if s.strip()])

        # ── 3.5 Semantic Subject Validation ───────────────────
        if update_progress:
            update_progress("PROGRESS", {"progress": "Validating subject relevance..."})
        from services.subject_validation import validate_subject_relevance
        validation = validate_subject_relevance(cleaned_text, submission.subject)
        
        if not validation["is_valid"]:
            logger.warning(f"Submission #{submission_id} rejected: {validation['reason']}")
            raise ValueError(validation["reason"])

        # ── 4. AI Detection ───────────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {"progress": "Running AI detection..."})
        ai_result = analyze_ai_content(cleaned_text)
        ai_score = ai_result["ai_score"]
        ai_label = ai_result["label"]

        # ── 5. Plagiarism Detection ───────────────────────────
        if update_progress:
            update_progress("PROGRESS", {"progress": "Checking plagiarism..."})

        # Build corpus from other completed submissions (same subject)
        other_reports = (
            db.query(Report)
            .join(Submission)
            .filter(
                Submission.subject == submission.subject,
                Submission.id != submission_id,
            )
            .all()
        )
        
        # Check visual plagiarism first
        visual_match_found = False
        if visual_hash:
            for r in other_reports:
                if r.visual_hash and r.visual_hash == visual_hash:
                    visual_match_found = True
                    break
        
        if visual_match_found:
            plagiarism_score = 100.0
            logger.warning(f"Submission #{submission_id}: Visual Plagiarism detected! Exact image match found.")
        else:
            corpus = [r.processed_text for r in other_reports if r.processed_text]
            plag_result = check_plagiarism(cleaned_text, corpus)
            plagiarism_score = plag_result["plagiarism_score"]

        # ── 6. Map label string to enum ───────────────────────
        label_map = {
            "Original": ContentLabel.original,
            "AI-generated": ContentLabel.ai_generated,
            "Mixed": ContentLabel.mixed,
        }
        content_label = label_map.get(ai_label, ContentLabel.original)

        # ── 7. Save Report ────────────────────────────────────
        if update_progress:
            update_progress("PROGRESS", {"progress": "Generating report..."})

        report = Report(
            submission_id=submission_id,
            ai_score=ai_score,
            plagiarism_score=plagiarism_score,
            label=content_label,
            processed_text=cleaned_text[:5000],    # store first 5000 chars
            word_count=word_count,
            sentence_count=sentence_count,
            visual_hash=visual_hash,
        )
        db.add(report)

        # ── 8. Mark submission as completed ───────────────────
        submission.status = SubmissionStatus.completed
        db.commit()

        logger.info(
            f"[Pipeline] Submission #{submission_id} COMPLETED — "
            f"AI: {ai_score}% ({ai_label}), Plagiarism: {plagiarism_score}%"
        )

        return {
            "submission_id": submission_id,
            "status": "completed",
            "ai_score": ai_score,
            "plagiarism_score": plagiarism_score,
            "label": ai_label,
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
