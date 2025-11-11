"""
Batch process DICOM files - extract metadata from all files
"""
import sys
from pathlib import Path
import pandas as pd
from tqdm import tqdm
sys.path.append(str(Path(__file__).parent))

from utils import find_dicom_files, read_dicom, get_metadata, save_metadata_to_json

def batch_extract_metadata(directory: Path, output_csv: Path = None):
    """Extract metadata from all DICOM files and save to CSV"""
    print(f"\nScanning directory: {directory}")
    
    dicom_files = find_dicom_files(directory)
    
    if not dicom_files:
        print("No DICOM files found!")
        return None
    
    print(f"Found {len(dicom_files)} DICOM files")
    print("Extracting metadata...\n")
    
    metadata_list = []
    
    for file in tqdm(dicom_files, desc="Processing"):
        try:
            ds = read_dicom(file)
            metadata = get_metadata(ds)
            metadata['file_path'] = str(file)
            metadata['file_name'] = file.name
            metadata['file_size_mb'] = file.stat().st_size / (1024 * 1024)
            metadata_list.append(metadata)
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue
    
    if not metadata_list:
        print("No metadata extracted!")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(metadata_list)
    
    # Save to CSV
    if output_csv is None:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_csv = output_dir / "dicom_metadata.csv"
    
    df.to_csv(output_csv, index=False)
    print(f"\n✓ Metadata saved to: {output_csv}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total files processed: {len(df)}")
    print(f"\nPatients: {df['patient_id'].nunique()}")
    print(f"Modalities: {', '.join(df['modality'].unique())}")
    print(f"\nModality breakdown:")
    print(df['modality'].value_counts())
    
    if 'study_date' in df.columns:
        print(f"\nDate range: {df['study_date'].min()} to {df['study_date'].max()}")
    
    return df

if __name__ == "__main__":
    data_dir = Path("/Users/aeishwary/DICOM-AI/data")
    
    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
    else:
        df = batch_extract_metadata(data_dir)
        
        if df is not None:
            print("\n" + "="*60)
            print("First few records:")
            print("="*60)
            print(df.head().to_string())
            
            print("\n💡 Tip: Open output/dicom_metadata.csv in Excel or Google Sheets")

