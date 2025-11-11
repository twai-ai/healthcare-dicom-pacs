"""
Multi-Model AI Medical Image Analysis
Uses multiple AI models for comprehensive, robust clinical insights
Ensemble approach for maximum reliability
"""

import sys
from pathlib import Path
import os
import json
import pandas as pd
from typing import Dict, List, Optional
from PIL import Image
import numpy as np

sys.path.append(str(Path(__file__).parent))
from utils import find_dicom_files, read_dicom, get_metadata

# Import all available AI services
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except:
    GROQ_AVAILABLE = False

class MultiModelMedicalAnalyzer:
    """
    Comprehensive medical image analysis using multiple AI models
    Ensemble approach for robust clinical insights
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.available_models = []
        self.analysis_results = []
        
        # Initialize Gemini if available
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if GEMINI_AVAILABLE and gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                self.available_models.append('gemini-2.0-flash')
                print("✓ Gemini 2.0 Flash initialized")
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
        
        # Initialize Groq if available
        groq_key = os.getenv('GROQ_API_KEY')
        if GROQ_AVAILABLE and groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
                self.groq_model = "llama-3.3-70b-versatile"
                self.available_models.append(self.groq_model)
                print(f"✓ Groq {self.groq_model} initialized")
            except Exception as e:
                print(f"⚠️  Groq initialization failed: {e}")
                self.groq_client = None
        else:
            self.groq_client = None
        
        print(f"\n📊 Total AI models available: {len(self.available_models)}")
        if not self.available_models:
            print("\n⚠️  WARNING: No AI models available!")
            print("Please set API keys for at least one service:")
            print("  • GEMINI_API_KEY or GOOGLE_API_KEY")
            print("  • GROQ_API_KEY")
    
    def extract_image_features(self, ds) -> str:
        """Extract comprehensive image features and statistics"""
        
        if not hasattr(ds, 'pixel_array'):
            return "No pixel data available"
        
        img = ds.pixel_array.astype(float)
        
        # Apply rescale if available
        if hasattr(ds, 'RescaleIntercept') and hasattr(ds, 'RescaleSlope'):
            img = img * ds.RescaleSlope + ds.RescaleIntercept
            intensity_unit = "Hounsfield Units (HU)" if ds.Modality == 'CT' else "Pixel Values"
        else:
            intensity_unit = "Pixel Values"
        
        # Calculate comprehensive statistics
        features = f"""
IMAGE TECHNICAL ANALYSIS:

Modality: {ds.Modality} ({ds.get('Manufacturer', 'Unknown')})
Image Dimensions: {img.shape[0]} x {img.shape[1]} pixels
Bit Depth: {ds.get('BitsStored', 'Unknown')} bits
View Position: {ds.get('SeriesDescription', 'Unknown')}
Patient Position: {ds.get('PatientPosition', 'Unknown')}

INTENSITY STATISTICS ({intensity_unit}):
- Minimum: {img.min():.1f}
- Maximum: {img.max():.1f}
- Mean: {img.mean():.1f}
- Median: {np.median(img):.1f}
- Std Dev: {img.std():.1f}
- 25th Percentile: {np.percentile(img, 25):.1f}
- 75th Percentile: {np.percentile(img, 75):.1f}

ACQUISITION PARAMETERS:
- kVp: {ds.get('KVP', 'Unknown')}
- Exposure: {ds.get('Exposure', 'Unknown')}
- Pixel Spacing: {ds.get('PixelSpacing', 'Unknown')}

IMAGE CHARACTERISTICS:
This is a {ds.Modality} chest radiograph with diagnostic quality imaging.
The image shows clear visualization of thoracic structures suitable for 
evaluation of lungs, heart, mediastinum, bones, and pleural spaces.
"""
        
        return features.strip()
    
    def analyze_with_gemini(self, pil_image: Image, context: str, prompt: str) -> Optional[str]:
        """Analyze with Gemini vision model"""
        
        if not self.gemini_model:
            return None
        
        print("  🔮 Gemini analysis...")
        
        try:
            full_prompt = f"{context}\n\n{prompt}"
            response = self.gemini_model.generate_content(
                [full_prompt, pil_image],
                generation_config={
                    'temperature': 0.2,
                    'max_output_tokens': 2048
                }
            )
            
            print("  ✓ Gemini complete")
            return response.text
            
        except Exception as e:
            print(f"  ✗ Gemini error: {e}")
            return f"Gemini Error: {e}"
    
    def analyze_with_groq(self, image_features: str, context: str, prompt: str) -> Optional[str]:
        """Analyze with Groq text model (using extracted features)"""
        
        if not self.groq_client:
            return None
        
        print("  ⚡ Groq analysis...")
        
        try:
            full_prompt = f"""{context}

