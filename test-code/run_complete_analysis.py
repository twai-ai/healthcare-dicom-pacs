"""
Complete Analysis Pipeline - Run All Analyses
Executes the entire diagnostic workflow
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a script and report status"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {description} complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run complete analysis pipeline"""
    
    print("\n" + "="*70)
    print("🚀 COMPLETE DICOM-AI ANALYSIS PIPELINE")
    print("="*70)
    print("\nThis will run all analyses in sequence:")
    print("  1. Protocol Analysis")
    print("  2. DICOM Validation")
    print("  3. Bias Detection")
    print("  4. Diagnostic Assessment")
    print("  5. Multi-Model AI Analysis")
    print("  6. Comprehensive Report Generation")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)
    
    results = {}
    
    # Run analyses in sequence
    scripts = [
        ("08_protocol_analyzer.py", "Protocol Analysis"),
        ("09_dicom_validator.py", "DICOM Validation"),
        ("11_bias_analyzer.py", "Bias Analysis"),
        ("15_diagnostic_analyzer.py", "Diagnostic Assessment"),
        ("14_multi_model_ai_analysis.py", "Multi-Model AI Analysis"),
        ("generate_medical_report.py", "Medical Report Generation"),
    ]
    
    for script, description in scripts:
        success = run_script(script, description)
        results[description] = success
    
    # Summary
    print("\n" + "="*70)
    print("📊 ANALYSIS PIPELINE SUMMARY")
    print("="*70)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for analysis, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {analysis}")
    
    print(f"\nSuccess Rate: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
    
    if success_count == total_count:
        print("\n" + "="*70)
        print("✅ ALL ANALYSES COMPLETE!")
        print("="*70)
        print("\n📄 Comprehensive report generated:")
        print("   output/Medical_Analysis_Report.pdf")
        print("\n🎯 Next: Open report and share with reviewers")
    else:
        print("\n⚠️  Some analyses failed. Check output above.")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

