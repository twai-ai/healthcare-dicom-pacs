"""
Enhanced TCIA Data Download using Official REST API
Based on: https://wiki.cancerimagingarchive.net/display/Public/TCIA+Programmatic+Interface+REST+API+Guides

This script uses the official tcia_utils package for programmatic access to TCIA data.
"""

import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
import json

try:
    from tcia_utils import nbia
except ImportError:
    print("⚠️  tcia_utils not installed!")
    print("\nInstalling required package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "tcia_utils"])
    from tcia_utils import nbia
    print("✓ tcia_utils installed successfully")

class TCIADataManager:
    """
    Enhanced TCIA data manager using official REST API
    Reference: https://wiki.cancerimagingarchive.net/display/Public/TCIA+Programmatic+Interface+REST+API+Guides
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path("../data/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def browse_collections(self, format: str = "df") -> pd.DataFrame:
        """
        Browse all available TCIA collections
        
        Args:
            format: 'df' for DataFrame, 'json' for JSON
        
        Returns:
            DataFrame or JSON with collection information
        """
        print("\n" + "="*60)
        print("BROWSING TCIA COLLECTIONS")
        print("="*60)
        print("\nFetching available collections from TCIA...")
        
        try:
            collections = nbia.getCollections(format=format)
            
            if format == "df" and isinstance(collections, pd.DataFrame):
                print(f"\n✓ Found {len(collections)} collections")
                print("\nTop Collections:")
                print(collections.head(10).to_string())
                
                # Save to CSV
                csv_path = self.output_dir / "tcia_collections.csv"
                collections.to_csv(csv_path, index=False)
                print(f"\n✓ Collections saved to: {csv_path}")
                
            return collections
            
        except Exception as e:
            print(f"\n✗ Error fetching collections: {e}")
            return None
    
    def search_collections(self, keywords: List[str]) -> pd.DataFrame:
        """
        Search collections by keywords
        
        Args:
            keywords: List of keywords to search (e.g., ['COVID', 'lung', 'chest'])
        """
        print("\n" + "="*60)
        print("SEARCHING COLLECTIONS")
        print("="*60)
        print(f"\nKeywords: {', '.join(keywords)}")
        
        collections = self.browse_collections()
        if collections is None or collections.empty:
            return None
        
        # Filter by keywords
        mask = collections['Collection'].str.contains('|'.join(keywords), case=False, na=False)
        results = collections[mask]
        
        print(f"\n✓ Found {len(results)} matching collections:")
        for idx, row in results.iterrows():
            print(f"  • {row['Collection']}")
        
        return results
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """
        Get detailed information about a specific collection
        
        Args:
            collection_name: Name of the collection (e.g., 'COVID-19-AR')
        """
        print("\n" + "="*60)
        print(f"COLLECTION INFO: {collection_name}")
        print("="*60)
        
        try:
            # Get patients in collection
            patients = nbia.getPatient(collection=collection_name, format="df")
            
            # Get series/studies
            series = nbia.getSeries(collection=collection_name, format="df")
            
            info = {
                'collection': collection_name,
                'total_patients': len(patients) if isinstance(patients, pd.DataFrame) else 0,
                'total_series': len(series) if isinstance(series, pd.DataFrame) else 0,
            }
            
            if isinstance(series, pd.DataFrame) and not series.empty:
                info['modalities'] = series['Modality'].unique().tolist()
                info['body_parts'] = series['BodyPartExamined'].unique().tolist()
                info['total_images'] = series['ImageCount'].sum() if 'ImageCount' in series.columns else 'Unknown'
            
            print(f"\nCollection: {info['collection']}")
            print(f"Patients: {info['total_patients']}")
            print(f"Series: {info['total_series']}")
            print(f"Modalities: {info.get('modalities', 'Unknown')}")
            print(f"Body Parts: {info.get('body_parts', 'Unknown')}")
            print(f"Total Images: {info.get('total_images', 'Unknown')}")
            
            return info
            
        except Exception as e:
            print(f"\n✗ Error getting collection info: {e}")
            return None
    
    def download_collection_sample(self, collection_name: str, num_patients: int = 2):
        """
        Download sample data from a collection
        
        Args:
            collection_name: Name of the collection
            num_patients: Number of patients to download
        """
        print("\n" + "="*60)
        print(f"DOWNLOADING SAMPLE DATA: {collection_name}")
        print("="*60)
        print(f"\nFetching up to {num_patients} patient(s)...")
        
        try:
            # Get patient list
            patients = nbia.getPatient(collection=collection_name, format="df")
            
            if patients is None or patients.empty:
                print(f"\n✗ No patients found in collection: {collection_name}")
                return
            
            print(f"✓ Found {len(patients)} patients in collection")
            
            # Limit to requested number
            sample_patients = patients.head(num_patients)
            
            for idx, patient in sample_patients.iterrows():
                patient_id = patient['PatientID']
                print(f"\n[{idx+1}/{len(sample_patients)}] Patient: {patient_id}")
                
                # Get series for this patient
                series = nbia.getSeries(
                    collection=collection_name,
                    patientId=patient_id,
                    format="df"
                )
                
                if series is None or series.empty:
                    print(f"  ✗ No series found")
                    continue
                
                print(f"  ✓ Found {len(series)} series")
                
                # Download first series
                series_uid = series.iloc[0]['SeriesInstanceUID']
                modality = series.iloc[0]['Modality']
                
                print(f"  Downloading {modality} series...")
                
                # Create output directory
                patient_dir = self.output_dir / collection_name / patient_id
                patient_dir.mkdir(parents=True, exist_ok=True)
                
                # Download series
                nbia.downloadSeries(
                    series_uid=series_uid,
                    input_type="uid",
                    path=str(patient_dir)
                )
                
                print(f"  ✓ Downloaded to: {patient_dir}")
            
            print("\n" + "="*60)
            print("✓ Download Complete!")
            print("="*60)
            print(f"\nData saved to: {self.output_dir / collection_name}")
            
        except Exception as e:
            print(f"\n✗ Error downloading data: {e}")
            print("\nTroubleshooting:")
            print("1. Check your internet connection")
            print("2. Verify collection name is correct")
            print("3. Some collections may require authentication")
    
    def search_by_modality(self, modality: str) -> pd.DataFrame:
        """
        Search for collections by imaging modality
        
        Args:
            modality: CT, MR, CR, DX, US, PT, etc.
        """
        print("\n" + "="*60)
        print(f"SEARCHING BY MODALITY: {modality}")
        print("="*60)
        
        try:
            # Get all modalities
            modalities = nbia.getModality(format="df")
            
            if modalities is not None and not modalities.empty:
                print(f"\nAvailable modalities:")
                for m in modalities['Modality'].unique():
                    print(f"  • {m}")
                
                # Get series with this modality
                series = nbia.getSeries(modality=modality, format="df")
                
                if series is not None and not series.empty:
                    print(f"\n✓ Found {len(series)} series with modality: {modality}")
                    
                    # Get unique collections
                    collections = series['Collection'].unique()
                    print(f"\nCollections with {modality} data:")
                    for coll in collections:
                        count = len(series[series['Collection'] == coll])
                        print(f"  • {coll} ({count} series)")
                    
                    return series
                else:
                    print(f"\n✗ No series found with modality: {modality}")
            
        except Exception as e:
            print(f"\n✗ Error searching by modality: {e}")
        
        return None
    
    def search_by_body_part(self, body_part: str) -> pd.DataFrame:
        """
        Search for collections by body part
        
        Args:
            body_part: chest, head, abdomen, etc.
        """
        print("\n" + "="*60)
        print(f"SEARCHING BY BODY PART: {body_part}")
        print("="*60)
        
        try:
            # Get all body parts
            body_parts = nbia.getBodyPart(format="df")
            
            if body_parts is not None and not body_parts.empty:
                print(f"\nAvailable body parts:")
                for bp in body_parts['BodyPartExamined'].unique()[:20]:
                    print(f"  • {bp}")
                
                # Search for matching series
                series = nbia.getSeries(bodyPartExamined=body_part, format="df")
                
                if series is not None and not series.empty:
                    print(f"\n✓ Found {len(series)} series with body part: {body_part}")
                    return series
                else:
                    print(f"\n✗ No series found with body part: {body_part}")
            
        except Exception as e:
            print(f"\n✗ Error searching by body part: {e}")
        
        return None
    
    def generate_citation(self, collection_name: str):
        """
        Generate proper citation for a TCIA collection
        Reference: TCIA Data Usage Policy
        """
        print("\n" + "="*60)
        print(f"CITATION FOR: {collection_name}")
        print("="*60)
        
        citation = f"""
        
Data Citation:
--------------
[Collection Name] (The Cancer Imaging Archive)
DOI: [To be retrieved from DataCite API]
https://www.cancerimagingarchive.net/collection/{collection_name.lower()}/

Acknowledgment Statement:
-------------------------
"Data used in this publication were obtained from The Cancer Imaging 
Archive (TCIA) sponsored by the Cancer Imaging Program, DCCPS, NCI. 
The Cancer Imaging Archive (TCIA) is funded by the Cancer Imaging 
Program, a part of the United States National Cancer Institute."

TCIA Data Usage Policy:
-----------------------
https://wiki.cancerimagingarchive.net/x/c4hF

Please consult the specific collection page for detailed citation 
requirements and any additional usage restrictions.
        """
        
        print(citation)
        
        # Save citation
        citation_path = self.output_dir / f"{collection_name}_citation.txt"
        with open(citation_path, 'w') as f:
            f.write(citation)
        
        print(f"\n✓ Citation saved to: {citation_path}")


def main():
    """Main function with examples"""
    
    print("\n" + "="*60)
    print("TCIA REST API - ENHANCED DATA MANAGER")
    print("="*60)
    print("\nUsing official tcia_utils package")
    print("Reference: https://wiki.cancerimagingarchive.net/")
    print("API Guide: TCIA Programmatic Interface REST API Guides")
    
    manager = TCIADataManager(output_dir="../data/raw")
    
    # Main menu
    print("\n" + "="*60)
    print("WHAT WOULD YOU LIKE TO DO?")
    print("="*60)
    print("\n1. Browse all collections")
    print("2. Search COVID-19 collections")
    print("3. Search by modality (e.g., CT, MR)")
    print("4. Get collection info")
    print("5. Download sample data")
    print("6. Generate citation")
    print("7. Search by body part")
    
    print("\n" + "="*60)
    print("RUNNING DEMO MODE")
    print("="*60)
    
    # Demo: Browse collections
    print("\n[DEMO 1] Browsing all TCIA collections...")
    collections = manager.browse_collections()
    
    # Demo: Search COVID collections
    print("\n[DEMO 2] Searching for COVID-19 collections...")
    covid_collections = manager.search_collections(['COVID', 'coronavirus'])
    
    # Demo: Search by modality
    print("\n[DEMO 3] Searching for CT scans...")
    ct_series = manager.search_by_modality('CT')
    
    # Demo: Get collection info
    if covid_collections is not None and not covid_collections.empty:
        collection_name = covid_collections.iloc[0]['Collection']
        print(f"\n[DEMO 4] Getting info for: {collection_name}")
        info = manager.get_collection_info(collection_name)
        
        # Demo: Generate citation
        print(f"\n[DEMO 5] Generating citation for: {collection_name}")
        manager.generate_citation(collection_name)
    
    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)
    print("\nYou can now use this script to:")
    print("• Browse 200+ TCIA collections")
    print("• Search by keywords, modality, body part")
    print("• Download specific datasets")
    print("• Generate proper citations")
    print("• Access full DICOM metadata")
    
    print("\n💡 Tip: Edit this script to customize your searches!")


if __name__ == "__main__":
    main()