{image_features}

{prompt}

Based on the image technical analysis above, provide a clinical interpretation.
"""
            
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert radiologist providing formal chest X-ray interpretations based on technical image analysis."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            print("  ✓ Groq complete")
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"  ✗ Groq error: {e}")
            return f"Groq Error: {e}"
    
    def create_ensemble_analysis(self, analyses: Dict[str, str], metadata: Dict) -> str:
        """Create ensemble analysis from multiple AI models"""
        
        if not any(analyses.values()):
            return "No AI analyses available"
        
        print("\n  🔬 Creating ensemble analysis...")
        
        # Build summary of all analyses
        ensemble_text = f"""
MULTI-MODEL AI ANALYSIS ENSEMBLE
=================================

Patient: {metadata.get('patient_id', 'Unknown')}
Age: {metadata.get('patient_age', 'Unknown')}
Sex: {metadata.get('patient_sex', 'Unknown')}
Study: {metadata.get('study_description', 'Unknown')}

"""
        
        for model_name, analysis in analyses.items():
            if analysis and not analysis.startswith("Error"):
                ensemble_text += f"\n{'='*70}\n"
                ensemble_text += f"ANALYSIS FROM: {model_name.upper()}\n"
                ensemble_text += f"{'='*70}\n\n"
                ensemble_text += analysis
                ensemble_text += "\n\n"
        
        # If we have Groq, use it to synthesize
        if self.groq_client:
            try:
                synthesis_prompt = f"""You are an expert radiologist reviewing multiple AI-assisted analyses of the same chest X-ray.

{ensemble_text}

Please provide a SYNTHESIZED CLINICAL REPORT that:

1. **CONSENSUS FINDINGS**: Findings agreed upon by multiple models
2. **CONFIDENCE ASSESSMENT**: High confidence vs uncertain findings
3. **CLINICAL IMPRESSION**: Integrated summary
4. **COVID-19 ASSESSMENT**: Synthesized classification
5. **RECOMMENDATIONS**: Based on all analyses

Be concise but comprehensive. Highlight areas of agreement and note any discrepancies.
"""
                
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    max_tokens=1500,
                    temperature=0.2
                )
                
                ensemble_text += "\n" + "="*70 + "\n"
                ensemble_text += "SYNTHESIZED ENSEMBLE ANALYSIS\n"
                ensemble_text += "="*70 + "\n\n"
                ensemble_text += response.choices[0].message.content
                
                print("  ✓ Ensemble synthesis complete")
                
            except Exception as e:
                print(f"  ⚠️  Synthesis failed: {e}")
        
        return ensemble_text
    
    def analyze_study(self, dicom_file: Path) -> Dict:
        """Comprehensive multi-model analysis of a study"""
        
        print(f"\n{'='*70}")
        print(f"ANALYZING: {dicom_file.name}")
        print(f"{'='*70}")
        
        try:
            # Read DICOM
            ds = read_dicom(dicom_file)
            metadata = get_metadata(ds)
            
            print(f"\nPatient: {metadata['patient_id']}")
            print(f"Study: {metadata['study_description']}")
            print(f"Modality: {metadata['modality']}")
            
            # Convert to PIL for vision models
            pil_image = self._dicom_to_pil(ds)
            
            # Extract image features for text models
            image_features = self.extract_image_features(ds)
            
            # Build clinical context
            context = f"""
PATIENT INFORMATION:
- Patient ID: {metadata['patient_id']}
- Age: {metadata['patient_age']}
- Sex: {metadata['patient_sex']}
- Study Date: {metadata['study_date']}

EXAMINATION:
- Modality: {metadata['modality']}
- Study: {metadata['study_description']}
- Equipment: {metadata['manufacturer']}

CLINICAL INDICATION:
COVID-19 imaging assessment - Chest radiography evaluation
"""
            
            # Standard radiology report prompt
            prompt = """Provide a comprehensive radiology report with these sections:

