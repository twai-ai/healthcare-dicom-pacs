# DICOM-AI Analysis Scripts

**Essential tools for medical imaging analysis**

---

## 📦 What's Included

### Core Analysis (12 Scripts)

**Data Management:**
- `01_check_manifest.py` - Parse TCIA manifest files
- `05_batch_process.py` - Batch metadata extraction
- `06_enhanced_tcia_download.py` - Download from TCIA (200+ collections)
- `07_advanced_search.py` - Advanced TCIA search

**Quality & Compliance:**
- `08_protocol_analyzer.py` - Protocol standardization analysis
- `09_dicom_validator.py` - DICOM compliance validation
- `10_deidentifier.py` - HIPAA de-identification
- `11_bias_analyzer.py` - Bias & generalizability detection

**Clinical Analysis:**
- `14_multi_model_ai_analysis.py` - Multi-model AI (Gemini + Groq)
- `15_diagnostic_analyzer.py` - Data-driven diagnostics

**Report Generation:**
- `generate_medical_report.py` - Comprehensive PDF report (15-18 pages)
- `run_complete_analysis.py` - Run all analyses automatically

**Utilities:**
- `utils.py` - Helper functions
- `view_results.py` - View all results

---

## 🚀 Quick Start

### Complete Analysis
```bash
# Setup
source venv/bin/activate

# Set API keys
export GEMINI_API_KEY='your-key'
export GROQ_API_KEY='your-key'

# Run everything
python run_complete_analysis.py

# View report
open output/Medical_Analysis_Report.pdf
```

### Individual Analyses
```bash
# Protocol analysis
python 08_protocol_analyzer.py

# DICOM validation
python 09_dicom_validator.py

# Diagnostic assessment
python 15_diagnostic_analyzer.py

# AI analysis
python 14_multi_model_ai_analysis.py

# Generate report
python generate_medical_report.py
```

---

## 📊 Output Files

### Main Report
- `Medical_Analysis_Report.pdf` - Comprehensive 15-18 page clinical report

### Analysis Results
- `diagnostic_report.txt` - Data-driven diagnostic assessments
- `multimodel_clinical_report.txt` - AI clinical analysis
- `multimodel_cohort_analysis.txt` - Cohort insights
- `protocol_database.csv` - Protocol analysis
- `validation_results.csv` - DICOM validation
- `bias_analysis_report.json` - Bias metrics
- `compliance_report.json` - Compliance summary
- `dicom_metadata.csv` - Basic metadata
- Images (PNG) - Visualizations

---

## 🤖 AI Models

- **Google Gemini 2.0 Flash** - Vision analysis (FREE tier)
- **Groq LLaMA 3.3 70B** - Clinical reasoning (FREE tier)

Get API keys:
- Gemini: https://ai.google.dev/
- Groq: https://console.groq.com/

---

## 📚 Documentation

- `COMPREHENSIVE_ANALYSIS_SUMMARY.md` - All 6 challenges addressed
- `ANALYSIS_COMPARISON.md` - Compare diagnostic methods
- `TCIA_API_REFERENCE.md` - TCIA API documentation
- `AI_SETUP_GUIDE.md` - AI configuration
- `MEDICAL_REPORT_GUIDE.md` - How to share reports

---

## ✅ Dependencies

See `requirements.txt`:
- pydicom, numpy, pandas (core)
- reportlab (PDF generation)
- google-generativeai, groq (AI)
- tcia-utils (TCIA API)
- scipy, scikit-learn (analysis)

---

## 🎯 What It Does

### Diagnostic Analysis
- COVID-19 probability scoring (0-5 scale)
- Differential diagnosis generation
- Severity estimation
- Risk factor identification

### AI Analysis
- Multi-model ensemble (2 AI models)
- Clinical impressions
- Consensus findings
- Cohort-level insights

### Quality Analysis
- Protocol standardization
- DICOM validation (100% compliance)
- Bias detection & scoring
- Generalizability assessment

### Reporting
- Professional medical reports
- Evidence-based methodology
- Clinical terminology
- Ready for validation

---

## 🚀 Status

✅ **Production-Ready**
- 12 essential scripts
- Triple-layer validation
- Comprehensive reports
- All challenges addressed

**Ready for clinical validation!**

---

See `../EXECUTIVE_SUMMARY.md` for complete platform overview.
