"""
Analysis API Routes
Endpoints for running DICOM analysis through the web interface
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile
from pathlib import Path
import shutil

from database import SessionLocal
import models
from analysis_engine import DICOMAnalyzer
from study_images import upsert_study_images

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize analyzer
def get_analyzer():
    return DICOMAnalyzer(
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        groq_api_key=os.getenv('GROQ_API_KEY')
    )

# ============================================================================
# FILE UPLOAD & ANALYSIS
# ============================================================================

@router.post("/upload")
async def upload_dicom(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Upload and analyze a single DICOM file"""
    
    if not file.filename.endswith('.dcm'):
        raise HTTPException(status_code=400, detail="File must be a DICOM file (.dcm)")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    
    try:
        # Run analysis
        analyzer = get_analyzer()
        result = analyzer.analyze_complete(tmp_path)
        
        # Save to database
        if result.get('status') == 'complete':
            metadata = result.get('metadata', {})
            patient_id = metadata.get('patient_id')
            
            # Create or get patient
            patient = db.query(models.Patient).filter(
                models.Patient.patient_id == patient_id
            ).first()
            
            if not patient:
                patient = models.Patient(
                    patient_id=patient_id,
                    patient_name=metadata.get('patient_name'),
                    patient_age=metadata.get('patient_age'),
                    patient_sex=metadata.get('patient_sex')
                )
                db.add(patient)
                db.flush()
            
            # Check if study already exists (to avoid duplicate key error)
            study_uid = metadata.get('study_instance_uid')
            study = db.query(models.Study).filter(
                models.Study.study_instance_uid == study_uid
            ).first()
            
            if not study:
                # Create new study
                study = models.Study(
                    patient_id=patient_id,
                    study_instance_uid=study_uid,
                    study_description=metadata.get('study_description'),
                    modality=metadata.get('modality'),
                    body_part=metadata.get('body_part'),
                    manufacturer=metadata.get('manufacturer'),
                    manufacturer_model=metadata.get('manufacturer_model')
                )
                db.add(study)
                db.flush()
                print(f"  ✓ Created new study: {study_uid}")
            else:
                print(f"  ℹ️  Using existing study: {study_uid}")
                # Delete old analyses to replace with new ones
                db.query(models.DiagnosticAnalysis).filter(
                    models.DiagnosticAnalysis.study_id == study.id
                ).delete()
                db.query(models.AIAnalysis).filter(
                    models.AIAnalysis.study_id == study.id
                ).delete()
                db.commit()
            
            # Save diagnostic analysis
            diagnostic = result.get('diagnostic', {})
            diag_record = models.DiagnosticAnalysis(
                patient_id=patient_id,
                study_id=study.id,
                covid_score=diagnostic.get('covid_score'),
                covid_probability=diagnostic.get('covid_probability'),
                severity=diagnostic.get('severity'),
                confidence=diagnostic.get('confidence'),
                clinical_reasoning=diagnostic.get('clinical_reasoning'),
                recommendations=diagnostic.get('recommendations'),
                quantitative_features=diagnostic.get('quantitative_features', {})
            )
            db.add(diag_record)
            
            # Save scan previews and intensity statistics
            upsert_study_images(db, study, tmp_path)
            
            # Save AI analyses
            ai_results = result.get('ai_analysis', {}).get('models', {})
            for model_name, ai_data in ai_results.items():
                if 'analysis' in ai_data:
                    ai_record = models.AIAnalysis(
                        patient_id=patient_id,
                        study_id=study.id,
                        model_name=ai_data.get('model', model_name),
                        analysis_type='vision',
                        findings=ai_data.get('analysis'),
                        analysis_json=ai_data
                    )
                    db.add(ai_record)
            
            db.commit()
            
            result['database_saved'] = True
            result['patient_id'] = patient_id
            result['study_id'] = study.id
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()

@router.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload and analyze multiple DICOM files"""
    
    results = []
    
    for file in files:
        if not file.filename.endswith('.dcm'):
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': 'Not a DICOM file'
            })
            continue
        
        # Save and analyze
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)
        
        try:
            analyzer = get_analyzer()
            result = analyzer.analyze_complete(tmp_path)
            result['filename'] = file.filename
            results.append(result)
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': str(e)
            })
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    
    return {
        'total_files': len(files),
        'results': results
    }

# ============================================================================
# RE-ANALYSIS
# ============================================================================

@router.post("/reanalyze/{patient_id}")
def reanalyze_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Re-run analysis for an existing patient"""
    
    patient = db.query(models.Patient).filter(
        models.Patient.patient_id == patient_id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # This would require the original DICOM file
    # For now, return existing analyses
    studies = db.query(models.Study).filter(
        models.Study.patient_id == patient_id
    ).all()
    
    ai_analyses = db.query(models.AIAnalysis).filter(
        models.AIAnalysis.patient_id == patient_id
    ).all()
    
    diagnostic = db.query(models.DiagnosticAnalysis).filter(
        models.DiagnosticAnalysis.patient_id == patient_id
    ).first()
    
    return {
        'patient_id': patient_id,
        'studies': [
            {
                'id': s.id,
                'modality': s.modality,
                'body_part': s.body_part
            } for s in studies
        ],
        'ai_analyses': len(ai_analyses),
        'diagnostic': diagnostic is not None,
        'message': 'To re-analyze, upload the original DICOM file'
    }

# ============================================================================
# ANALYSIS STATUS
# ============================================================================

@router.get("/status")
def get_analysis_status():
    """Get current analysis engine status"""
    
    gemini_configured = bool(os.getenv('GEMINI_API_KEY'))
    groq_configured = bool(os.getenv('GROQ_API_KEY'))
    
    return {
        'status': 'operational',
        'capabilities': {
            'dicom_processing': True,
            'diagnostic_analysis': True,
            'gemini_ai': gemini_configured,
            'groq_ai': groq_configured,
            'batch_processing': True
        },
        'models_available': [
            'Data-Driven Diagnostic Engine',
            'Google Gemini 2.0 Flash' if gemini_configured else None,
            'Groq LLaMA 3.3 70B' if groq_configured else None
        ],
        'supported_formats': ['.dcm'],
        'max_file_size': '100MB'
    }

