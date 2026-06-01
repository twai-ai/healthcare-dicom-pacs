"""
Analysis Engine - Core analysis functionality integrated into backend
Combines all analysis logic from test-code into web-accessible API
"""

import os
import json
import numpy as np
import pandas as pd
import pydicom
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
from groq import Groq
import base64
from PIL import Image
import io
from image_processor import ImageProcessor

class DICOMAnalyzer:
    """Main analysis engine combining all analysis capabilities"""
    
    def __init__(self, gemini_api_key: str = None, groq_api_key: str = None):
        """Initialize with API keys"""
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        
        # Initialize AI clients if keys provided
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except Exception as e:
                print(f"Warning: Gemini initialization failed: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
            
        if self.groq_api_key:
            try:
                # Groq client - simple initialization without proxies
                import httpx
                self.groq_client = Groq(
                    api_key=self.groq_api_key,
                    http_client=httpx.Client(timeout=60.0)
                )
            except Exception as e:
                print(f"Warning: Groq initialization failed: {e}")
                self.groq_client = None
        else:
            self.groq_client = None
    
    # ========================================================================
    # DICOM PROCESSING
    # ========================================================================
    
    def extract_metadata(self, dicom_file: Path) -> Dict:
        """Extract comprehensive metadata from DICOM file"""
        try:
            ds = pydicom.dcmread(dicom_file)
            
            metadata = {
                'patient_id': str(ds.get('PatientID', 'Unknown')),
                'patient_name': str(ds.get('PatientName', 'Unknown')),
                'patient_age': self._parse_age(ds.get('PatientAge', '')),
                'patient_sex': str(ds.get('PatientSex', 'Unknown')),
                'study_date': str(ds.get('StudyDate', '')),
                'study_description': str(ds.get('StudyDescription', '')),
                'modality': str(ds.get('Modality', '')),
                'body_part': str(ds.get('BodyPartExamined', '')),
                'manufacturer': str(ds.get('Manufacturer', '')),
                'manufacturer_model': str(ds.get('ManufacturerModelName', '')),
                'study_instance_uid': str(ds.get('StudyInstanceUID', '')),
                'series_instance_uid': str(ds.get('SeriesInstanceUID', '')),
                'sop_instance_uid': str(ds.get('SOPInstanceUID', '')),
                'rows': int(ds.get('Rows', 0)),
                'columns': int(ds.get('Columns', 0)),
            }
            
            # Extract pixel data for analysis
            if hasattr(ds, 'pixel_array'):
                pixel_array = ds.pixel_array
                metadata['image_stats'] = {
                    'mean': float(np.mean(pixel_array)),
                    'std': float(np.std(pixel_array)),
                    'min': float(np.min(pixel_array)),
                    'max': float(np.max(pixel_array)),
                    'median': float(np.median(pixel_array)),
                }
            
            return metadata
            
        except Exception as e:
            return {'error': str(e)}
    
    def _parse_age(self, age_str: str) -> Optional[int]:
        """Parse DICOM age string"""
        if not age_str:
            return None
        try:
            if 'Y' in age_str:
                return int(age_str.replace('Y', ''))
            return int(age_str)
        except:
            return None
    
    def dicom_to_image(self, dicom_file: Path) -> Optional[Image.Image]:
        """Convert DICOM to PIL Image for AI analysis"""
        try:
            ds = pydicom.dcmread(dicom_file)
            pixel_array = ds.pixel_array
            
            # Normalize to 0-255
            pixel_array = ((pixel_array - pixel_array.min()) / 
                          (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            
            return Image.fromarray(pixel_array)
        except Exception as e:
            print(f"Error converting DICOM: {e}")
            return None
    
    # ========================================================================
    # DATA-DRIVEN DIAGNOSTIC ANALYSIS
    # ========================================================================
    
    def analyze_diagnostic(self, metadata: Dict, image_stats: Dict) -> Dict:
        """Data-driven diagnostic assessment based on quantitative features"""
        
        covid_score = 0
        reasoning = []
        
        # Analyze image statistics
        mean_intensity = image_stats.get('mean', 0)
        std_intensity = image_stats.get('std', 0)
        
        # Rule-based COVID-19 assessment
        if mean_intensity > 800:
            covid_score += 1
            reasoning.append("Elevated mean intensity suggests increased opacity")
        
        if std_intensity > 400:
            covid_score += 1
            reasoning.append("High intensity variance indicates heterogeneous infiltrates")
        
        # Classify based on score
        if covid_score <= 1:
            probability = "LOW"
            severity = "None or Minimal"
            confidence = "HIGH"
        elif covid_score == 2:
            probability = "MODERATE"
            severity = "Mild"
            confidence = "MODERATE"
        elif covid_score == 3:
            probability = "MODERATE"
            severity = "Moderate"
            confidence = "MODERATE"
        else:
            probability = "HIGH"
            severity = "Severe"
            confidence = "HIGH"
        
        return {
            'covid_score': covid_score,
            'covid_probability': probability,
            'severity': severity,
            'confidence': confidence,
            'clinical_reasoning': ' '.join(reasoning) if reasoning else 'Minimal COVID-19 features detected',
            'recommendations': self._get_recommendations(covid_score),
            'quantitative_features': image_stats
        }
    
    def _get_recommendations(self, score: int) -> str:
        """Generate clinical recommendations based on score"""
        if score <= 1:
            return "No immediate COVID-19 concerns. Clinical correlation advised."
        elif score <= 2:
            return "Consider COVID-19 testing. Monitor for symptom progression."
        elif score == 3:
            return "High suspicion for COVID-19. Immediate testing and clinical evaluation recommended."
        else:
            return "Very high suspicion for COVID-19. Urgent evaluation and potential hospitalization."
    
    # ========================================================================
    # AI ANALYSIS (GEMINI)
    # ========================================================================
    
    def analyze_with_gemini(self, image: Image.Image, metadata: Dict) -> Dict:
        """Analyze with Google Gemini"""
        if not self.gemini_model:
            return {'error': 'Gemini API key not configured'}
        
        try:
            # Convert PIL Image to bytes in a format Gemini accepts
            import io
            
            # Ensure image is in RGB mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to bytes buffer as JPEG (more compatible than PNG)
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            
            # Load from buffer for Gemini
            from PIL import Image as PILImage
            gemini_image = PILImage.open(buffer)
            
            prompt = f"""You are an expert radiologist. Analyze this medical chest X-ray image.

Patient Information:
- Age: {metadata.get('patient_age', 'Unknown')} years
- Sex: {metadata.get('patient_sex', 'Unknown')}
- Modality: {metadata.get('modality', 'Unknown')}
- View: {metadata.get('body_part', 'CHEST')}

Provide a structured radiology report with:

1. TECHNIQUE & QUALITY
- Image quality
- Positioning
- Technical adequacy

2. FINDINGS
- Lungs (clarity, infiltrates, consolidations)
- Heart (size, borders, cardiothoracic ratio)
- Mediastinum (width, contours)
- Pleura (effusions, pneumothorax)
- Bones (ribs, clavicles, spine)

3. COVID-19 ASSESSMENT
- Classification (Positive/Negative/Indeterminate)
- Severity (if applicable)
- Key features

4. IMPRESSION
- Summary of findings

5. RECOMMENDATIONS
- Follow-up needed
- Additional studies

Use plain text only, no markdown symbols."""

            response = self.gemini_model.generate_content([prompt, gemini_image])
            
            return {
                'model': 'Google Gemini 2.0 Flash',
                'analysis': response.text,
                'status': 'success'
            }
            
        except Exception as e:
            return {'error': f'Gemini Error: {str(e)}', 'model': 'Gemini'}
    
    # ========================================================================
    # AI ANALYSIS (GROQ)
    # ========================================================================
    
    def analyze_with_groq(self, image: Image.Image, metadata: Dict) -> Dict:
        """Analyze with Groq LLaMA"""
        if not self.groq_client:
            return {'error': 'Groq API key not configured'}
        
        try:
            # Groq text-based analysis with image statistics
            prompt = f"""You are an expert radiologist analyzing a chest X-ray.

PATIENT INFORMATION:
- Age: {metadata.get('patient_age', 'Unknown')} years
- Sex: {metadata.get('patient_sex', 'Unknown')}
- Modality: {metadata.get('modality', 'Unknown')}
- View: {metadata.get('study_description', 'Chest X-ray')}

IMAGE STATISTICS:
- Mean Intensity: {metadata.get('image_stats', {}).get('mean', 'N/A')}
- Std Deviation: {metadata.get('image_stats', {}).get('std', 'N/A')}
- Intensity Range: {metadata.get('image_stats', {}).get('min', 0)} - {metadata.get('image_stats', {}).get('max', 0)}

Based on these quantitative metrics and clinical context, provide a structured radiology report:

1. TECHNIQUE & QUALITY
2. FINDINGS (based on intensity patterns)
3. COVID-19 ASSESSMENT
4. IMPRESSION
5. RECOMMENDATIONS

Use plain text, no markdown symbols, no asterisks."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            return {
                'model': 'Groq LLaMA 3.3 70B',
                'analysis': response.choices[0].message.content,
                'status': 'success'
            }
            
        except Exception as e:
            return {'error': f'Groq Error: {str(e)}', 'model': 'Groq'}
    
    # ========================================================================
    # MULTI-MODEL ENSEMBLE
    # ========================================================================
    
    def analyze_multimodel(self, image: Image.Image, metadata: Dict) -> Dict:
        """Run analysis with all available models and create ensemble"""
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'patient_id': metadata.get('patient_id'),
            'models': {}
        }
        
        # Run Gemini
        if self.gemini_model:
            results['models']['gemini'] = self.analyze_with_gemini(image, metadata)
        
        # Run Groq
        if self.groq_client:
            results['models']['groq'] = self.analyze_with_groq(image, metadata)
        
        # Create ensemble summary
        if results['models']:
            results['ensemble'] = self._create_ensemble_summary(results['models'])
        else:
            results['error'] = 'No AI models configured'
        
        return results
    
    def _create_ensemble_summary(self, model_results: Dict) -> Dict:
        """Create consensus from multiple model outputs"""
        
        analyses = [r.get('analysis', '') for r in model_results.values() if 'analysis' in r]
        
        if not analyses:
            return {'consensus': 'No analyses available'}
        
        return {
            'consensus': 'Multiple models analyzed. See individual results.',
            'models_used': list(model_results.keys()),
            'agreement': 'Review individual analyses for consensus'
        }
    
    # ========================================================================
    # COMPLETE ANALYSIS PIPELINE
    # ========================================================================
    
    def analyze_complete(self, dicom_file: Path) -> Dict:
        """Run complete analysis pipeline on a DICOM file"""
        
        print(f"\n🔬 Analyzing: {dicom_file.name}")
        
        results = {
            'file': str(dicom_file),
            'timestamp': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        try:
            # 1. Extract metadata
            print("  📋 Extracting metadata...")
            metadata = self.extract_metadata(dicom_file)
            results['metadata'] = metadata
            
            if 'error' in metadata:
                results['status'] = 'error'
                results['error'] = metadata['error']
                return results
            
            # 2. Generate images and visualizations
            print("  🖼️  Generating images and visualizations...")
            images = ImageProcessor.generate_analysis_images(str(dicom_file))
            results['images'] = images
            
            # 3. Data-driven diagnostic analysis
            print("  🔬 Running diagnostic analysis...")
            diagnostic = self.analyze_diagnostic(
                metadata, 
                metadata.get('image_stats', {})
            )
            results['diagnostic'] = diagnostic
            
            # 4. Convert to image for AI
            print("  🖼️  Converting to image for AI...")
            image = self.dicom_to_image(dicom_file)
            
            if image:
                # 5. Multi-model AI analysis
                print("  🤖 Running AI analysis...")
                ai_results = self.analyze_multimodel(image, metadata)
                results['ai_analysis'] = ai_results
            else:
                results['ai_analysis'] = {'error': 'Could not convert DICOM to image'}
            
            results['status'] = 'complete'
            print("  ✅ Analysis complete!")
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            print(f"  ✗ Error: {e}")
        
        return results

# ============================================================================
# BATCH PROCESSING
# ============================================================================

def analyze_batch(dicom_files: List[Path], analyzer: DICOMAnalyzer) -> Dict:
    """Analyze multiple DICOM files"""
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(dicom_files),
        'analyses': []
    }
    
    for dicom_file in dicom_files:
        result = analyzer.analyze_complete(dicom_file)
        results['analyses'].append(result)
    
    return results

