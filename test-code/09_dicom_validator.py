"""
DICOM Validation and Standardization Layer
Ensures interoperability across different DICOM implementations
Addresses: Interoperability and standardization gaps
"""

import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
import json

sys.path.append(str(Path(__file__).parent))
from utils import find_dicom_files, read_dicom

class DICOMValidator:
    """
    Validate and standardize DICOM files for interoperability
    Reference: DICOM Standard PS3.3
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.validation_rules = self._define_validation_rules()
        self.validation_results = []
    
    def _define_validation_rules(self):
        """Define validation rules based on DICOM standard"""
        return {
            'required_tags': [
                'PatientID', 'StudyInstanceUID', 'SeriesInstanceUID',
                'SOPInstanceUID', 'Modality'
            ],
            'modality_specific': {
                'CT': ['SliceThickness', 'KVP', 'PixelSpacing'],
                'MR': ['EchoTime', 'RepetitionTime', 'MagneticFieldStrength'],
                'CR': ['PixelSpacing'],
                'DX': ['PixelSpacing']
            },
            'recommended_tags': [
                'StudyDate', 'StudyDescription', 'SeriesDescription',
                'Manufacturer', 'ManufacturerModelName'
            ],
            'phi_tags': [
                'PatientBirthDate', 'PatientName', 'InstitutionName',
                'ReferringPhysicianName', 'OperatorsName'
            ]
        }
    
    def validate_dicom(self, file_path: Path) -> Dict:
        """Comprehensive DICOM validation"""
        
        validation_result = {
            'file': str(file_path),
            'file_name': file_path.name,
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': [],
            'conformance_level': 'full',
            'deidentified': True
        }
        
        try:
            ds = read_dicom(file_path)
            
            # 1. Check required tags
            for tag in self.validation_rules['required_tags']:
                if not hasattr(ds, tag):
                    validation_result['errors'].append(f"Missing required tag: {tag}")
                    validation_result['valid'] = False
                    validation_result['conformance_level'] = 'invalid'
            
            # 2. Check modality-specific requirements
            modality = ds.get('Modality', 'Unknown')
            validation_result['modality'] = modality
            
            if modality in self.validation_rules['modality_specific']:
                for tag in self.validation_rules['modality_specific'][modality]:
                    if not hasattr(ds, tag) or ds.get(tag) is None:
                        validation_result['warnings'].append(
                            f"Missing recommended tag for {modality}: {tag}"
                        )
                        if validation_result['conformance_level'] == 'full':
                            validation_result['conformance_level'] = 'partial'
            
            # 3. Validate pixel data integrity
            if hasattr(ds, 'pixel_array'):
                try:
                    img = ds.pixel_array
                    validation_result['info'].append(
                        f"Pixel data OK: shape={img.shape}, dtype={img.dtype}"
                    )
                except Exception as e:
                    validation_result['errors'].append(f"Pixel data error: {e}")
                    validation_result['valid'] = False
            else:
                validation_result['warnings'].append("No pixel data found")
            
            # 4. Check for PHI (should be de-identified)
            for tag in self.validation_rules['phi_tags']:
                if hasattr(ds, tag) and ds.get(tag):
                    value = str(ds.get(tag))
                    if value and value not in ['', 'ANONYMOUS', 'Unknown']:
                        validation_result['warnings'].append(
                            f"Contains potential PHI tag: {tag} = {value[:20]}..."
                        )
                        validation_result['deidentified'] = False
            
            # 5. Check de-identification status
            if hasattr(ds, 'PatientIdentityRemoved'):
                if ds.PatientIdentityRemoved == 'YES':
                    validation_result['info'].append("✓ Marked as de-identified")
                else:
                    validation_result['warnings'].append("Not marked as de-identified")
            
            # 6. Validate important geometric parameters
            if modality in ['CT', 'MR']:
                if not hasattr(ds, 'ImageOrientationPatient'):
                    validation_result['warnings'].append("Missing ImageOrientationPatient")
                if not hasattr(ds, 'ImagePositionPatient'):
                    validation_result['warnings'].append("Missing ImagePositionPatient")
            
            # 7. Check for recommended metadata
            missing_recommended = []
            for tag in self.validation_rules['recommended_tags']:
                if not hasattr(ds, tag) or not ds.get(tag):
                    missing_recommended.append(tag)
            
            if missing_recommended:
                validation_result['info'].append(
                    f"Missing recommended tags: {', '.join(missing_recommended)}"
                )
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['conformance_level'] = 'invalid'
            validation_result['errors'].append(f"File read error: {e}")
        
        return validation_result
    
    def validate_directory(self, directory: Path) -> pd.DataFrame:
        """Validate all DICOM files in a directory"""
        
        print("\n" + "="*60)
        print("DICOM VALIDATION")
        print("="*60)
        print(f"\nValidating directory: {directory}")
        
        dicom_files = find_dicom_files(directory)
        
        if not dicom_files:
            print("No DICOM files found!")
            return pd.DataFrame()
        
        print(f"Found {len(dicom_files)} DICOM files")
        print("Validating...\n")
        
        self.validation_results = []
        
        for file in dicom_files:
            result = self.validate_dicom(file)
            self.validation_results.append(result)
        
        # Create DataFrame
        df = pd.DataFrame(self.validation_results)
        
        # Save results
        csv_path = self.output_dir / "validation_results.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Validation results saved to: {csv_path}")
        
        # Print summary
        self._print_validation_summary(df)
        
        return df
    
    def _print_validation_summary(self, df: pd.DataFrame):
        """Print validation summary"""
        
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        total = len(df)
        valid = df['valid'].sum()
        invalid = total - valid
        
        print(f"\nTotal files: {total}")
        print(f"✓ Valid: {valid} ({valid/total*100:.1f}%)")
        if invalid > 0:
            print(f"✗ Invalid: {invalid} ({invalid/total*100:.1f}%)")
        
        print(f"\n📊 Conformance Levels:")
        for level, count in df['conformance_level'].value_counts().items():
            print(f"  • {level}: {count} files ({count/total*100:.1f}%)")
        
        print(f"\n🔒 De-identification Status:")
        deidentified = df['deidentified'].sum()
        print(f"  • De-identified: {deidentified} files ({deidentified/total*100:.1f}%)")
        if deidentified < total:
            print(f"  • ⚠️  Contains PHI: {total - deidentified} files")
        
        # Error summary
        all_errors = []
        for idx, row in df.iterrows():
            if row['errors']:
                all_errors.extend(row['errors'])
        
        if all_errors:
            print(f"\n⚠️  Common Errors:")
            from collections import Counter
            error_counts = Counter(all_errors)
            for error, count in error_counts.most_common(5):
                print(f"  • {error}: {count} occurrences")
        
        # Warning summary
        all_warnings = []
        for idx, row in df.iterrows():
            if row['warnings']:
                all_warnings.extend(row['warnings'])
        
        if all_warnings:
            print(f"\n⚠️  Common Warnings:")
            from collections import Counter
            warning_counts = Counter(all_warnings)
            for warning, count in warning_counts.most_common(5):
                print(f"  • {warning}: {count} occurrences")
    
    def generate_compliance_report(self) -> Dict:
        """Generate detailed compliance report"""
        
        if not self.validation_results:
            return {}
        
        df = pd.DataFrame(self.validation_results)
        
        report = {
            'total_files': len(df),
            'valid_files': int(df['valid'].sum()),
            'invalid_files': int((~df['valid']).sum()),
            'deidentified_files': int(df['deidentified'].sum()),
            'conformance': {
                'full': int((df['conformance_level'] == 'full').sum()),
                'partial': int((df['conformance_level'] == 'partial').sum()),
                'invalid': int((df['conformance_level'] == 'invalid').sum())
            },
            'modality_breakdown': df['modality'].value_counts().to_dict(),
            'recommendations': []
        }
        
        # Generate recommendations
        if report['invalid_files'] > 0:
            report['recommendations'].append(
                "⚠️  Fix invalid DICOM files before processing"
            )
        
        if report['deidentified_files'] < report['total_files']:
            report['recommendations'].append(
                "⚠️  De-identify files containing PHI before sharing"
            )
        
        if report['conformance']['partial'] > report['conformance']['full']:
            report['recommendations'].append(
                "⚠️  Many files missing recommended metadata. "
                "This may affect analysis quality."
            )
        
        # Save report
        report_path = self.output_dir / "compliance_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*60)
        print("COMPLIANCE REPORT")
        print("="*60)
        print(json.dumps(report, indent=2))
        print(f"\n✓ Report saved to: {report_path}")
        
        return report


def main():
    """Run DICOM validation"""
    
    print("\n" + "="*60)
    print("DICOM VALIDATOR")
    print("="*60)
    print("\nAddresses: Interoperability and standardization gaps")
    print("Ensures: DICOM compliance and data quality")
    
    # Validate data directory
    data_dir = Path("../data")
    
    validator = DICOMValidator()
    
    # Run validation
    results_df = validator.validate_directory(data_dir)
    
    if not results_df.empty:
        # Generate compliance report
        compliance = validator.generate_compliance_report()
    else:
        print("\n⚠️  No files validated. Check data directory.")
    
    print("\n" + "="*60)
    print("✓ VALIDATION COMPLETE")
    print("="*60)
    print("\nResults saved to output/ directory")


if __name__ == "__main__":
    main()
