"""
DICOM-AI Platform Backend API
FastAPI application for medical imaging analysis platform
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import os
from datetime import datetime

from database import engine, SessionLocal, Base
import models
import schemas
from analysis_routes import router as analysis_router
from pdf_export import PDFReportGenerator

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="DICOM-AI Platform API",
    description="AI-Powered Medical Imaging Analysis Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include analysis routes
app.include_router(analysis_router)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# HEALTH CHECK & INFO
# ============================================================================

@app.get("/")
def root():
    """API root - health check"""
    return {
        "status": "healthy",
        "service": "DICOM-AI Platform API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/info")
def get_platform_info(db: Session = Depends(get_db)):
    """Get platform overview information"""
    
    total_patients = db.query(models.Patient).count()
    total_studies = db.query(models.Study).count()
    total_ai_analyses = db.query(models.AIAnalysis).count()
    total_diagnostic_analyses = db.query(models.DiagnosticAnalysis).count()
    
    # Get modality distribution
    modalities = db.query(
        models.Study.modality,
        func.count(models.Study.id).label('count')
    ).group_by(models.Study.modality).all()
    
    # Get latest bias analysis
    latest_bias = db.query(models.BiasAnalysis).order_by(
        models.BiasAnalysis.created_at.desc()
    ).first()
    
    return {
        "overview": {
            "total_patients": total_patients,
            "total_studies": total_studies,
            "total_ai_analyses": total_ai_analyses,
            "total_diagnostic_analyses": total_diagnostic_analyses,
        },
        "modality_distribution": [
            {"modality": m.modality, "count": m.count} for m in modalities
        ],
        "bias_status": {
            "risk_level": latest_bias.bias_risk_level if latest_bias else "UNKNOWN",
            "bias_score": latest_bias.bias_score if latest_bias else 0.0,
        } if latest_bias else None,
        "platform_features": [
            "Multi-Model AI Analysis (Gemini + Groq)",
            "Data-Driven Diagnostic Assessment",
            "Protocol Standardization Analysis",
            "DICOM Validation & Compliance",
            "Bias & Generalizability Assessment",
            "Comprehensive Medical Reports"
        ]
    }

# ============================================================================
# PATIENTS
# ============================================================================

@app.get("/api/patients", response_model=List[schemas.PatientListItem])
def get_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all patients with scan thumbnails when available"""
    patients = db.query(models.Patient).offset(skip).limit(limit).all()
    results = []

    for patient in patients:
        study = (
            db.query(models.Study)
            .filter(models.Study.patient_id == patient.patient_id)
            .order_by(models.Study.id)
            .first()
        )
        stats = None
        if study:
            stats = (
                db.query(models.ImageStatistics)
                .filter(models.ImageStatistics.study_id == study.id)
                .first()
            )
        diagnostic = (
            db.query(models.DiagnosticAnalysis)
            .filter(models.DiagnosticAnalysis.patient_id == patient.patient_id)
            .first()
        )

        results.append(
            schemas.PatientListItem(
                id=patient.id,
                patient_id=patient.patient_id,
                patient_name=patient.patient_name,
                patient_age=patient.patient_age,
                patient_sex=patient.patient_sex,
                created_at=patient.created_at,
                scan_thumbnail=stats.main_image_data if stats else None,
                modality=study.modality if study else None,
                study_description=study.study_description if study else None,
                covid_score=diagnostic.covid_score if diagnostic else None,
            )
        )

    return results

@app.get("/api/patients/{patient_id}", response_model=schemas.PatientDetail)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get detailed patient information"""
    patient = db.query(models.Patient).filter(
        models.Patient.patient_id == patient_id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get related data
    studies = db.query(models.Study).filter(
        models.Study.patient_id == patient_id
    ).all()
    
    ai_analyses = db.query(models.AIAnalysis).filter(
        models.AIAnalysis.patient_id == patient_id
    ).all()
    
    diagnostic = db.query(models.DiagnosticAnalysis).filter(
        models.DiagnosticAnalysis.patient_id == patient_id
    ).first()

    image_statistics = None
    if studies:
        image_statistics = (
            db.query(models.ImageStatistics)
            .filter(models.ImageStatistics.study_id == studies[0].id)
            .first()
        )
    
    return {
        "patient": patient,
        "studies": studies,
        "ai_analyses": ai_analyses,
        "diagnostic_analysis": diagnostic,
        "image_statistics": image_statistics,
    }

# ============================================================================
# STUDIES
# ============================================================================

@app.get("/api/studies", response_model=List[schemas.StudyOut])
def get_studies(
    modality: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of all studies, optionally filtered by modality"""
    query = db.query(models.Study)
    
    if modality:
        query = query.filter(models.Study.modality == modality)
    
    studies = query.offset(skip).limit(limit).all()
    return studies

