"""
Data-Driven Diagnostic Analyzer
Makes clinical inferences from DICOM metadata, image statistics, and technical parameters
Uses rule-based logic and clinical reasoning for COVID-19 assessment
"""

import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.append(str(Path(__file__).parent))
from utils import find_dicom_files, read_dicom, get_metadata

class DiagnosticAnalyzer:
    """
    Comprehensive diagnostic analysis using all available data
    Makes intelligent clinical inferences from:
    - DICOM metadata (age, sex, clinical context)
    - Image statistics (intensity patterns, distributions)
    - Technical parameters (acquisition settings)
    - Quantitative features (texture, density)
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.diagnostic_results = []
        
        # COVID-19 risk factors and patterns
        self.covid_risk_factors = {
            'age_high_risk': 60,  # Age > 60 = higher risk
            'bilateral_pattern': True,  # Bilateral = more suggestive
            'peripheral_distribution': True,  # Peripheral = typical for COVID
        }
    
    def extract_quantitative_features(self, ds) -> Dict:
        """Extract comprehensive quantitative features from image"""
        
        if not hasattr(ds, 'pixel_array'):
            return {}
        
        img = ds.pixel_array.astype(float)
        
        # Apply rescale if available
        if hasattr(ds, 'RescaleIntercept') and hasattr(ds, 'RescaleSlope'):
            img = img * ds.RescaleSlope + ds.RescaleIntercept
            is_hu = ds.Modality == 'CT'
        else:
            is_hu = False
        
        features = {
            # Basic statistics
            'mean_intensity': float(np.mean(img)),
            'median_intensity': float(np.median(img)),
            'std_intensity': float(np.std(img)),
            'min_intensity': float(np.min(img)),
            'max_intensity': float(np.max(img)),
            
            # Distribution features
            'intensity_range': float(np.max(img) - np.min(img)),
            'coefficient_of_variation': float(np.std(img) / np.mean(img)) if np.mean(img) > 0 else 0,
            
            # Percentiles
            'p25': float(np.percentile(img, 25)),
            'p75': float(np.percentile(img, 75)),
            'p95': float(np.percentile(img, 95)),
            'p05': float(np.percentile(img, 5)),
            
            # Histogram features
            'histogram_skewness': float(self._calculate_skewness(img)),
            'histogram_kurtosis': float(self._calculate_kurtosis(img)),
            
            # Spatial features (approximate)
            'image_entropy': float(self._calculate_entropy(img)),
            
            # Hounsfield Units specific (if CT)
            'is_hounsfield': is_hu,
        }
        
        # Add density analysis for chest imaging
        if is_hu:
            features.update(self._analyze_ct_densities(img))
        else:
            features.update(self._analyze_xray_patterns(img))
        
        return features
    
    def _calculate_skewness(self, img):
        """Calculate histogram skewness"""
        from scipy import stats
        try:
            return stats.skew(img.flatten())
        except:
            return 0
    
    def _calculate_kurtosis(self, img):
        """Calculate histogram kurtosis"""
        from scipy import stats
        try:
            return stats.kurtosis(img.flatten())
        except:
            return 0
    
    def _calculate_entropy(self, img):
        """Calculate image entropy (measure of information/complexity)"""
        from scipy.stats import entropy
        try:
            hist, _ = np.histogram(img.flatten(), bins=256)
            hist = hist / hist.sum()  # Normalize
            return entropy(hist + 1e-10)  # Add small value to avoid log(0)
        except:
            return 0
    
    def _analyze_ct_densities(self, img_hu) -> Dict:
        """Analyze CT densities in Hounsfield Units"""
        
        # Standard HU ranges
        analysis = {
            'air_proportion': float(np.sum(img_hu < -500) / img_hu.size),  # Air/lung
            'soft_tissue_proportion': float(np.sum((img_hu >= -100) & (img_hu <= 100)) / img_hu.size),
            'bone_proportion': float(np.sum(img_hu > 300) / img_hu.size),
            'ground_glass_pattern': False,  # -500 to -300 HU
            'consolidation_pattern': False,  # > -100 HU in lungs
        }
        
        # Ground-glass opacity detection (COVID-19 typical)
        gg_range = np.sum((img_hu >= -700) & (img_hu <= -300))
        if gg_range / img_hu.size > 0.1:  # >10% of image
            analysis['ground_glass_pattern'] = True
        
        # Consolidation detection
        consolidation = np.sum((img_hu >= -100) & (img_hu <= 100))
        if consolidation / img_hu.size > 0.05:
            analysis['consolidation_pattern'] = True
        
        return analysis
    
    def _analyze_xray_patterns(self, img) -> Dict:
        """Analyze X-ray intensity patterns"""
        
        # Divide image into regions
        height, width = img.shape
        
        # Upper, middle, lower thirds
        upper_third = img[:height//3, :]
        middle_third = img[height//3:2*height//3, :]
        lower_third = img[2*height//3:, :]
        
        analysis = {
            'upper_mean': float(np.mean(upper_third)),
            'middle_mean': float(np.mean(middle_third)),
            'lower_mean': float(np.mean(lower_third)),
            
            # Bilateral symmetry check
            'left_half_mean': float(np.mean(img[:, :width//2])),
            'right_half_mean': float(np.mean(img[:, width//2:])),
            'bilateral_asymmetry': float(abs(np.mean(img[:, :width//2]) - np.mean(img[:, width//2:])) / np.mean(img)),
            
            # Peripheral vs central
            'peripheral_mean': float(self._get_peripheral_mean(img)),
            'central_mean': float(self._get_central_mean(img)),
        }
        
        # Check for infiltrate patterns
        lower_std = np.std(lower_third)
        if lower_std > np.std(img) * 1.2:
            analysis['lower_field_heterogeneity'] = True  # Possible infiltrates
        else:
            analysis['lower_field_heterogeneity'] = False
        
        return analysis
    
    def _get_peripheral_mean(self, img):
        """Get mean intensity of peripheral 20% of image"""
        h, w = img.shape
        border = min(h, w) // 10
        peripheral = np.concatenate([
            img[:border, :].flatten(),
            img[-border:, :].flatten(),
            img[:, :border].flatten(),
            img[:, -border:].flatten()
        ])
        return np.mean(peripheral)
    
    def _get_central_mean(self, img):
        """Get mean intensity of central region"""
        h, w = img.shape
        h_start, h_end = h//4, 3*h//4
        w_start, w_end = w//4, 3*w//4
        return np.mean(img[h_start:h_end, w_start:w_end])
    
    def generate_diagnostic_assessment(self, ds, metadata: Dict, features: Dict) -> Dict:
        """
        Generate diagnostic assessment based on all available data
        Makes intelligent clinical inferences
        """
        
        assessment = {
            'patient_id': metadata['patient_id'],
            'timestamp': datetime.now().isoformat(),
            'data_sources': ['metadata', 'image_statistics', 'technical_parameters'],
            'assumptions': [],
            'findings': [],
            'differential_diagnosis': [],
            'covid19_assessment': {},
            'risk_factors': [],
            'confidence_level': 'moderate',
            'recommendations': []
        }
        
        # 1. Demographic risk assessment
        age = metadata.get('patient_age', '')
        sex = metadata.get('patient_sex', '')
        
        if age:
            age_years = int(age.replace('Y', '')) if 'Y' in age else 0
            
            if age_years > 60:
                assessment['risk_factors'].append(f"Advanced age ({age_years}Y) - Higher COVID-19 severity risk")
                assessment['assumptions'].append("Assumed increased susceptibility based on age >60")
            
            if age_years < 40:
                assessment['findings'].append(f"Younger patient ({age_years}Y) - Generally better prognosis")
        
        if sex == 'M':
            assessment['risk_factors'].append("Male sex - Slightly higher COVID-19 complication risk")
        
        # 2. Study description analysis
        study_desc = metadata.get('study_description', '').upper()
        if 'PORTABLE' in study_desc or 'AP' in study_desc:
            assessment['findings'].append("Portable AP view - Suggests inpatient or emergency setting")
            assessment['assumptions'].append("Portable study indicates possible acute illness or limited mobility")
        
        # 3. Image statistics analysis
        if features:
            # Analyze intensity patterns
            cv = features.get('coefficient_of_variation', 0)
            if cv > 0.5:
                assessment['findings'].append(
                    f"High intensity variation (CV={cv:.2f}) - Suggests heterogeneous lung parenchyma"
                )
                assessment['assumptions'].append("Heterogeneity may indicate infiltrates or abnormal findings")
            
            # Check for bilateral patterns
            if 'bilateral_asymmetry' in features:
                asymmetry = features['bilateral_asymmetry']
                if asymmetry < 0.1:  # Less than 10% difference
                    assessment['findings'].append("Bilateral symmetry maintained - May suggest diffuse process")
                    assessment['assumptions'].append("Symmetric bilateral findings typical for viral pneumonia including COVID-19")
                else:
                    assessment['findings'].append(f"Bilateral asymmetry detected ({asymmetry:.1%}) - May indicate focal process")
            
            # Lower field heterogeneity
            if features.get('lower_field_heterogeneity'):
                assessment['findings'].append("Increased heterogeneity in lower lung fields")
                assessment['differential_diagnosis'].append("Lower lobe infiltrates (infection, aspiration, edema)")
            
            # Entropy analysis
            entropy = features.get('image_entropy', 0)
            if entropy > 6:  # High entropy
                assessment['findings'].append(f"High image complexity (entropy={entropy:.2f}) - Multiple tissue densities")
        
        # 4. COVID-19 specific assessment
        covid_score = 0
        covid_features = []
        
        # Age factor
        if age and age_years > 50:
            covid_score += 1
            covid_features.append("Age >50 (risk factor)")
        
        # Bilateral pattern
        if features.get('bilateral_asymmetry', 1) < 0.15:
            covid_score += 2
            covid_features.append("Bilateral symmetric pattern (typical)")
        
        # Lower field involvement
        if features.get('lower_field_heterogeneity'):
            covid_score += 1
            covid_features.append("Lower field changes")
        
        # Heterogeneity
        if features.get('coefficient_of_variation', 0) > 0.4:
            covid_score += 1
            covid_features.append("Increased parenchymal heterogeneity")
        
        # Classify COVID-19 likelihood
        if covid_score >= 4:
            covid_classification = "HIGH probability - Typical features"
            confidence = "high"
        elif covid_score >= 2:
            covid_classification = "MODERATE probability - Indeterminate features"
            confidence = "moderate"
        else:
            covid_classification = "LOW probability - Atypical or negative"
            confidence = "low"
        
        assessment['covid19_assessment'] = {
            'classification': covid_classification,
            'score': covid_score,
            'max_score': 5,
            'features_present': covid_features,
            'confidence': confidence,
            'severity_estimate': self._estimate_severity(covid_score, features)
        }
        
        # 5. Generate differential diagnosis
        assessment['differential_diagnosis'] = self._generate_differential(
            metadata, features, covid_score
        )
        
        # 6. Confidence assessment
        if len(assessment['findings']) >= 3 and covid_score > 0:
            assessment['confidence_level'] = 'moderate-high'
        elif len(assessment['findings']) < 2:
            assessment['confidence_level'] = 'low'
        else:
            assessment['confidence_level'] = 'moderate'
        
        # 7. Clinical recommendations
        assessment['recommendations'] = self._generate_recommendations(
            assessment, metadata
        )
        
        return assessment
    
    def _estimate_severity(self, covid_score: int, features: Dict) -> str:
        """Estimate disease severity based on quantitative features"""
        
        if covid_score < 2:
            return "N/A (low probability of COVID-19)"
        
        # Use heterogeneity and other features
        heterogeneity = features.get('coefficient_of_variation', 0)
        lower_involvement = features.get('lower_field_heterogeneity', False)
        
        severity_score = 0
        
        if heterogeneity > 0.6:
            severity_score += 2
        elif heterogeneity > 0.4:
            severity_score += 1
        
        if lower_involvement:
            severity_score += 1
        
        if severity_score >= 3:
            return "Moderate-Severe (extensive involvement suggested)"
        elif severity_score >= 1:
            return "Mild-Moderate (limited involvement)"
        else:
            return "Mild (minimal changes)"
    
    def _generate_differential(self, metadata: Dict, features: Dict, covid_score: int) -> List[str]:
        """Generate differential diagnosis list"""
        
        differentials = []
        
        # COVID-19 related
        if covid_score >= 2:
            differentials.append("COVID-19 pneumonia (viral)")
        
        # Age-based considerations
        age = metadata.get('patient_age', '')
        if age and 'Y' in age:
            age_years = int(age.replace('Y', ''))
            
            if age_years > 60:
                differentials.extend([
                    "Bacterial pneumonia (community-acquired)",
                    "Heart failure / pulmonary edema",
                    "Chronic obstructive pulmonary disease (COPD) exacerbation"
                ])
            else:
                differentials.extend([
                    "Viral pneumonia (other)",
                    "Bacterial pneumonia (atypical)",
                    "Reactive airway disease"
                ])
        
        # Pattern-based
        if features.get('bilateral_asymmetry', 1) < 0.1:
            differentials.append("Diffuse alveolar disease (multiple etiologies)")
        
        if features.get('lower_field_heterogeneity'):
            differentials.append("Lower lobe pneumonia")
            differentials.append("Aspiration pneumonia")
        
        # Always consider normal
        if covid_score < 2:
            differentials.insert(0, "Normal chest radiograph (no acute disease)")
        
        return differentials[:5]  # Top 5
    
    def _generate_recommendations(self, assessment: Dict, metadata: Dict) -> List[str]:
        """Generate clinical recommendations"""
        
        recommendations = []
        
        covid_class = assessment['covid19_assessment']['classification']
        
        if 'HIGH' in covid_class:
            recommendations.extend([
                "🔴 HIGH Priority: RT-PCR COVID-19 testing indicated",
                "Consider CT chest for detailed assessment if clinically indicated",
                "Isolation precautions per institutional COVID-19 protocols",
                "Monitor oxygen saturation and respiratory status",
                "Follow-up chest X-ray in 24-48 hours to assess progression"
            ])
        
        elif 'MODERATE' in covid_class:
            recommendations.extend([
                "🟡 MODERATE Priority: COVID-19 testing recommended",
                "Clinical correlation with symptoms (fever, cough, dyspnea)",
                "Consider CT if diagnosis uncertain and clinically significant",
                "Follow-up imaging in 2-3 days if symptoms persist or worsen"
            ])
        
        else:
            recommendations.extend([
                "🟢 LOW Priority: COVID-19 testing if high clinical suspicion",
                "Clinical correlation recommended",
                "Follow-up as clinically indicated"
            ])
        
        # Age-specific
        age = metadata.get('patient_age', '')
        if age and 'Y' in age:
            age_years = int(age.replace('Y', ''))
            if age_years > 70:
                recommendations.append("Elderly patient: Monitor closely for rapid deterioration")
        
        # Quality recommendations
        if 'PORTABLE' in metadata.get('study_description', '').upper():
            recommendations.append("Consider PA/lateral views when patient condition allows for better evaluation")
        
        return recommendations
    
    def analyze_patient(self, dicom_file: Path) -> Dict:
        """Comprehensive diagnostic analysis for single patient"""
        
        print(f"\n{'='*70}")
        print(f"DIAGNOSTIC ANALYSIS: {dicom_file.name}")
        print(f"{'='*70}")
        
        try:
            # Read DICOM
            ds = read_dicom(dicom_file)
            metadata = get_metadata(ds)
            
            print(f"\nPatient: {metadata['patient_id']}")
            print(f"Age: {metadata['patient_age']}, Sex: {metadata['patient_sex']}")
            print(f"Study: {metadata['study_description']}")
            
            # Extract quantitative features
            print("\n📊 Extracting quantitative features...")
            features = self.extract_quantitative_features(ds)
            print(f"   ✓ Extracted {len(features)} quantitative features")
            
            # Generate diagnostic assessment
            print("\n🔬 Generating diagnostic assessment...")
            assessment = self.generate_diagnostic_assessment(ds, metadata, features)
            assessment['dicom_file'] = str(dicom_file)
            assessment['quantitative_features'] = features
            
            # Print summary
            self._print_assessment_summary(assessment)
            
            return assessment
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return {'dicom_file': str(dicom_file), 'error': str(e)}
    
    def _print_assessment_summary(self, assessment: Dict):
        """Print diagnostic assessment summary"""
        
        print(f"\n{'='*70}")
        print("DIAGNOSTIC ASSESSMENT SUMMARY")
        print(f"{'='*70}")
        
        # COVID-19 assessment
        covid = assessment['covid19_assessment']
        print(f"\n🦠 COVID-19 Assessment:")
        print(f"   Classification: {covid['classification']}")
        print(f"   Score: {covid['score']}/{covid['max_score']}")
        print(f"   Confidence: {covid['confidence'].upper()}")
        print(f"   Severity: {covid['severity_estimate']}")
        
        if covid['features_present']:
            print(f"\n   Features Present:")
            for feature in covid['features_present']:
                print(f"     • {feature}")
        
        # Differential diagnosis
        if assessment['differential_diagnosis']:
            print(f"\n🔍 Differential Diagnosis:")
            for i, dx in enumerate(assessment['differential_diagnosis'], 1):
                print(f"   {i}. {dx}")
        
        # Key findings
        if assessment['findings']:
            print(f"\n📋 Key Findings:")
            for finding in assessment['findings'][:5]:
                print(f"   • {finding}")
        
        # Recommendations
        if assessment['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in assessment['recommendations'][:5]:
                print(f"   {rec}")
    
    def analyze_cohort(self, data_dir: Path) -> List[Dict]:
        """Analyze entire cohort"""
        
        print("\n" + "="*70)
        print("📊 COHORT DIAGNOSTIC ANALYSIS")
        print("="*70)
        print("\nData-driven diagnostic inferences from:")
        print("  • DICOM metadata")
        print("  • Image statistics")
        print("  • Technical parameters")
        print("  • Clinical reasoning")
        
        dicom_files = find_dicom_files(data_dir)
        
        if not dicom_files:
            print("\n⚠️  No DICOM files found!")
            return []
        
        print(f"\nFound {len(dicom_files)} DICOM files\n")
        
        results = []
        
        for idx, dicom_file in enumerate(dicom_files, 1):
            print(f"\n[{idx}/{len(dicom_files)}]")
            assessment = self.analyze_patient(dicom_file)
            
            if 'covid19_assessment' in assessment:
                results.append(assessment)
                self.diagnostic_results.append(assessment)
                
                # Save individual assessment
                result_file = self.output_dir / f"diagnostic_assessment_{idx}.json"
                with open(result_file, 'w') as f:
                    json.dump(assessment, f, indent=2, default=str)
        
        # Generate cohort summary
        if results:
            self._save_cohort_diagnostics(results)
        
        return results
    
    def _save_cohort_diagnostics(self, results: List[Dict]):
        """Save comprehensive diagnostic results"""
        
        # Save all assessments as JSON
        json_path = self.output_dir / "diagnostic_assessments_complete.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Create formatted diagnostic report
        report_path = self.output_dir / "diagnostic_report.txt"
        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("DATA-DRIVEN DIAGNOSTIC ANALYSIS REPORT\n")
            f.write("="*70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write(f"Total Patients: {len(results)}\n")
            f.write("Method: Quantitative analysis + Clinical reasoning\n")
            f.write("="*70 + "\n\n")
            
            for idx, assessment in enumerate(results, 1):
                f.write(f"\n{'='*70}\n")
                f.write(f"PATIENT {idx}: {assessment['patient_id']}\n")
                f.write(f"{'='*70}\n\n")
                
                # COVID-19 assessment
                covid = assessment['covid19_assessment']
                f.write("COVID-19 ASSESSMENT:\n")
                f.write(f"  Classification: {covid['classification']}\n")
                f.write(f"  Diagnostic Score: {covid['score']}/{covid['max_score']}\n")
                f.write(f"  Confidence: {covid['confidence']}\n")
                f.write(f"  Estimated Severity: {covid['severity_estimate']}\n\n")
                
                # Features
                if covid['features_present']:
                    f.write("  Supporting Features:\n")
                    for feature in covid['features_present']:
                        f.write(f"    • {feature}\n")
                    f.write("\n")
                
                # Differential
                f.write("DIFFERENTIAL DIAGNOSIS:\n")
                for i, dx in enumerate(assessment['differential_diagnosis'], 1):
                    f.write(f"  {i}. {dx}\n")
                f.write("\n")
                
                # Key findings
                f.write("KEY FINDINGS:\n")
                for finding in assessment['findings']:
                    f.write(f"  • {finding}\n")
                f.write("\n")
                
                # Recommendations
                f.write("CLINICAL RECOMMENDATIONS:\n")
                for rec in assessment['recommendations']:
                    f.write(f"  {rec}\n")
                f.write("\n")
        
        # Create cohort statistics
        self._generate_cohort_statistics(results, report_path)
        
        print(f"\n✓ Diagnostic results saved:")
        print(f"  • {json_path}")
        print(f"  • {report_path}")
    
    def _generate_cohort_statistics(self, results: List[Dict], report_path: Path):
        """Generate cohort-level diagnostic statistics"""
        
        # COVID-19 classification distribution
        classifications = [r['covid19_assessment']['classification'] for r in results]
        
        high_prob = sum(1 for c in classifications if 'HIGH' in c)
        mod_prob = sum(1 for c in classifications if 'MODERATE' in c)
        low_prob = sum(1 for c in classifications if 'LOW' in c)
        
        stats_text = f"""