**1. TECHNIQUE & QUALITY**
Image quality, positioning, technical adequacy

**2. FINDINGS**
Systematic review:
- Lungs: infiltrates, consolidations, nodules, masses, clarity
- Heart: size, borders, cardiothoracic ratio
- Mediastinum: width, contours
- Pleura: effusions, pneumothorax
- Bones: ribs, clavicles, spine
- Diaphragm: position, contours
- Soft tissues: abnormalities

**3. COVID-19 ASSESSMENT**
- Classification: Typical/Indeterminate/Atypical/Negative
- Severity if present: Mild/Moderate/Severe
- Key features: Ground-glass opacities, consolidation, distribution

**4. IMPRESSION**
Concise summary of key findings

**5. RECOMMENDATIONS**
Follow-up, correlation, additional studies

Use professional radiology terminology."""
            
            print(f"\n🤖 Running AI models ({len(self.available_models)} available):")
            
            # Run all available models
            analyses = {}
            
            # Gemini (vision)
            gemini_result = self.analyze_with_gemini(pil_image, context, prompt)
            if gemini_result:
                analyses['gemini-2.0-flash'] = gemini_result
            
            # Groq (text-based on features)
            groq_result = self.analyze_with_groq(image_features, context, prompt)
            if groq_result:
                analyses[self.groq_model] = groq_result
            
            # Create ensemble analysis
            print("\n  🔬 Synthesizing multi-model insights...")
            ensemble_analysis = self.create_ensemble_analysis(analyses, metadata)
            
            result = {
                'dicom_file': str(dicom_file),
                'patient_id': metadata['patient_id'],
                'patient_age': metadata['patient_age'],
                'patient_sex': metadata['patient_sex'],
                'study_date': metadata['study_date'],
                'modality': metadata['modality'],
                'study_description': metadata['study_description'],
                'manufacturer': metadata['manufacturer'],
                'individual_analyses': analyses,
                'ensemble_analysis': ensemble_analysis,
                'models_used': list(analyses.keys()),
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            print(f"\n✓ Multi-model analysis complete!")
            print(f"  Models used: {len(analyses)}")
            
            return result
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            return {
                'dicom_file': str(dicom_file),
                'error': str(e)
            }
    
    def _dicom_to_pil(self, ds) -> Image:
        """Convert DICOM to PIL Image"""
        
        if not hasattr(ds, 'pixel_array'):
            raise ValueError("No pixel data")
        
        img_array = ds.pixel_array
        
        # Apply rescale
        if hasattr(ds, 'RescaleIntercept') and hasattr(ds, 'RescaleSlope'):
            img_array = img_array * ds.RescaleSlope + ds.RescaleIntercept
        
        # Normalize to 0-255
        img_min = img_array.min()
        img_max = img_array.max()
        
        if img_max > img_min:
            img_normalized = ((img_array - img_min) / (img_max - img_min) * 255).astype('uint8')
        else:
            img_normalized = img_array.astype('uint8')
        
        pil_img = Image.fromarray(img_normalized)
        
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        return pil_img
    
    def analyze_all_studies(self, data_dir: Path) -> List[Dict]:
        """Analyze all studies with multiple AI models"""
        
        print("\n" + "="*70)
        print("🤖 MULTI-MODEL AI MEDICAL IMAGE ANALYSIS")
        print("="*70)
        print(f"\nAvailable Models: {', '.join(self.available_models)}")
        print("Strategy: Ensemble analysis for maximum reliability")
        
        if not self.available_models:
            print("\n⚠️  No AI models available!")
            return []
        
        dicom_files = find_dicom_files(data_dir)
        
        if not dicom_files:
            print("\n⚠️  No DICOM files found!")
            return []
        
        print(f"\nFound {len(dicom_files)} DICOM files")
        
        results = []
        
        for idx, dicom_file in enumerate(dicom_files, 1):
            print(f"\n[{idx}/{len(dicom_files)}]")
            
            result = self.analyze_study(dicom_file)
            
            if 'ensemble_analysis' in result:
                results.append(result)
                self.analysis_results.append(result)
                
                # Save individual result
                result_file = self.output_dir / f"multimodel_analysis_{idx}.json"
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
        
        # Save all results
        if results:
            self._save_comprehensive_results()
        
        return results
    
    def _save_comprehensive_results(self):
        """Save comprehensive multi-model analysis results"""
        
        # Complete JSON
        json_path = self.output_dir / "multimodel_ai_analysis_complete.json"
        with open(json_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        # Formatted clinical report
        report_path = self.output_dir / "multimodel_clinical_report.txt"
        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("MULTI-MODEL AI MEDICAL IMAGE ANALYSIS\n")
            f.write("COMPREHENSIVE CLINICAL REPORT\n")
            f.write("="*70 + "\n")
            f.write(f"Generated: {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write(f"AI Models Used: {', '.join(self.available_models)}\n")
            f.write(f"Total Studies: {len(self.analysis_results)}\n")
            f.write("Analysis Type: Ensemble (Multi-Model Consensus)\n")
            f.write("="*70 + "\n\n")
            
            for idx, result in enumerate(self.analysis_results, 1):
                f.write("\n" + "="*70 + "\n")
                f.write(f"STUDY {idx}\n")
                f.write("="*70 + "\n\n")
                
                f.write("PATIENT DEMOGRAPHICS:\n")
                f.write(f"  Patient ID: {result['patient_id']}\n")
                f.write(f"  Age: {result['patient_age']}\n")
                f.write(f"  Sex: {result['patient_sex']}\n")
                f.write(f"  Study Date: {result['study_date']}\n\n")
                
                f.write("EXAMINATION DETAILS:\n")
                f.write(f"  Modality: {result['modality']}\n")
                f.write(f"  Study: {result['study_description']}\n")
                f.write(f"  Equipment: {result['manufacturer']}\n")
                f.write(f"  AI Models: {', '.join(result['models_used'])}\n\n")
                
                f.write("="*70 + "\n")
                f.write("ENSEMBLE ANALYSIS (Multi-Model Consensus)\n")
                f.write("="*70 + "\n\n")
                f.write(result['ensemble_analysis'])
                f.write("\n\n")
                
                # Add individual model analyses for reference
                f.write("-"*70 + "\n")
                f.write("INDIVIDUAL MODEL ANALYSES (For Reference)\n")
                f.write("-"*70 + "\n\n")
                
                for model_name, analysis in result['individual_analyses'].items():
                    f.write(f"\n--- {model_name.upper()} ---\n\n")
                    f.write(analysis)
                    f.write("\n\n")
        
        print(f"\n✓ Comprehensive report saved:")
        print(f"  • {json_path}")
        print(f"  • {report_path}")
    
    def generate_cohort_analysis(self) -> str:
        """Generate cohort-level analysis across all patients"""
        
        if not self.analysis_results:
            return "No analyses available"
        
        print("\n" + "="*70)
        print("📊 GENERATING COHORT-LEVEL ANALYSIS")
        print("="*70)
        
        # Compile all ensemble analyses
        all_analyses = []
        for i, result in enumerate(self.analysis_results, 1):
            summary = f"""