@app.get("/api/studies/{study_id}", response_model=schemas.StudyDetail)
def get_study(study_id: int, db: Session = Depends(get_db)):
    """Get detailed study information"""
    study = db.query(models.Study).filter(models.Study.id == study_id).first()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get related data
    dicom_metadata = db.query(models.DICOMMetadata).filter(
        models.DICOMMetadata.study_id == study_id
    ).all()
    
    protocol = db.query(models.ProtocolAnalysis).filter(
        models.ProtocolAnalysis.study_id == study_id
    ).first()
    
    quality = db.query(models.QualityMetrics).filter(
        models.QualityMetrics.study_id == study_id
    ).first()
    
    stats = db.query(models.ImageStatistics).filter(
        models.ImageStatistics.study_id == study_id
    ).first()
    
    return {
        "study": study,
        "dicom_metadata": dicom_metadata,
        "protocol_analysis": protocol,
        "quality_metrics": quality,
        "image_statistics": stats
    }

# ============================================================================
# AI ANALYSIS
# ============================================================================

@app.get("/api/ai-analysis", response_model=List[schemas.AIAnalysisOut])
def get_ai_analyses(
    model_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all AI analysis results"""
    query = db.query(models.AIAnalysis)
    
    if model_name:
        query = query.filter(models.AIAnalysis.model_name == model_name)
    
    analyses = query.order_by(models.AIAnalysis.created_at.desc()).offset(skip).limit(limit).all()
    return analyses

@app.get("/api/ai-analysis/patient/{patient_id}", response_model=List[schemas.AIAnalysisOut])
def get_patient_ai_analyses(patient_id: str, db: Session = Depends(get_db)):
    """Get AI analysis results for a specific patient"""
    analyses = db.query(models.AIAnalysis).filter(
        models.AIAnalysis.patient_id == patient_id
    ).all()
    
    if not analyses:
        raise HTTPException(status_code=404, detail="No AI analyses found for this patient")
    
    return analyses

# ============================================================================
# DIAGNOSTIC ANALYSIS
# ============================================================================

@app.get("/api/diagnostic-analysis", response_model=List[schemas.DiagnosticAnalysisOut])
def get_diagnostic_analyses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all diagnostic analysis results"""
    analyses = db.query(models.DiagnosticAnalysis).order_by(
        models.DiagnosticAnalysis.created_at.desc()
    ).offset(skip).limit(limit).all()
    return analyses

@app.get("/api/diagnostic-analysis/patient/{patient_id}", response_model=schemas.DiagnosticAnalysisOut)
def get_patient_diagnostic_analysis(patient_id: str, db: Session = Depends(get_db)):
    """Get diagnostic analysis for a specific patient"""
    analysis = db.query(models.DiagnosticAnalysis).filter(
        models.DiagnosticAnalysis.patient_id == patient_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No diagnostic analysis found for this patient")
    
    return analysis

# ============================================================================
# QUALITY & PROTOCOL ANALYSIS
# ============================================================================

@app.get("/api/protocol-analysis")
def get_protocol_analyses(db: Session = Depends(get_db)):
    """Get protocol analysis summary"""
    protocols = db.query(models.ProtocolAnalysis).all()
    
    # Aggregate statistics
    total = len(protocols)
    drift_detected = sum(1 for p in protocols if p.drift_detected)
    avg_standardization = sum(p.standardization_score for p in protocols) / total if total > 0 else 0
    
    # Manufacturer distribution
    manufacturers = db.query(
        models.ProtocolAnalysis.manufacturer,
        func.count(models.ProtocolAnalysis.id).label('count')
    ).group_by(models.ProtocolAnalysis.manufacturer).all()
    
    return {
        "summary": {
            "total_protocols": total,
            "drift_detected": drift_detected,
            "avg_standardization_score": round(avg_standardization, 2)
        },
        "manufacturer_distribution": [
            {"manufacturer": m.manufacturer, "count": m.count} for m in manufacturers
        ],
        "protocols": protocols
    }

@app.get("/api/bias-analysis")
def get_bias_analysis(db: Session = Depends(get_db)):
    """Get latest bias analysis"""
    analysis = db.query(models.BiasAnalysis).order_by(
        models.BiasAnalysis.created_at.desc()
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No bias analysis found")
    
    return analysis

# ============================================================================
# STATISTICS & METRICS
# ============================================================================

@app.get("/api/statistics/overview")
def get_statistics_overview(db: Session = Depends(get_db)):
    """Get comprehensive platform statistics"""
    
    # Patient demographics
    patients = db.query(models.Patient).all()
    age_distribution = {}
    sex_distribution = {}
    
    for p in patients:
        if p.patient_age:
            age_group = f"{(p.patient_age // 10) * 10}-{(p.patient_age // 10) * 10 + 9}"
            age_distribution[age_group] = age_distribution.get(age_group, 0) + 1
        if p.patient_sex:
            sex_distribution[p.patient_sex] = sex_distribution.get(p.patient_sex, 0) + 1
    
    # Diagnostic results summary
    diagnostics = db.query(models.DiagnosticAnalysis).all()
    covid_scores = [d.covid_score for d in diagnostics if d.covid_score]
    
    # AI model performance
    ai_analyses = db.query(models.AIAnalysis).all()
    ai_confidence = [a.confidence_score for a in ai_analyses if a.confidence_score]
    
    return {
        "demographics": {
            "age_distribution": age_distribution,
            "sex_distribution": sex_distribution
        },
        "diagnostic_summary": {
            "total_analyses": len(diagnostics),
            "avg_covid_score": sum(covid_scores) / len(covid_scores) if covid_scores else 0,
            "score_distribution": {
                "low": sum(1 for s in covid_scores if s <= 2),
                "moderate": sum(1 for s in covid_scores if 2 < s <= 3),
                "high": sum(1 for s in covid_scores if s > 3)
            }
        },
        "ai_performance": {
            "total_analyses": len(ai_analyses),
            "avg_confidence": sum(ai_confidence) / len(ai_confidence) if ai_confidence else 0,
            "models_used": list(set(a.model_name for a in ai_analyses))
        }
    }

@app.get("/api/statistics/cohort")
def get_cohort_statistics(db: Session = Depends(get_db)):
    """Get cohort-level analysis statistics"""
    
    # Modality distribution
    modalities = db.query(
        models.Study.modality,
        func.count(models.Study.id).label('count')
    ).group_by(models.Study.modality).all()
    
    # Manufacturer distribution
    manufacturers = db.query(
        models.Study.manufacturer,
        func.count(models.Study.id).label('count')
    ).group_by(models.Study.manufacturer).filter(
        models.Study.manufacturer.isnot(None)
    ).all()
    
    # Body part examined
    body_parts = db.query(
        models.Study.body_part,
        func.count(models.Study.id).label('count')
    ).group_by(models.Study.body_part).filter(
        models.Study.body_part.isnot(None)
    ).all()
    
    return {
        "modality_distribution": [
            {"modality": m.modality, "count": m.count} for m in modalities
        ],
        "manufacturer_distribution": [
            {"manufacturer": m.manufacturer or "Unknown", "count": m.count} for m in manufacturers
        ],
        "body_part_distribution": [
            {"body_part": b.body_part, "count": b.count} for b in body_parts
        ]
    }

# ============================================================================
# FUTURE SCOPE
# ============================================================================

# ============================================================================
# PDF EXPORT
# ============================================================================

@app.get("/api/export/pdf/{patient_id}")
def export_patient_pdf(patient_id: str):
    """Export comprehensive patient analysis as PDF"""
    try:
        generator = PDFReportGenerator()
        pdf_buffer = generator.generate_patient_report(patient_id)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=DICOM_AI_Report_{patient_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/api/future-scope")
def get_future_scope():
    """Get platform future scope and roadmap"""
    return {
        "near_term": [
            {
                "title": "Expanded Dataset",
                "description": "Scale to 100-1000 patients for robust validation",
                "priority": "HIGH",
                "timeline": "1-2 months"
            },
            {
                "title": "Custom AI Model Training",
                "description": "Train domain-specific models on curated datasets",
                "priority": "HIGH",
                "timeline": "2-3 months"
            },
            {
                "title": "Multi-Center Validation",
                "description": "Validate across multiple institutions and scanner types",
                "priority": "MEDIUM",
                "timeline": "3-6 months"
            },
            {
                "title": "3D Visualization",
                "description": "Interactive 3D rendering of CT and MRI volumes",
                "priority": "MEDIUM",
                "timeline": "2-4 months"
            }
        ],
        "long_term": [
            {
                "title": "FDA/CE Regulatory Approval",
                "description": "Clinical validation and regulatory submission",
                "priority": "HIGH",
                "timeline": "12-18 months"
            },
            {
                "title": "PACS Integration",
                "description": "Direct integration with hospital PACS systems",
                "priority": "HIGH",
                "timeline": "6-12 months"
            },
            {
                "title": "Real-Time Analysis",
                "description": "Live analysis as images are acquired",
                "priority": "MEDIUM",
                "timeline": "12-18 months"
            },
            {
                "title": "Multi-Disease Detection",
                "description": "Expand beyond COVID-19 to multiple pathologies",
                "priority": "MEDIUM",
                "timeline": "6-12 months"
            },
            {
                "title": "Federated Learning",
                "description": "Privacy-preserving multi-institutional training",
                "priority": "LOW",
                "timeline": "18-24 months"
            }
        ],
        "research_opportunities": [
            "Publication in radiology journals",
            "Clinical trial design and execution",
            "Algorithm performance benchmarking",
            "Health economics and outcomes research",
            "AI explainability and interpretability studies"
        ],
        "technical_enhancements": [
            "Automated de-identification pipeline",
            "Advanced bias mitigation techniques",
            "Model uncertainty quantification",
            "Adversarial robustness testing",
            "Continuous learning and model updates"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

