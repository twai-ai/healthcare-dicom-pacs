"""
Load Existing Analysis Data into Database
Loads data from test-code/output directory
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).parent))

from database import SessionLocal, engine, Base
import models

# Paths to data
OUTPUT_DIR = Path("/Users/aeishwary/DICOM-AI/test-code/output")

def load_patients_and_studies(db: Session):
    """Load patient and study data from metadata CSV"""
    
    print("\n" + "="*70)
    print("LOADING PATIENTS AND STUDIES")
    print("="*70)
    
    metadata_csv = OUTPUT_DIR / "dicom_metadata.csv"
    
    if not metadata_csv.exists():
        print(f"✗ File not found: {metadata_csv}")
        return
    
    df = pd.read_csv(metadata_csv)
    print(f"✓ Loaded {len(df)} records")
    
    patients_added = 0
    studies_added = 0
    
    for idx, row in df.iterrows():
        patient_id = row.get('PatientID')
        
        if not patient_id:
            continue
        
        # Check if patient exists
        patient = db.query(models.Patient).filter(
            models.Patient.patient_id == patient_id
        ).first()
        
        if not patient:
            patient = models.Patient(
                patient_id=patient_id,
                patient_name=row.get('PatientName'),
                patient_age=int(row['PatientAge']) if pd.notna(row.get('PatientAge')) else None,
                patient_sex=row.get('PatientSex')
            )
            db.add(patient)
            db.flush()
            patients_added += 1
            print(f"  ✓ Added patient: {patient_id}")
        
        # Create study
        study_uid = row.get('StudyInstanceUID')
        if study_uid:
            existing_study = db.query(models.Study).filter(
                models.Study.study_instance_uid == study_uid
            ).first()
            
            if not existing_study:
                study_date_str = row.get('StudyDate')
                study_date = None
                if study_date_str and pd.notna(study_date_str):
                    try:
                        study_date = datetime.strptime(str(study_date_str), '%Y%m%d').date()
                    except:
                        pass
                
                study = models.Study(
                    patient_id=patient_id,
                    study_instance_uid=study_uid,
                    study_date=study_date,
                    study_description=row.get('StudyDescription'),
                    modality=row.get('Modality'),
                    body_part=row.get('BodyPartExamined'),
                    institution_name=row.get('InstitutionName'),
                    manufacturer=row.get('Manufacturer'),
                    manufacturer_model=row.get('ManufacturerModelName')
                )
                db.add(study)
                studies_added += 1
    
    db.commit()
    print(f"\n✓ Added {patients_added} patients")
    print(f"✓ Added {studies_added} studies")
    return patients_added, studies_added

def load_ai_analyses(db: Session):
    """Load multi-model AI analysis"""
    
    print("\n" + "="*70)
    print("LOADING AI ANALYSES")
    print("="*70)
    
    ai_file = OUTPUT_DIR / "multimodel_ai_analysis_complete.json"
    
    if not ai_file.exists():
        print(f"✗ File not found: {ai_file}")
        return 0
    
    with open(ai_file, 'r') as f:
        data = json.load(f)
    
    analyses_added = 0
    
    # Process patient analyses
    for patient_id, patient_data in data.get('patient_analyses', {}).items():
        study = db.query(models.Study).filter(
            models.Study.patient_id == patient_id
        ).first()
        
        # Add Gemini analysis
        gemini_data = patient_data.get('gemini', {})
        if gemini_data:
            ai_analysis = models.AIAnalysis(
                patient_id=patient_id,
                study_id=study.id if study else None,
                model_name="Google Gemini 2.0 Flash",
                analysis_type="vision",
                findings=gemini_data.get('analysis', ''),
                confidence_score=None,
                covid_probability=None,
                severity_assessment=gemini_data.get('severity'),
                recommendations=gemini_data.get('recommendations'),
                analysis_json=gemini_data
            )
            db.add(ai_analysis)
            analyses_added += 1
        
        # Add Groq analysis
        groq_data = patient_data.get('groq', {})
        if groq_data:
            ai_analysis = models.AIAnalysis(
                patient_id=patient_id,
                study_id=study.id if study else None,
                model_name="Groq LLaMA 3.3 70B",
                analysis_type="vision",
                findings=groq_data.get('analysis', ''),
                confidence_score=None,
                covid_probability=None,
                severity_assessment=groq_data.get('severity'),
                recommendations=groq_data.get('recommendations'),
                analysis_json=groq_data
            )
            db.add(ai_analysis)
            analyses_added += 1
        
        # Add ensemble analysis
        ensemble_data = patient_data.get('ensemble', {})
        if ensemble_data:
            ai_analysis = models.AIAnalysis(
                patient_id=patient_id,
                study_id=study.id if study else None,
                model_name="Multi-Model Ensemble",
                analysis_type="ensemble",
                findings=ensemble_data.get('consensus_analysis', ''),
                confidence_score=None,
                covid_probability=None,
                severity_assessment=ensemble_data.get('severity'),
                recommendations=ensemble_data.get('recommendations'),
                analysis_json=ensemble_data
            )
            db.add(ai_analysis)
            analyses_added += 1
    
    db.commit()
    print(f"✓ Added {analyses_added} AI analyses")
    return analyses_added

def load_diagnostic_analyses(db: Session):
    """Load diagnostic assessments"""
    
    print("\n" + "="*70)
    print("LOADING DIAGNOSTIC ANALYSES")
    print("="*70)
    
    diag_file = OUTPUT_DIR / "diagnostic_assessments_complete.json"
    
    if not diag_file.exists():
        print(f"✗ File not found: {diag_file}")
        return 0
    
    with open(diag_file, 'r') as f:
        data = json.load(f)
    
    analyses_added = 0
    
    for patient_id, assessment in data.get('assessments', {}).items():
        study = db.query(models.Study).filter(
            models.Study.patient_id == patient_id
        ).first()
        
        diagnostic = models.DiagnosticAnalysis(
            patient_id=patient_id,
            study_id=study.id if study else None,
            covid_score=assessment.get('covid_score'),
            covid_probability=assessment.get('covid_probability'),
            severity=assessment.get('severity'),
            confidence=assessment.get('confidence'),
            opacity_features=assessment.get('opacity_features', {}),
            distribution_features=assessment.get('distribution_features', {}),
            quantitative_features=assessment.get('quantitative_features', {}),
            clinical_reasoning=assessment.get('clinical_reasoning'),
            differential_diagnosis=assessment.get('differential_diagnosis'),
            recommendations=assessment.get('recommendations')
        )
        db.add(diagnostic)
        analyses_added += 1
    
    db.commit()
    print(f"✓ Added {analyses_added} diagnostic analyses")
    return analyses_added

def load_bias_analysis(db: Session):
    """Load bias analysis"""
    
    print("\n" + "="*70)
    print("LOADING BIAS ANALYSIS")
    print("="*70)
    
    bias_file = OUTPUT_DIR / "bias_analysis_report.json"
    
    if not bias_file.exists():
        print(f"✗ File not found: {bias_file}")
        return 0
    
    with open(bias_file, 'r') as f:
        data = json.load(f)
    
    total_patients = db.query(models.Patient).count()
    total_studies = db.query(models.Study).count()
    
    bias_analysis = models.BiasAnalysis(
        analysis_date=date.today(),
        total_patients=total_patients,
        total_studies=total_studies,
        manufacturer_diversity=0.5,
        protocol_diversity=0.5,
        bias_risk_level=data.get('risk_level', 'MEDIUM'),
        bias_score=data.get('bias_score', 0.5),
        recommendations=data.get('recommendations', ''),
        metrics_json=data
    )
    db.add(bias_analysis)
    db.commit()
    
    print(f"✓ Added bias analysis")
    return 1

def main():
    """Main loading process"""
    
    print("\n" + "="*70)
    print("LOADING EXISTING ANALYSIS DATA")
    print("="*70)
    print(f"\nData directory: {OUTPUT_DIR}")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Load data
        patients, studies = load_patients_and_studies(db)
        ai_count = load_ai_analyses(db)
        diag_count = load_diagnostic_analyses(db)
        bias_count = load_bias_analysis(db)
        
        print("\n" + "="*70)
        print("✅ DATA LOADING COMPLETE!")
        print("="*70)
        print(f"\nLoaded:")
        print(f"  • {patients} patients")
        print(f"  • {studies} studies")
        print(f"  • {ai_count} AI analyses")
        print(f"  • {diag_count} diagnostic analyses")
        print(f"  • {bias_count} bias analysis")
        
        print("\n🌐 View in web app: http://localhost:3000")
        
    except Exception as e:
        print(f"\n✗ Error during loading: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