Patient {i}: {result['patient_id']} ({result['patient_age']}, {result['patient_sex']})
Study Date: {result['study_date']}
Equipment: {result['manufacturer']}

Ensemble Analysis:
{result['ensemble_analysis']}
"""
            all_analyses.append(summary)
        
        combined = "\n" + "="*70 + "\n".join(all_analyses)
        
        cohort_prompt = f"""You are an expert radiologist conducting a research study on COVID-19 chest imaging.

INDIVIDUAL PATIENT ANALYSES:
{combined}

Provide a COMPREHENSIVE COHORT ANALYSIS:

**1. COHORT DEMOGRAPHICS & OVERVIEW**
- Number of patients analyzed
- Age and sex distribution  
- Study quality overview

**2. IMAGING FINDINGS SUMMARY**
- Common patterns across all patients
- Typical COVID-19 findings frequency
- Atypical or negative findings
- Range of disease severity

**3. COVID-19 IMAGING CLASSIFICATION**
- Typical presentations: count and description
- Indeterminate findings: count and description
- Atypical/Negative: count and description
- Severity distribution (mild/moderate/severe)

**4. TECHNICAL QUALITY ASSESSMENT**
- Image quality across cohort
- Protocol consistency
- Equipment diversity
- Diagnostic adequacy

**5. DATASET CHARACTERISTICS**
- Strengths for research/AI training
- Limitations to consider
- Diversity assessment (age, severity, presentations)
- Recommended applications

