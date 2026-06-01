"""
Analysis API Routes
Endpoints for running DICOM analysis through the web interface
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile
from pathlib import Path
import shutil

from database import SessionLocal
import models
from analysis_engine import DICOMAnalyzer
from dicom_storage import persist_analysis_from_upload, storage_status

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_analyzer():
    return DICOMAnalyzer(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )


@router.post("/upload")
async def upload_dicom(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and analyze a single DICOM file; persist to Postgres + object storage."""
    if not file.filename.endswith(".dcm"):
        raise HTTPException(status_code=400, detail="File must be a DICOM file (.dcm)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        analyzer = get_analyzer()
        result = analyzer.analyze_complete(tmp_path)
        if result.get("status") == "complete":
            result = persist_analysis_from_upload(db, tmp_path, result, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload and analyze multiple DICOM files."""
    results = []

    for file in files:
        if not file.filename.endswith(".dcm"):
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "error": "Not a DICOM file",
                }
            )
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)

        try:
            analyzer = get_analyzer()
            result = analyzer.analyze_complete(tmp_path)
            result["filename"] = file.filename
            if result.get("status") == "complete":
                result = persist_analysis_from_upload(
                    db, tmp_path, result, file.filename
                )
            results.append(result)
        except Exception as e:
            results.append(
                {"filename": file.filename, "status": "error", "error": str(e)}
            )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    return {"total_files": len(files), "results": results}


@router.post("/reanalyze/{patient_id}")
def reanalyze_patient(patient_id: str, db: Session = Depends(get_db)):
    """Re-run analysis for an existing patient."""
    patient = (
        db.query(models.Patient)
        .filter(models.Patient.patient_id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    studies = (
        db.query(models.Study)
        .filter(models.Study.patient_id == patient_id)
        .all()
    )
    ai_analyses = (
        db.query(models.AIAnalysis)
        .filter(models.AIAnalysis.patient_id == patient_id)
        .all()
    )
    diagnostic = (
        db.query(models.DiagnosticAnalysis)
        .filter(models.DiagnosticAnalysis.patient_id == patient_id)
        .first()
    )

    return {
        "patient_id": patient_id,
        "studies": [
            {"id": s.id, "modality": s.modality, "body_part": s.body_part}
            for s in studies
        ],
        "ai_analyses": len(ai_analyses),
        "diagnostic": diagnostic is not None,
        "message": "To re-analyze, upload the original DICOM file",
    }


@router.get("/status")
def get_analysis_status():
    """Get current analysis engine status."""
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    groq_configured = bool(os.getenv("GROQ_API_KEY"))

    return {
        "status": "operational",
        "storage": storage_status(),
        "capabilities": {
            "dicom_processing": True,
            "diagnostic_analysis": True,
            "gemini_ai": gemini_configured,
            "groq_ai": groq_configured,
            "batch_processing": True,
            "object_storage": True,
        },
        "models_available": [
            "Data-Driven Diagnostic Engine",
            "Google Gemini 2.0 Flash" if gemini_configured else None,
            "Groq LLaMA 3.3 70B" if groq_configured else None,
        ],
        "supported_formats": [".dcm"],
        "max_file_size": "100MB",
    }
