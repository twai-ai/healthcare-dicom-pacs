"""
Download Expanded Dataset from TCIA
Downloads additional COVID-19 and multi-modality data for comprehensive analysis
"""

import sys
from pathlib import Path
from tcia_utils import nbia
import pandas as pd

def download_covid_dataset(num_patients=10, collection="COVID-19-AR"):
    """
    Download COVID-19 dataset
    
    Args:
        num_patients: Number of patients to download (default: 10)
        collection: TCIA collection name
    """
    
    print("\n" + "="*70)
    print(f"📥 DOWNLOADING COVID-19 DATASET: {collection}")
    print("="*70)
    print(f"\nTarget: {num_patients} patients")
    
    # Get patients
    print("\nFetching patient list...")
    patients = nbia.getPatient(collection=collection, format="df")
    
    if patients is None or patients.empty:
        print("✗ No patients found!")
        return
    
    print(f"✓ Found {len(patients)} total patients in collection")
    
    # Debug: print column names
    print(f"Available columns: {list(patients.columns)}")
    
    # Limit to requested number
    sample_patients = patients.head(num_patients)
    
    output_dir = Path("../data/raw") / collection
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_count = 0
    total_images = 0
    
    for idx, patient_row in sample_patients.iterrows():
        # Handle different column name formats (TCIA uses 'PatientId')
        patient_id = patient_row.get('PatientId') or patient_row.get('PatientID') or patient_row.get('Patient ID')
        
        print(f"\n[{idx+1}/{num_patients}] Patient: {patient_id}")
        
        # Get series for this patient
        series = nbia.getSeries(
            collection=collection,
            patientId=patient_id,
            format="df"
        )
        
        if series is None or series.empty:
            print(f"  ✗ No series found")
            continue
        
        print(f"  ✓ Found {len(series)} series")
        
        # Download first series (or CT series if available)
        ct_series = series[series['Modality'] == 'CT']
        if not ct_series.empty:
            target_series = ct_series.iloc[0]
            print(f"  📊 Downloading CT series...")
        else:
            target_series = series.iloc[0]
            print(f"  📊 Downloading {target_series['Modality']} series...")
        
        series_uid = target_series['SeriesInstanceUID']
        modality = target_series['Modality']
        image_count = target_series.get('ImageCount', 0)
        
        # Create patient directory
        patient_dir = output_dir / patient_id
        patient_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download series (using correct TCIA API parameters)
            nbia.downloadSeries(
                [series_uid],  # Pass list of UIDs as first positional argument
                path=str(patient_dir),
                input_type="list"  # Specify input type
            )
            
            print(f"  ✓ Downloaded {modality} series ({image_count} images)")
            print(f"  📁 Saved to: {patient_dir}")
            
            downloaded_count += 1
            total_images += image_count
            
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
    
    print("\n" + "="*70)
    print("📊 DOWNLOAD SUMMARY")
    print("="*70)
    print(f"\n✓ Successfully downloaded: {downloaded_count}/{num_patients} patients")
    print(f"✓ Total images: {total_images}")
    print(f"✓ Location: {output_dir}")
    
    return downloaded_count

def download_multimodality_sample():
    """Download sample data from multiple modalities"""
    
    print("\n" + "="*70)
    print("📥 DOWNLOADING MULTI-MODALITY SAMPLE")
    print("="*70)
    
    samples = [
        {"collection": "LIDC-IDRI", "modality": "CT", "patients": 5, "description": "Lung CT nodules"},
        {"collection": "COVID-19-AR", "modality": "CT", "patients": 5, "description": "COVID-19 chest CT"},
        {"collection": "COVID-19-AR", "modality": "DX", "patients": 5, "description": "COVID-19 chest X-ray"},
    ]
    
    output_base = Path("../data/raw")
    
    for sample in samples:
        print(f"\n{'='*70}")
        print(f"Collection: {sample['collection']} ({sample['description']})")
        print(f"{'='*70}")
        
        # Get series
        print(f"\nFetching {sample['modality']} series...")
        series = nbia.getSeries(
            collection=sample['collection'],
            modality=sample['modality'],
            format="df"
        )
        
        if series is None or series.empty:
            print(f"✗ No {sample['modality']} series found")
            continue
        
        print(f"✓ Found {len(series)} series")
        
        # Get unique patients
        unique_patients = series['PatientID'].unique()[:sample['patients']]
        
        for patient_id in unique_patients:
            patient_series = series[series['PatientID'] == patient_id].iloc[0]
            
            series_uid = patient_series['SeriesInstanceUID']
            image_count = patient_series.get('ImageCount', 0)
            
            output_dir = output_base / sample['collection'] / patient_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                print(f"  Downloading {patient_id}... ({image_count} images)")
                
                nbia.downloadSeries(
                    [series_uid],  # Pass list of UIDs as first positional argument
                    path=str(output_dir),
                    input_type="list"  # Specify input type
                )
                
                print(f"  ✓ Complete")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")

def main():
    """Main download function"""
    
    print("\n" + "="*70)
    print("🚀 TCIA DATA DOWNLOAD - EXPAND YOUR DATASET")
    print("="*70)
    
    print("\nAvailable options:")
    print("1. Download 10 more COVID-19-AR patients (recommended)")
    print("2. Download 20 COVID-19-AR patients (comprehensive)")
    print("3. Download multi-modality sample (CT + X-ray)")
    print("4. Custom download")
    
    print("\n" + "="*70)
    print("DOWNLOADING: Option 2 (20 COVID-19-AR patients - COMPREHENSIVE)")
    print("="*70)
    
    # Download 20 COVID-19 patients (comprehensive dataset)
    downloaded = download_covid_dataset(num_patients=20, collection="COVID-19-AR")
    
    if downloaded > 0:
        print("\n" + "="*70)
        print("✅ DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"\nYou now have {downloaded + 2} total patients!")
        print("\n🎯 Next steps:")
        print("  1. Run analysis on expanded dataset:")
        print("     python run_complete_analysis.py")
        print("\n  2. View updated report:")
        print("     open output/Medical_Analysis_Report.pdf")
    
    print("\n💡 To download more:")
    print("   Edit this script and change num_patients parameter")
    print("   Or run: python 07_advanced_search.py for custom searches")

if __name__ == "__main__":
    main()

