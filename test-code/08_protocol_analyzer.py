"""
Protocol Analyzer - Extract and standardize imaging protocols
Addresses: Scanner/vendor/protocol variability (Protocol Genome challenge)
Reference: arXiv - Hidden confounders in medical imaging
"""

import sys
from pathlib import Path
import pandas as pd
from collections import defaultdict
from typing import Dict, List
import json

sys.path.append(str(Path(__file__).parent))
from utils import find_dicom_files, read_dicom

class ProtocolAnalyzer:
    """
    Analyze and standardize imaging protocols across datasets
    Detects hidden confounders (scanner, sequence, vendor)
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.protocol_database = defaultdict(list)
    
    def analyze_protocols(self, directory: Path) -> pd.DataFrame:
        """Extract all protocol variations from a dataset"""
        
        print("\n" + "="*60)
        print("PROTOCOL ANALYSIS")
        print("="*60)
        print(f"\nAnalyzing directory: {directory}")
        
        dicom_files = find_dicom_files(directory)
        
        if not dicom_files:
            print("No DICOM files found!")
            return pd.DataFrame()
        
        print(f"Found {len(dicom_files)} DICOM files")
        print("Extracting protocol information...\n")
        
        for file in dicom_files:
            try:
                ds = read_dicom(file)
                
                protocol_signature = {
                    'modality': ds.get('Modality', 'Unknown'),
                    'manufacturer': ds.get('Manufacturer', 'Unknown'),
                    'model': ds.get('ManufacturerModelName', 'Unknown'),
                    'software_version': ds.get('SoftwareVersions', 'Unknown'),
                    'protocol_name': ds.get('ProtocolName', 'Unknown'),
                    'series_description': ds.get('SeriesDescription', 'Unknown'),
                    'body_part': ds.get('BodyPartExamined', 'Unknown'),
                    'patient_position': ds.get('PatientPosition', 'Unknown'),
                    
                    # CT-specific parameters
                    'slice_thickness': ds.get('SliceThickness') if ds.Modality == 'CT' else None,
                    'kvp': ds.get('KVP') if ds.Modality == 'CT' else None,
                    'kernel': ds.get('ConvolutionKernel') if ds.Modality == 'CT' else None,
                    'exposure': ds.get('Exposure') if ds.Modality == 'CT' else None,
                    
                    # MR-specific parameters
                    'sequence': ds.get('SequenceName') if ds.Modality == 'MR' else None,
                    'te': ds.get('EchoTime') if ds.Modality == 'MR' else None,
                    'tr': ds.get('RepetitionTime') if ds.Modality == 'MR' else None,
                    'field_strength': ds.get('MagneticFieldStrength') if ds.Modality == 'MR' else None,
                    
                    # Geometric parameters
                    'pixel_spacing': str(ds.get('PixelSpacing', 'Unknown')),
                    'image_size': f"{ds.Rows}x{ds.Columns}" if hasattr(ds, 'Rows') else 'Unknown',
                    
                    # File info
                    'file_name': file.name,
                }
                
                self.protocol_database[ds.Modality].append(protocol_signature)
                
            except Exception as e:
                print(f"Error processing {file}: {e}")
                continue
        
        # Create comprehensive protocol report
        all_protocols = []
        for modality, protocols in self.protocol_database.items():
            df = pd.DataFrame(protocols)
            all_protocols.append(df)
        
        if all_protocols:
            combined_df = pd.concat(all_protocols, ignore_index=True)
            
            # Save protocol database
            csv_path = self.output_dir / "protocol_database.csv"
            combined_df.to_csv(csv_path, index=False)
            print(f"✓ Protocol database saved to: {csv_path}")
            
            # Generate summary
            self._print_protocol_summary(combined_df)
            
            return combined_df
        
        return pd.DataFrame()
    
    def _print_protocol_summary(self, df: pd.DataFrame):
        """Print comprehensive protocol summary"""
        
        print("\n" + "="*60)
        print("PROTOCOL SUMMARY")
        print("="*60)
        
        print(f"\nTotal series analyzed: {len(df)}")
        
        print(f"\n📊 Modality Distribution:")
        for modality, count in df['modality'].value_counts().items():
            print(f"  • {modality}: {count} series")
        
        print(f"\n🏭 Manufacturer Distribution:")
        for manufacturer, count in df['manufacturer'].value_counts().items():
            print(f"  • {manufacturer}: {count} series")
        
        print(f"\n🔧 Model Diversity:")
        print(f"  Unique models: {df['model'].nunique()}")
        top_models = df['model'].value_counts().head(3)
        for model, count in top_models.items():
            print(f"  • {model}: {count} series")
        
        print(f"\n📋 Protocol Diversity:")
        print(f"  Unique protocols: {df['protocol_name'].nunique()}")
        
        # CT-specific summary
        ct_data = df[df['modality'] == 'CT']
        if not ct_data.empty:
            print(f"\n🔬 CT Protocol Variations:")
            if 'slice_thickness' in ct_data.columns:
                st_values = ct_data['slice_thickness'].dropna()
                if not st_values.empty:
                    print(f"  Slice thickness range: {st_values.min():.1f} - {st_values.max():.1f} mm")
            if 'kvp' in ct_data.columns:
                kvp_values = ct_data['kvp'].dropna()
                if not kvp_values.empty:
                    print(f"  kVp range: {kvp_values.min():.0f} - {kvp_values.max():.0f}")
        
        # MR-specific summary
        mr_data = df[df['modality'] == 'MR']
        if not mr_data.empty:
            print(f"\n🧲 MR Protocol Variations:")
            if 'field_strength' in mr_data.columns:
                fs_values = mr_data['field_strength'].dropna()
                if not fs_values.empty:
                    print(f"  Field strengths: {fs_values.unique()}")
    
    def detect_protocol_drift(self, protocols_df: pd.DataFrame) -> Dict:
        """
        Detect variations that could affect AI model performance
        Reference: Hidden confounders in medical imaging
        """
        
        print("\n" + "="*60)
        print("PROTOCOL DRIFT DETECTION")
        print("="*60)
        
        drift_report = {
            'unique_manufacturers': protocols_df['manufacturer'].nunique(),
            'unique_models': protocols_df['model'].nunique(),
            'unique_protocols': protocols_df['protocol_name'].nunique(),
            'warnings': [],
            'risk_level': 'low'
        }
        
        # Check manufacturer concentration
        manufacturer_dist = protocols_df['manufacturer'].value_counts()
        max_concentration = manufacturer_dist.max() / len(protocols_df)
        
        if max_concentration > 0.8:
            drift_report['warnings'].append(
                f"⚠️  HIGH RISK: Single manufacturer dominates ({max_concentration*100:.1f}%). "
                "Model may not generalize to other scanners."
            )
            drift_report['risk_level'] = 'high'
        elif max_concentration > 0.6:
            drift_report['warnings'].append(
                f"⚠️  MEDIUM RISK: Manufacturer imbalance ({max_concentration*100:.1f}%). "
                "Consider augmenting with data from other vendors."
            )
            drift_report['risk_level'] = 'medium'
        
        # Check protocol diversity
        if drift_report['unique_protocols'] < 3:
            drift_report['warnings'].append(
                "⚠️  LOW PROTOCOL DIVERSITY: Limited protocol variations may affect generalizability."
            )
        
        # CT-specific drift
        ct_data = protocols_df[protocols_df['modality'] == 'CT']
        if not ct_data.empty:
            if 'slice_thickness' in ct_data.columns:
                st_values = ct_data['slice_thickness'].dropna()
                if not st_values.empty:
                    st_range = st_values.max() - st_values.min()
                    if st_range > 5:
                        drift_report['warnings'].append(
                            f"⚠️  LARGE SLICE THICKNESS VARIATION: {st_range:.1f}mm range. "
                            "Consider resampling to common spacing."
                        )
        
        # Print warnings
        print(f"\n🎯 Risk Level: {drift_report['risk_level'].upper()}")
        print(f"\n📊 Diversity Metrics:")
        print(f"  • Unique manufacturers: {drift_report['unique_manufacturers']}")
        print(f"  • Unique models: {drift_report['unique_models']}")
        print(f"  • Unique protocols: {drift_report['unique_protocols']}")
        
        if drift_report['warnings']:
            print(f"\n⚠️  Detected Issues:")
            for warning in drift_report['warnings']:
                print(f"  {warning}")
        else:
            print(f"\n✓ No significant protocol drift detected")
        
        # Save drift report
        report_path = self.output_dir / "protocol_drift_report.json"
        with open(report_path, 'w') as f:
            json.dump(drift_report, f, indent=2)
        print(f"\n✓ Drift report saved to: {report_path}")
        
        return drift_report
    
    def generate_recommendations(self, drift_report: Dict) -> List[str]:
        """Generate recommendations for improving protocol standardization"""
        
        recommendations = []
        
        if drift_report['risk_level'] == 'high':
            recommendations.append(
                "1. URGENT: Acquire data from multiple scanner manufacturers"
            )
            recommendations.append(
                "2. Implement scanner-specific normalization or harmonization"
            )
            recommendations.append(
                "3. Use domain adaptation techniques during model training"
            )
        
        if drift_report['unique_protocols'] < 5:
            recommendations.append(
                "4. Increase protocol diversity in training dataset"
            )
        
        recommendations.append(
            "5. Implement stratified sampling by manufacturer during train/test split"
        )
        
        recommendations.append(
            "6. Track protocol metadata in all experiments for reproducibility"
        )
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        for rec in recommendations:
            print(f"\n{rec}")
        
        return recommendations


def main():
    """Run protocol analysis"""
    
    print("\n" + "="*60)
    print("PROTOCOL ANALYZER")
    print("="*60)
    print("\nAddresses: Scanner/vendor/protocol variability")
    print("Reference: Protocol Genome - Hidden confounders")
    
    # Analyze data directory
    data_dir = Path("../data")
    
    analyzer = ProtocolAnalyzer()
    
    # Extract protocols
    protocols_df = analyzer.analyze_protocols(data_dir)
    
    if not protocols_df.empty:
        # Detect drift
        drift_report = analyzer.detect_protocol_drift(protocols_df)
        
        # Generate recommendations
        recommendations = analyzer.generate_recommendations(drift_report)
    else:
        print("\n⚠️  No protocols extracted. Check data directory.")
    
    print("\n" + "="*60)
    print("✓ PROTOCOL ANALYSIS COMPLETE")
    print("="*60)
    print("\nResults saved to output/ directory")


if __name__ == "__main__":
    main()