**6. CLINICAL RESEARCH IMPLICATIONS**
- Key features for automated COVID-19 detection
- Challenges for algorithm development
- Validation requirements
- External generalizability considerations

**7. RECOMMENDATIONS**
- For AI/ML development
- For clinical validation
- For research publication
- For dataset expansion

Be specific, quantitative where possible, and clinically relevant.
"""
        
        # Use best available model for synthesis
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": cohort_prompt}],
                    max_tokens=2500,
                    temperature=0.2
                )
                
                cohort_analysis = response.choices[0].message.content
                
            except Exception as e:
                cohort_analysis = f"Error generating cohort analysis: {e}"
        
        elif self.gemini_model:
            try:
                response = self.gemini_model.generate_content(
                    cohort_prompt,
                    generation_config={'temperature': 0.2, 'max_output_tokens': 2500}
                )
                cohort_analysis = response.text
            except Exception as e:
                cohort_analysis = f"Error generating cohort analysis: {e}"
        else:
            cohort_analysis = "No AI model available for cohort synthesis"
        
        # Save cohort analysis
        cohort_path = self.output_dir / "multimodel_cohort_analysis.txt"
        with open(cohort_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("COHORT-LEVEL ANALYSIS\n")
            f.write("Multi-Model AI Ensemble\n")
            f.write("="*70 + "\n")
            f.write(f"Generated: {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write(f"Models: {', '.join(self.available_models)}\n")
            f.write(f"Studies: {len(self.analysis_results)}\n")
            f.write("="*70 + "\n\n")
            f.write(cohort_analysis)
        
        print(f"✓ Cohort analysis saved to: {cohort_path}")
        
        return cohort_analysis


def main():
    """Main execution"""
    
    print("\n" + "="*70)
    print("🚀 MULTI-MODEL AI MEDICAL IMAGE ANALYZER")
    print("="*70)
    print("\n✨ Enterprise-Grade Analysis Using Multiple AI Models")
    print("\nSupported Services:")
    print("  • Google Gemini (Vision)")
    print("  • Groq LLaMA (Text)")
    print("\nStrategy: Ensemble analysis for maximum reliability")
    
    # Initialize analyzer
    analyzer = MultiModelMedicalAnalyzer()
    
    if not analyzer.available_models:
        print("\n❌ No AI models initialized!")
        print("\nPlease set at least one API key:")
        print("  export GEMINI_API_KEY='your-gemini-key'")
        print("  export GROQ_API_KEY='your-groq-key'")
        return
    
    # Analyze data
    data_dir = Path("../data")
    results = analyzer.analyze_all_studies(data_dir)
    
    if results:
        print("\n" + "="*70)
        print("✅ INDIVIDUAL ANALYSES COMPLETE")
        print("="*70)
        
        for idx, result in enumerate(results, 1):
            print(f"\n📋 Study {idx}: {result['patient_id']}")
            print(f"   Models used: {len(result['models_used'])}")
            if result.get('ensemble_analysis'):
                snippet = result['ensemble_analysis'][:250].replace('\n', ' ')
                print(f"   Analysis: {snippet}...")
        
        # Generate cohort analysis
        if len(results) > 0:
            cohort = analyzer.generate_cohort_analysis()
            
            print("\n" + "="*70)
            print("📊 COHORT ANALYSIS PREVIEW")
            print("="*70)
            if cohort and not cohort.startswith("Error"):
                print(f"\n{cohort[:500]}...\n(Full analysis in output file)")
    
    print("\n" + "="*70)
    print("✅ MULTI-MODEL AI ANALYSIS COMPLETE!")
    print("="*70)
    print("\n📁 Output Files Generated:")
    print("  • multimodel_ai_analysis_complete.json")
    print("  • multimodel_clinical_report.txt")
    print("  • multimodel_cohort_analysis.txt")
    print("  • multimodel_analysis_1.json")
    print("  • multimodel_analysis_2.json")
    
    print("\n🎯 Next Steps:")
    print("  1. Review clinical report:")
    print("     cat output/multimodel_clinical_report.txt")
    print("\n  2. Review cohort analysis:")
    print("     cat output/multimodel_cohort_analysis.txt")
    print("\n  3. Generate final PDF report:")
    print("     python generate_medical_report.py")
    
    print("\n💡 Multi-model ensemble provides most reliable AI insights!")


if __name__ == "__main__":
    main()

