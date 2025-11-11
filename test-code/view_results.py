"""
View all analysis results
Opens generated images and displays summary
"""
from pathlib import Path
import pandas as pd
import subprocess
import sys

def view_results():
    """Display all analysis results"""
    output_dir = Path(__file__).parent / "output"
    
    print("="*60)
    print("DICOM ANALYSIS RESULTS")
    print("="*60)
    
    # Check if output exists
    if not output_dir.exists():
        print("\n⚠️  No output directory found!")
        print("Please run the analysis scripts first:")
        print("  python 03_explore_dicom.py")
        print("  python 04_basic_analysis.py")
        print("  python 05_batch_process.py")
        return
    
    # List output files
    files = list(output_dir.glob("*"))
    if not files:
        print("\n⚠️  No output files found!")
        return
    
    print(f"\n📁 Output Directory: {output_dir}")
    print(f"\n📊 Generated Files ({len(files)}):")
    
    images = []
    csv_files = []
    
    for file in sorted(files):
        size = file.stat().st_size / 1024  # KB
        print(f"  • {file.name:30s} ({size:8.1f} KB)")
        
        if file.suffix in ['.png', '.jpg', '.jpeg']:
            images.append(file)
        elif file.suffix == '.csv':
            csv_files.append(file)
    
    # Display CSV summary
    if csv_files:
        print("\n" + "="*60)
        print("METADATA SUMMARY")
        print("="*60)
        
        for csv_file in csv_files:
            print(f"\nFrom: {csv_file.name}")
            df = pd.read_csv(csv_file)
            print(df.to_string(index=False))
    
    # Offer to open images
    print("\n" + "="*60)
    print("IMAGE FILES")
    print("="*60)
    
    if images:
        print(f"\nFound {len(images)} image files:")
        for img in images:
            print(f"  • {img.name}")
        
        print("\n💡 To view images:")
        print(f"   open {output_dir}")
        print("\n   Or individually:")
        for img in images:
            print(f"   open {img}")
    
    print("\n" + "="*60)
    print("✓ Analysis complete!")
    print("="*60)
    
    print("\n📄 For detailed summary, see: RESULTS_SUMMARY.md")
    
    # Auto-open on macOS
    if sys.platform == 'darwin':
        print("\n🖼️  Opening output folder...")
        subprocess.run(['open', str(output_dir)])

if __name__ == "__main__":
    view_results()

