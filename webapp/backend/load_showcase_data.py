"""
Load Showcase Data from Existing Analysis
Populates database with your 2 analyzed COVID-19 patients
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
from object_storage import open_data_file


def _read_showcase_csv():
    with open_data_file("dicom_metadata.csv") as path:
        return pd.read_csv(path)


def _read_showcase_json(name: str):
    with open_data_file(name) as path:
        with open(path) as f:
            return json.load(f)

def load_patients_and_studies(db: Session):
    """Load 2 COVID-19 patients with studies"""
    
    print("\n" + "="*70)
    print("LOADING PATIENTS AND STUDIES")
    print("="*70)
    
    try:
        df = _read_showcase_csv()
    except FileNotFoundError:
        print("✗ File not found: dicom_metadata.csv (showcase/ local or S3)")
        return 0, 0
    print(f"✓ Loaded {len(df)} records from metadata")
    
    patients_added = 0
    studies_added = 0
    
    for idx, row in df.iterrows():
        patient_id = row.get('PatientID')
        if not patient_id:
            continue
        
        # Delete existing patient and related data first
        existing = db.query(models.Patient).filter(
            models.Patient.patient_id == patient_id
        ).first()
        
        if existing:
            # Delete related data first
            db.query(models.AIAnalysis).filter(models.AIAnalysis.patient_id == patient_id).delete()
            db.query(models.DiagnosticAnalysis).filter(models.DiagnosticAnalysis.patient_id == patient_id).delete()
            db.query(models.Study).filter(models.Study.patient_id == patient_id).delete()
            db.query(models.Patient).filter(models.Patient.patient_id == patient_id).delete()
            db.commit()
        
        # Add fresh patient
        patient = models.Patient(
            patient_id=patient_id,
            patient_name=row.get('PatientName'),
            patient_age=int(row['PatientAge']) if pd.notna(row.get('PatientAge')) else None,
            patient_sex=row.get('PatientSex')
        )
        db.add(patient)
        db.flush()
        patients_added += 1
        print(f"  ✓ Added patient: {patient_id} ({row.get('PatientAge')}Y {row.get('PatientSex')})")
        
        # Add study
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
                        study_date = datetime.strptime(str(int(study_date_str)), '%Y%m%d').date()
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
                db.flush()
                studies_added += 1
    
    # Important: Commit patients and studies BEFORE adding analyses
    db.commit()
    print(f"\n✅ Added {patients_added} patients, {studies_added} studies")
    print(f"✓ Committed to database - ready for analyses")
    return patients_added, studies_added

def load_ai_analyses(db: Session):
    """Load multi-model AI analysis results"""
    
    print("\n" + "="*70)
    print("LOADING AI ANALYSES")
    print("="*70)
    
    try:
        data = _read_showcase_json("multimodel_ai_analysis_complete.json")
    except FileNotFoundError:
        print("✗ File not found: multimodel_ai_analysis_complete.json")
        return 0
    
    analyses_added = 0
    
    # Data is a list of patient analyses
    for patient_data in data:
        patient_id = patient_data.get('patient_id')
        
        if not patient_id:
            continue
        
        study = db.query(models.Study).filter(
            models.Study.patient_id == patient_id
        ).first()
        
        # Get individual analyses
        individual = patient_data.get('individual_analyses', {})
        
        # Gemini analysis
        gemini_text = individual.get('gemini-2.0-flash', '')
        if gemini_text and not gemini_text.startswith('Gemini Error'):
            ai = models.AIAnalysis(
                patient_id=patient_id,
                study_id=study.id if study else None,
                model_name="Google Gemini 2.0 Flash",
                analysis_type="vision",
                findings=gemini_text,
                severity_assessment="Indeterminate",
                analysis_json={'analysis': gemini_text}
            )
            db.add(ai)
            analyses_added += 1
            print(f"  ✓ Added Gemini analysis for {patient_id}")
        
        # Groq analysis
        groq_text = individual.get('llama-3.3-70b-versatile', '')
        if groq_text:
            ai = models.AIAnalysis(
                patient_id=patient_id,
                study_id=study.id if study else None,
                model_name="Groq LLaMA 3.3 70B",
                analysis_type="vision",
                findings=groq_text,
                severity_assessment="Indeterminate",
                analysis_json={'analysis': groq_text}
            )
            db.add(ai)
            analyses_added += 1
            print(f"  ✓ Added Groq analysis for {patient_id}")
        
        # Ensemble
        ensemble_text = patient_data.get('ensemble_analysis', '')
        if ensemble_text:
            ai = models.AIAnalysis(
                patient_id=patient_id,
                study_id=study.id if study else None,
                model_name="Multi-Model Ensemble",
                analysis_type="ensemble",
                findings=ensemble_text,
                severity_assessment="Indeterminate",
                analysis_json={'analysis': ensemble_text}
            )
            db.add(ai)
            analyses_added += 1
            print(f"  ✓ Added Ensemble analysis for {patient_id}")
    
    db.commit()
    print(f"\n✅ Added {analyses_added} AI analyses")
    return analyses_added

def load_diagnostic_analyses(db: Session):
    """Load diagnostic assessments"""
    
    print("\n" + "="*70)
    print("LOADING DIAGNOSTIC ANALYSES")
    print("="*70)
    
    try:
        data = _read_showcase_json("diagnostic_assessments_complete.json")
    except FileNotFoundError:
        print("✗ File not found: diagnostic_assessments_complete.json")
        return 0
    
    analyses_added = 0
    
    # Data is a list of assessments
    for assessment in data:
        patient_id = assessment.get('patient_id')
        
        if not patient_id:
            continue
        
        study = db.query(models.Study).filter(
            models.Study.patient_id == patient_id
        ).first()
        
        covid_assess = assessment.get('covid19_assessment', {})
        
        # Join recommendations list into string
        recommendations_list = assessment.get('recommendations', [])
        recommendations = '\n'.join(recommendations_list) if isinstance(recommendations_list, list) else str(recommendations_list)
        
        # Join differential diagnosis
        diff_diagnosis = ', '.join(assessment.get('differential_diagnosis', []))
        
        diagnostic = models.DiagnosticAnalysis(
            patient_id=patient_id,
            study_id=study.id if study else None,
            covid_score=covid_assess.get('score'),
            covid_probability=covid_assess.get('classification', 'Unknown'),
            severity=covid_assess.get('severity_estimate', 'Unknown'),
            confidence=assessment.get('confidence_level', 'Unknown'),
            quantitative_features=assessment.get('quantitative_features', {}),
            clinical_reasoning=covid_assess.get('classification', ''),
            differential_diagnosis=diff_diagnosis,
            recommendations=recommendations
        )
        db.add(diagnostic)
        analyses_added += 1
        
        score = covid_assess.get('score', 0)
        print(f"  ✓ Added diagnostic for {patient_id}: COVID Score {score}/5 ({covid_assess.get('classification', 'Unknown')})")
    
    db.commit()
    print(f"\n✅ Added {analyses_added} diagnostic analyses")
    return analyses_added

def load_bias_analysis(db: Session):
    """Load bias analysis"""
    
    print("\n" + "="*70)
    print("LOADING BIAS ANALYSIS")
    print("="*70)
    
    try:
        data = _read_showcase_json("bias_analysis_report.json")
    except FileNotFoundError:
        print("✗ File not found: bias_analysis_report.json")
        return 0
    
    total_patients = db.query(models.Patient).count()
    total_studies = db.query(models.Study).count()
    
    bias = models.BiasAnalysis(
        analysis_date=date.today(),
        total_patients=total_patients,
        total_studies=total_studies,
        manufacturer_diversity=0.5,
        protocol_diversity=0.5,
        bias_risk_level=data.get('risk_level', 'HIGH'),
        bias_score=data.get('bias_score', 0.5),
        recommendations=data.get('recommendations', 'Expand dataset for better diversity'),
        metrics_json=data
    )
    db.add(bias)
    db.commit()
    
    print(f"✓ Added bias analysis: {bias.bias_risk_level} risk")
    print(f"\n✅ Bias analysis loaded")
    return 1

def main():
    """Load all showcase data"""
    
    print("\n" + "="*70)
    print("🎬 LOADING SHOWCASE DATA")
    print("="*70)
    print("\nLoading your existing 2 analyzed COVID-19 patients...")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        patients, studies = load_patients_and_studies(db)
        ai_count = load_ai_analyses(db)
        diag_count = load_diagnostic_analyses(db)
        bias_count = load_bias_analysis(db)
        
        print("\n" + "="*70)
        print("✅ SHOWCASE DATA LOADED SUCCESSFULLY!")
        print("="*70)
        print(f"\nDatabase now contains:")
        print(f"  • {patients} patients (COVID-19 cases)")
        print(f"  • {studies} studies (chest X-rays)")
        print(f"  • {ai_count} AI analyses (Gemini + Groq + Ensemble)")
        print(f"  • {diag_count} diagnostic analyses (COVID-19 scoring)")
        print(f"  • {bias_count} bias analysis")
        
        print("\n🎉 Your platform is now ready to showcase!")
        print("\n🌐 View at: http://localhost:3000")
        print("  → Dashboard shows statistics")
        print("  → Patients shows 2 analyzed cases")
        print("  → Click patient for full AI analysis")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

