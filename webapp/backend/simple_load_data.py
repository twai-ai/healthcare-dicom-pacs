"""
Simple Data Loader - Load showcase data reliably
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date

sys.path.append('/app')

from database import SessionLocal
import models
from object_storage import open_data_file


def _read_csv():
    with open_data_file("dicom_metadata.csv") as path:
        return pd.read_csv(path)


def _read_json(name):
    with open_data_file(name) as path:
        with open(path) as f:
            return json.load(f)

def main():
    db = SessionLocal()
    
    print("\n🎬 LOADING SHOWCASE DATA - 2 COVID-19 PATIENTS\n")
    
    # Step 1: Load patients from CSV
    print("Step 1: Loading patients...")
    df = _read_csv()
    print(f"  Columns in CSV: {list(df.columns)}")
    
    for _, row in df.iterrows():
        pid = row['patient_id']  # Note: lowercase in CSV
        
        # Create patient
        p = models.Patient(
            patient_id=pid,
            patient_name=row.get('patient_name'),
            patient_age=int(row['patient_age'].replace('Y', '')) if pd.notna(row.get('patient_age')) else None,
            patient_sex=row.get('patient_sex')
        )
        db.add(p)
        print(f"  ✓ {pid} ({row['patient_age']} {row['patient_sex']})")
        
        # Create study  
        s = models.Study(
            patient_id=pid,
            study_instance_uid=f"study-{pid}",  # Generate UID
            study_date=datetime.strptime(str(int(row['study_date'])), '%Y%m%d').date() if pd.notna(row.get('study_date')) else None,
            modality=row.get('modality'),
            body_part='CHEST',
            manufacturer=row.get('manufacturer'),
            study_description=row.get('study_description')
        )
        db.add(s)
    
    db.commit()
    print(f"✅ Committed {len(df)} patients\n")
    
    # Step 2: Load AI analyses
    print("Step 2: Loading AI analyses...")
    ai_data = _read_json("multimodel_ai_analysis_complete.json")
    count = 0
    
    for item in ai_data:
        pid = item['patient_id']
        study = db.query(models.Study).filter(models.Study.patient_id == pid).first()
        
        # Gemini
        gemini_text = item.get('individual_analyses', {}).get('gemini-2.0-flash', '')
        if gemini_text and 'Error' not in gemini_text[:50]:
            db.add(models.AIAnalysis(
                patient_id=pid,
                study_id=study.id if study else None,
                model_name="Google Gemini 2.0 Flash",
                analysis_type="vision",
                findings=gemini_text[:5000],  # Truncate if too long
                severity_assessment="Indeterminate"
            ))
            count += 1
        
        # Groq
        groq_text = item.get('individual_analyses', {}).get('llama-3.3-70b-versatile', '')
        if groq_text:
            db.add(models.AIAnalysis(
                patient_id=pid,
                study_id=study.id if study else None,
                model_name="Groq LLaMA 3.3 70B",
                analysis_type="vision",
                findings=groq_text[:5000],
                severity_assessment="Indeterminate"
            ))
            count += 1
        
        # Ensemble
        ensemble = item.get('ensemble_analysis', '')
        if ensemble:
            db.add(models.AIAnalysis(
                patient_id=pid,
                study_id=study.id if study else None,
                model_name="Multi-Model Ensemble",
                analysis_type="ensemble",
                findings=ensemble[:5000],
                severity_assessment="Indeterminate"
            ))
            count += 1
    
    db.commit()
    print(f"✅ Committed {count} AI analyses\n")
    
    # Step 3: Load diagnostic analyses
    print("Step 3: Loading diagnostic analyses...")
    diag_data = _read_json("diagnostic_assessments_complete.json")
    count = 0
    
    for item in diag_data:
        pid = item['patient_id']
        study = db.query(models.Study).filter(models.Study.patient_id == pid).first()
        covid = item.get('covid19_assessment', {})
        
        db.add(models.DiagnosticAnalysis(
            patient_id=pid,
            study_id=study.id if study else None,
            covid_score=covid.get('score'),
            covid_probability=covid.get('classification', 'Unknown'),
            severity=covid.get('severity_estimate', 'Unknown'),
            confidence=item.get('confidence_level', 'Unknown'),
            clinical_reasoning=covid.get('classification', ''),
            recommendations='\n'.join(item.get('recommendations', [])),
            differential_diagnosis=', '.join(item.get('differential_diagnosis', [])),
            quantitative_features=item.get('quantitative_features', {})
        ))
        count += 1
    
    db.commit()
    print(f"✅ Committed {count} diagnostic analyses\n")
    
    # Step 4: Load bias analysis
    print("Step 4: Loading bias analysis...")
    bias_data = _read_json("bias_analysis_report.json")
    
    db.add(models.BiasAnalysis(
        analysis_date=date.today(),
        total_patients=2,
        total_studies=2,
        manufacturer_diversity=0.5,
        protocol_diversity=0.5,
        bias_risk_level=bias_data.get('risk_level', 'HIGH'),
        bias_score=bias_data.get('bias_score', 0.5),
        recommendations=bias_data.get('recommendations', ''),
        metrics_json=bias_data
    ))
    db.commit()
    print(f"✅ Committed bias analysis\n")
    
    # Summary
    print("="*70)
    print("✅ SHOWCASE DATA LOADED SUCCESSFULLY!")
    print("="*70)
    print(f"\nDatabase now has:")
    print(f"  • 2 COVID-19 patients")
    print(f"  • 2 studies (chest X-rays)")
    print(f"  • {db.query(models.AIAnalysis).count()} AI analyses")
    print(f"  • 2 diagnostic analyses")  
    print(f"  • 1 bias analysis")
    print("\n🎉 Your web app is now ready to showcase!")
    print("🌐 View at: http://localhost:3000\n")
    
    db.close()

if __name__ == "__main__":
    # Clear existing data first
    db = SessionLocal()
    print("Clearing existing data...")
    db.query(models.AIAnalysis).delete()
    db.query(models.DiagnosticAnalysis).delete()
    db.query(models.BiasAnalysis).delete()
    db.query(models.Study).delete()
    db.query(models.Patient).delete()
    db.commit()
    db.close()
    
    # Load fresh data
    main()