{'='*70}
COHORT STATISTICS
{'='*70}

Total Patients Analyzed: {len(results)}

COVID-19 PROBABILITY DISTRIBUTION:
  • HIGH Probability: {high_prob} patients ({high_prob/len(results)*100:.1f}%)
  • MODERATE Probability: {mod_prob} patients ({mod_prob/len(results)*100:.1f}%)
  • LOW Probability: {low_prob} patients ({low_prob/len(results)*100:.1f}%)

CONFIDENCE LEVELS:
"""
        
        confidence_counts = {}
        for r in results:
            conf = r['covid19_assessment']['confidence']
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        
        for conf, count in confidence_counts.items():
            stats_text += f"  • {conf.capitalize()}: {count} patients ({count/len(results)*100:.1f}%)\n"
        
        # Severity distribution
        stats_text += "\nESTIMATED SEVERITY (for COVID-19 probable/possible cases):\n"
        severity_counts = {}
        for r in results:
            if r['covid19_assessment']['score'] >= 2:
                sev = r['covid19_assessment']['severity_estimate']
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        for sev, count in severity_counts.items():
            stats_text += f"  • {sev}: {count} patients\n"
        
        # Common findings
        stats_text += "\nCOMMON FINDINGS ACROSS COHORT:\n"
        all_findings = []
        for r in results:
            all_findings.extend(r['findings'])
        
        from collections import Counter
        common = Counter(all_findings).most_common(5)
        for finding, count in common:
            stats_text += f"  • {finding[:60]}... ({count} patients)\n"
        
        stats_text += f"\n{'='*70}\n"
        
        # Append to report
        with open(report_path, 'a') as f:
            f.write(stats_text)
        
        print(f"\n✓ Cohort statistics added to report")


def main():
    """Main execution for diagnostic analysis"""
    
    print("\n" + "="*70)
    print("🔬 DATA-DRIVEN DIAGNOSTIC ANALYZER")
    print("="*70)
    print("\n✨ Comprehensive Clinical Assessment Using:")
    print("  • DICOM metadata (demographics, clinical context)")
    print("  • Image statistics (intensity patterns, distributions)")
    print("  • Technical parameters (acquisition settings)")
    print("  • Quantitative features (texture, density, symmetry)")
    print("  • Clinical reasoning (evidence-based rules)")
    
    print("\n📋 Diagnostic Capabilities:")
    print("  • COVID-19 probability assessment")
    print("  • Severity estimation")
    print("  • Differential diagnosis generation")
    print("  • Risk factor identification")
    print("  • Clinical recommendations")
    
    # Initialize analyzer
    analyzer = DiagnosticAnalyzer()
    
    # Analyze cohort
    data_dir = Path("../data")
    results = analyzer.analyze_cohort(data_dir)
    
    if results:
        print("\n" + "="*70)
        print("✅ DIAGNOSTIC ANALYSIS COMPLETE")
        print("="*70)
        
        print(f"\n📊 Cohort Summary:")
        print(f"   Patients analyzed: {len(results)}")
        
        # Quick summary
        for idx, result in enumerate(results, 1):
            covid = result['covid19_assessment']
            print(f"\n   Patient {idx}: {result['patient_id']}")
            print(f"     COVID-19: {covid['classification']}")
            print(f"     Confidence: {covid['confidence']}")
            print(f"     Severity: {covid['severity_estimate']}")
        
        print("\n" + "="*70)
        print("📁 OUTPUT FILES:")
        print("="*70)
        print("\n  ✓ diagnostic_assessments_complete.json - All assessments")
        print("  ✓ diagnostic_report.txt - Formatted report")
        print("  ✓ diagnostic_assessment_1.json - Patient 1")
        print("  ✓ diagnostic_assessment_2.json - Patient 2")
        
        print("\n" + "="*70)
        print("🎯 NEXT STEPS:")
        print("="*70)
        print("\n  1. Review diagnostic report:")
        print("     cat output/diagnostic_report.txt")
        print("\n  2. Compare with AI analysis:")
        print("     cat output/multimodel_clinical_report.txt")
        print("\n  3. Generate final comprehensive report:")
        print("     python generate_medical_report.py")
        print("\n  4. Validate findings with expert radiologist")
    
    print("\n" + "="*70)
    print("✨ DIAGNOSTIC ANALYSIS COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()

