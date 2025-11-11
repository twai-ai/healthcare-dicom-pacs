"""
Parse TCIA manifest files
"""
from pathlib import Path

def parse_manifest(manifest_path: Path):
    """Parse .tcia manifest file"""
    print(f"\n{'='*60}")
    print(f"Parsing: {manifest_path.name}")
    print(f"{'='*60}\n")
    
    with open(manifest_path, 'r') as f:
        lines = f.readlines()
    
    config = {}
    series_list = []
    in_series_list = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        if line.startswith('ListOfSeriesToDownload='):
            in_series_list = True
            continue
        
        if in_series_list:
            series_list.append(line)
        elif '=' in line:
            key, value = line.split('=', 1)
            config[key] = value
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print(f"\nSeries to download: {len(series_list)}")
    for i, series in enumerate(series_list, 1):
        print(f"  {i}. {series}")
    
    return config, series_list

if __name__ == "__main__":
    # Your COVID-19 data directory
    data_dir = Path("/Users/aeishwary/DICOM-AI/data/COVID-19")
    
    # Find all .tcia files
    manifest_files = list(data_dir.glob("*.tcia"))
    
    if not manifest_files:
        print("No .tcia manifest files found!")
        print(f"Looking in: {data_dir}")
    else:
        for manifest in manifest_files:
            config, series = parse_manifest(manifest)
            print("\n" + "="*60 + "\n")
    
    print("\n💡 Next step: Use NBIA Data Retriever to download these series")
    print("   Download from: https://wiki.cancerimagingarchive.net/display/NBIA")

