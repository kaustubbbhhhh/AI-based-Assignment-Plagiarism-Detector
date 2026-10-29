"""
FastAPI REST API for Multi-Model Assignment OCR Pipeline.
Exposes endpoints for file uploads, JSON responses, model health, and VRAM monitoring.
"""

import os
import shutil
import tempfile
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.responses import JSONResponse

from ..pipeline.pipeline import OCRPipeline
from ..schemas.ocr_schema import AssignmentDocument
from ..models.model_manager import ModelManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Model Assignment OCR Pipeline",
    description="CRAFT + TrOCR + GOT-OCR 2.0 Hybrid Pipeline for High-Accuracy Academic OCR",
    version="1.0.0"
)

pipeline_instance: Optional[OCRPipeline] = None


@app.on_event("startup")
def startup_event():
    global pipeline_instance
    logger.info("Initializing OCR Pipeline service...")
    pipeline_instance = OCRPipeline()


@app.get("/health")
def health():
    mm = ModelManager()
    vram = mm.get_vram_usage()
    return {
        "status": "online",
        "device": mm.device,
        "vram": vram,
        "got_enabled": mm.is_got_available()
    }


@app.post("/api/v1/ocr/process-file", response_model=AssignmentDocument)
async def process_file(
    file: UploadFile = File(...),
    enable_debug: bool = Query(default=False)
):
    """
    Process an uploaded PDF or image assignment through the multi-model OCR pipeline.
    """
    global pipeline_instance
    if pipeline_instance is None:
        pipeline_instance = OCRPipeline()

    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in [".pdf", ".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Unsupported file extension. Provide .pdf, .png, or .jpg")

    # Save to temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        debug_dir = os.path.join(temp_dir, "debug") if enable_debug else None
        result = pipeline_instance.process(temp_file_path, debug_dir=debug_dir)
        return result

    except Exception as e:
        logger.error(f"Failed to process file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v1/ocr/clear-vram")
def clear_vram():
    mm = ModelManager()
    mm.clear_vram()
    return {"status": "success", "vram": mm.get_vram_usage()}
