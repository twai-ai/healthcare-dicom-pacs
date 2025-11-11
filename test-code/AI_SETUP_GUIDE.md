# AI Analysis Setup Guide

**Status:** Framework ready, awaiting valid OpenAI API key

---

## 🔑 Getting Your OpenAI API Key

### Step 1: Create OpenAI Account
1. Visit: https://platform.openai.com/
2. Sign up or log in
3. Navigate to: https://platform.openai.com/account/api-keys

### Step 2: Generate API Key
1. Click "Create new secret key"
2. Name it: "DICOM-AI-Platform"
3. Copy the key (starts with `sk-proj-` or `sk-`)
4. **IMPORTANT:** Save it securely - you won't see it again!

### Step 3: Add Credits (if needed)
- OpenAI requires credits for API usage
- Go to: https://platform.openai.com/account/billing
- Add payment method and credits
- Recommended: Start with $5-10 for testing

### Estimated Costs
- GPT-4 Vision: ~$0.01-0.03 per image
- For 100 images: ~$1-3
- For 1000 images: ~$10-30

---

## ⚙️ Configuration

### Option 1: Environment Variable (Recommended)

```bash
# Add to your shell profile (~/.zshrc or ~/.bashrc)
export OPENAI_API_KEY='sk-proj-YOUR-ACTUAL-KEY-HERE'

# Or set temporarily
export OPENAI_API_KEY='sk-proj-YOUR-KEY'
```

### Option 2: .env File (Secure)

```bash
cd /Users/aeishwary/DICOM-AI/test-code

# Create .env file
cp .env.example .env

# Edit .env file and add your key
# OPENAI_API_KEY=sk-proj-YOUR-ACTUAL-KEY-HERE
```

Then use python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 3: Direct Parameter (Testing only)

```python
analyzer = AIImageAnalyzer(api_key='sk-proj-YOUR-KEY')
```

⚠️ **Never commit API keys to git!**

---

## 🚀 Running AI Analysis

### Basic Usage

```bash
cd /Users/aeishwary/DICOM-AI/test-code
source venv/bin/activate

# Set API key
export OPENAI_API_KEY='sk-proj-YOUR-ACTUAL-KEY'

# Run AI analysis
python 12_ai_image_analyzer.py
```

### What It Analyzes

For each chest X-ray:
1. **Technical Quality**
   - Image quality assessment
   - Positioning evaluation
   - Artifacts detection

2. **Anatomical Findings**
   - Lungs (infiltrates, consolidation, nodules)
   - Heart (size, borders)
   - Mediastinum (widening, masses)
   - Bones (fractures, lesions)
   - Pleural spaces (effusion, pneumothorax)
   - Diaphragm (elevation, contours)

3. **Clinical Impression**
   - Primary findings summary
   - Clinical significance
   - Severity assessment

4. **COVID-19 Specific** (if applicable)
   - Typical/atypical/negative findings
   - Severity scoring
   - Distribution patterns

5. **Recommendations**
   - Follow-up imaging
   - Clinical correlation
   - Additional studies needed

### Output Files

```
output/
├── ai_analysis_1.json               # Patient 1 analysis
├── ai_analysis_2.json               # Patient 2 analysis
├── ai_analysis_complete.json        # All analyses combined
├── ai_analysis_summary.txt          # Readable summary
└── ai_comparative_analysis.txt      # Multi-patient comparison
```

---

## 📊 AI Analysis Features

### Individual Patient Analysis
- Detailed radiology-style report
- Clinical terminology
- Structured findings
- Actionable recommendations

### Comparative Analysis (2+ patients)
- Pattern recognition across cohort
- Severity comparison
- Quality consistency check
- Research/training dataset suitability

### Integration with Medical Report
- AI findings included in PDF report
- Section: "AI-Assisted Clinical Analysis"
- Professional formatting
- Clear attribution to AI system

---

## 🎯 Use Cases

### 1. Clinical Decision Support
```python
# Analyze single study
result = analyzer.analyze_chest_xray(image_path, metadata)
print(result['analysis'])
```

### 2. Quality Assurance
```python
# Batch analyze for quality check
results = analyzer.analyze_all_images(data_dir)

# Identify suboptimal studies
for r in results:
    if 'poor quality' in r['analysis'].lower():
        print(f"Review needed: {r['patient_id']}")
```

### 3. Research Dataset Validation
```python
# Assess dataset suitability
comparative = analyzer.generate_comparison_analysis(results)

# Check for consistency, outliers, quality issues
```

### 4. Training Data Annotation
```python
# Use AI to pre-annotate images
# Human radiologist reviews and corrects
# Speeds up annotation process
```

---

## 🛡️ Important Considerations

### Medical Use Disclaimer
⚠️ **AI analysis is for research and quality assessment only**
- Not FDA-approved for clinical diagnosis
- Requires radiologist review and validation
- Should not replace physician judgment
- Use for research, education, QA purposes

### Data Privacy
✓ All images processed via secure API  
✓ No data stored by OpenAI (per their policy)  
✓ De-identify images before AI analysis  
✓ Comply with HIPAA/institutional policies  

### Quality Control
- Validate AI findings against expert reads
- Track accuracy over time
- Monitor for hallucinations or errors
- Use ensemble with other AI models

---

## 🔧 Troubleshooting

### Error: "Invalid API key"

**Solution:**
1. Verify key is correct (no extra spaces)
2. Check key starts with `sk-` or `sk-proj-`
3. Ensure account has credits
4. Generate new key if needed

### Error: "Rate limit exceeded"

**Solution:**
1. Add delays between API calls
2. Upgrade to higher tier plan
3. Process in smaller batches

### Error: "Image too large"

**Solution:**
1. Images auto-resized before upload
2. Check image encoding (PNG required)
3. Verify base64 conversion

---

## 📈 Next Steps

### Once API Key is Valid

1. **Run AI Analysis**
   ```bash
   python 12_ai_image_analyzer.py
   ```

2. **Review AI Findings**
   ```bash
   cat output/ai_analysis_summary.txt
   ```

3. **Generate Enhanced Report**
   ```bash
   python generate_medical_report.py
   ```

4. **Validate with Radiologist**
   - Compare AI findings with expert reads
   - Calculate agreement metrics
   - Refine prompts if needed

### Scale Up

1. **Process Larger Dataset**
   - Download 100+ images from TCIA
   - Run batch AI analysis
   - Generate cohort insights

2. **Build AI Models**
   - Use AI annotations as training labels
   - Train custom detection models
   - Fine-tune for COVID-19 specifics

3. **Clinical Integration**
   - Connect to PACS worklist
   - Auto-trigger AI analysis
   - Send results to RIS

---

## ✅ What's Ready

- ✅ AI analyzer framework complete
- ✅ GPT-4 Vision integration code ready
- ✅ Structured report generation
- ✅ Comparative analysis capability
- ✅ Integration with medical PDF report
- ⏳ Awaiting valid API key

---

## 💡 Alternative: Use Demo Mode

If you want to test without API key, I can create a demo mode that:
- Simulates AI analysis
- Uses pre-defined templates
- Tests the report generation
- Validates the workflow

Let me know if you need:
1. Help getting valid API key
2. Demo mode implementation
3. Alternative AI models (local models, other APIs)
4. Different analysis configurations

---

**Next:** Provide valid OpenAI API key to enable full AI analysis capabilities!

**File:** `/Users/aeishwary/DICOM-AI/test-code/12_ai_image_analyzer.py`  
**Status:** ✅ Ready to run with valid API key

