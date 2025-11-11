"""
Simple and Reliable TCIA Data Download
Downloads COVID-19 data directly using simplified approach
"""

from pathlib import Path
from tcia_utils import nbia
import time

def download_covid19_sample(num_series=10):
    """
    Download sample COVID-19 series
    
    Args:
        num_series: Number of series to download (default: 10)
    """
    
    print("\n" + "="*70)
    print("📥 SIMPLE COVID-19 DATA DOWNLOAD")
    print("="*70)
    print(f"\nDownloading {num_series} COVID-19 imaging series...")
    
    # Get COVID-19-AR series (already filtered)
    print("\nQuerying TCIA for COVID-19-AR series...")
    
    try:
        # Get series list
        series_list = nbia.getSeries(
            collection="COVID-19-AR",
            modality="DX",  # Start with X-rays (smaller, faster)
            format="df"
        )
        
        if series_list is None or series_list.empty:
            print("✗ No series found")
            return
        
        print(f"✓ Found {len(series_list)} X-ray series")
        
        # Limit to requested number
        sample_series = series_list.head(num_series)
        
        output_dir = Path("../data/raw/COVID-19-AR-Downloaded")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = 0
        
        for idx, row in sample_series.iterrows():
            patient_id = row['PatientID']
            series_uid = row['SeriesInstanceUID']
            image_count = row.get('ImageCount', 0)
            
            print(f"\n[{idx+1}/{num_series}] {patient_id}")
            print(f"  Series: {row.get('SeriesDescription', 'Unknown')}")
            print(f"  Images: {image_count}")
            print(f"  Downloading...")
            
            # Create output directory for this series
            series_dir = output_dir / f"{patient_id}_{idx}"
            series_dir.mkdir(exist_ok=True)
            
            try:
                # Download using series UID directly
                nbia.downloadSeries(
                    series_data=[series_uid],
                    path=str(series_dir)
                )
                
                # Verify download
                dcm_files = list(series_dir.rglob("*.dcm"))
                if dcm_files:
                    print(f"  ✓ Downloaded {len(dcm_files)} DICOM files")
                    downloaded += 1
                else:
                    print(f"  ⚠️  Downloaded but no .dcm files found")
                
                # Small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        print("\n" + "="*70)
        print("📊 DOWNLOAD SUMMARY")
        print("="*70)
        print(f"\n✓ Successfully downloaded: {downloaded}/{num_series} series")
        print(f"✓ Location: {output_dir}")
        
        # Count total files
        all_dcm = list(output_dir.rglob("*.dcm"))
        print(f"✓ Total DICOM files: {len(all_dcm)}")
        
        return downloaded
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return 0

def main():
    """Main execution"""
    
    print("\n" + "="*70)
    print("🚀 SIMPLE TCIA DATA DOWNLOAD")
    print("="*70)
    print("\nThis script downloads COVID-19 chest X-rays from TCIA")
    print("Starting with 10 series for quick testing...")
    
    downloaded = download_covid19_sample(num_series=10)
    
    if downloaded > 0:
        print("\n" + "="*70)
        print("✅ DOWNLOAD COMPLETE!")
        print("="*70)
        print(f"\nYou now have {downloaded} additional series!")
        print("\n🎯 Next steps:")
        print("  1. Verify download:")
        print("     ls -R ../data/raw/COVID-19-AR-Downloaded/")
        print("\n  2. Run analysis:")
        print("     python run_complete_analysis.py")
        print("\n  3. View updated report:")
        print("     open output/Medical_Analysis_Report.pdf")
    else:
        print("\n⚠️  Download failed or incomplete")
        print("\nAlternatives:")
        print("  1. Check internet connection")
        print("  2. Try again: python simple_data_download.py")
        print("  3. Use NBIA Data Retriever (manual download)")

if __name__ == "__main__":
    main()

