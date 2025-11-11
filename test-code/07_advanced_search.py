"""
Advanced TCIA Search using REST API
Demonstrates advanced querying capabilities with filters and batch operations
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

try:
    from tcia_utils import nbia, datacite
except ImportError:
    print("Installing tcia_utils...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "tcia_utils"])
    from tcia_utils import nbia, datacite

class AdvancedTCIASearch:
    """
    Advanced search capabilities for TCIA data
    Leverages full power of NBIA v4 REST API
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def search_covid_datasets(self) -> pd.DataFrame:
        """Search for all COVID-19 related datasets"""
        print("\n" + "="*60)
        print("SEARCHING COVID-19 DATASETS")
        print("="*60)
        
        # Keywords to search
        covid_keywords = ['COVID', 'coronavirus', 'SARS-CoV-2', 'pandemic']
        
        all_collections = nbia.getCollections(format="df")
        
        if all_collections is None or all_collections.empty:
            print("No collections found")
            return None
        
        # Filter COVID-related
        mask = all_collections['Collection'].str.contains(
            '|'.join(covid_keywords), 
            case=False, 
            na=False
        )
        covid_collections = all_collections[mask]
        
        print(f"\n✓ Found {len(covid_collections)} COVID-19 collections:")
        
        results = []
        for idx, row in covid_collections.iterrows():
            collection = row['Collection']
            print(f"\n  {idx+1}. {collection}")
            
            try:
                # Get detailed info
                series = nbia.getSeries(collection=collection, format="df")
                
                if series is not None and not series.empty:
                    info = {
                        'Collection': collection,
                        'Total_Series': len(series),
                        'Total_Images': series['ImageCount'].sum() if 'ImageCount' in series.columns else 0,
                        'Modalities': ', '.join(series['Modality'].unique()),
                        'Patients': series['PatientID'].nunique()
                    }
                    results.append(info)
                    
                    print(f"     Series: {info['Total_Series']}")
                    print(f"     Images: {info['Total_Images']}")
                    print(f"     Modalities: {info['Modalities']}")
                    print(f"     Patients: {info['Patients']}")
            except Exception as e:
                print(f"     Error getting details: {e}")
        
        if results:
            df = pd.DataFrame(results)
            csv_path = self.output_dir / "covid_datasets_detailed.csv"
            df.to_csv(csv_path, index=False)
            print(f"\n✓ Detailed results saved to: {csv_path}")
            return df
        
        return None
    
    def search_lung_imaging(self, modality: Optional[str] = None) -> pd.DataFrame:
        """
        Search for lung/chest imaging across all collections
        
        Args:
            modality: Filter by specific modality (CT, CR, DX, etc.)
        """
        print("\n" + "="*60)
        print("SEARCHING LUNG/CHEST IMAGING")
        print("="*60)
        if modality:
            print(f"Modality filter: {modality}")
        
        # Body parts related to lung imaging
        body_parts = ['CHEST', 'LUNG', 'THORAX']
        
        results = []
        for body_part in body_parts:
            try:
                print(f"\nSearching for: {body_part}...")
                series = nbia.getSeries(
                    bodyPartExamined=body_part,
                    modality=modality if modality else None,
                    format="df"
                )
                
                if series is not None and not series.empty:
                    print(f"  ✓ Found {len(series)} series")
                    results.append(series)
            except Exception as e:
                print(f"  Error: {e}")
        
        if results:
            combined = pd.concat(results, ignore_index=True)
            combined = combined.drop_duplicates(subset=['SeriesInstanceUID'])
            
            print(f"\n{'='*60}")
            print(f"TOTAL RESULTS: {len(combined)} unique series")
            print(f"{'='*60}")
            
            # Summary
            print(f"\nCollections: {combined['Collection'].nunique()}")
            print(f"Patients: {combined['PatientID'].nunique()}")
            print(f"Modalities: {', '.join(combined['Modality'].unique())}")
            
            # Save results
            csv_path = self.output_dir / "lung_imaging_search.csv"
            combined.to_csv(csv_path, index=False)
            print(f"\n✓ Results saved to: {csv_path}")
            
            return combined
        
        return None
    
    def search_by_manufacturer(self, manufacturer: str) -> pd.DataFrame:
        """Search for studies by equipment manufacturer"""
        print("\n" + "="*60)
        print(f"SEARCHING BY MANUFACTURER: {manufacturer}")
        print("="*60)
        
        try:
            series = nbia.getSeries(manufacturer=manufacturer, format="df")
            
            if series is not None and not series.empty:
                print(f"\n✓ Found {len(series)} series from {manufacturer}")
                
                # Group by modality
                print("\nBreakdown by modality:")
                for modality in series['Modality'].unique():
                    count = len(series[series['Modality'] == modality])
                    print(f"  • {modality}: {count} series")
                
                return series
            else:
                print(f"\n✗ No series found from: {manufacturer}")
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        return None
    
    def search_by_date_range(self, 
                            collection: str,
                            start_date: str = None,
                            end_date: str = None) -> pd.DataFrame:
        """
        Search for studies within a date range
        
        Args:
            collection: Collection name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        print("\n" + "="*60)
        print(f"SEARCHING BY DATE RANGE: {collection}")
        print("="*60)
        
        if start_date:
            print(f"From: {start_date}")
        if end_date:
            print(f"To: {end_date}")
        
        try:
            series = nbia.getSeries(
                collection=collection,
                dateRange=f"{start_date}/{end_date}" if start_date and end_date else None,
                format="df"
            )
            
            if series is not None and not series.empty:
                print(f"\n✓ Found {len(series)} series in date range")
                
                # Show date distribution
                if 'StudyDate' in series.columns:
                    print("\nDate distribution:")
                    series['StudyDate'] = pd.to_datetime(series['StudyDate'], format='%Y%m%d', errors='coerce')
                    print(f"  Earliest: {series['StudyDate'].min()}")
                    print(f"  Latest: {series['StudyDate'].max()}")
                
                return series
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        return None
    
    def advanced_filter(self,
                       collection: Optional[str] = None,
                       modality: Optional[str] = None,
                       body_part: Optional[str] = None,
                       manufacturer: Optional[str] = None,
                       min_images: int = 0) -> pd.DataFrame:
        """
        Apply multiple filters simultaneously
        
        Args:
            collection: Collection name
            modality: Imaging modality
            body_part: Body part examined
            manufacturer: Equipment manufacturer
            min_images: Minimum number of images per series
        """
        print("\n" + "="*60)
        print("ADVANCED MULTI-FILTER SEARCH")
        print("="*60)
        
        print("\nFilters:")
        if collection:
            print(f"  Collection: {collection}")
        if modality:
            print(f"  Modality: {modality}")
        if body_part:
            print(f"  Body Part: {body_part}")
        if manufacturer:
            print(f"  Manufacturer: {manufacturer}")
        if min_images > 0:
            print(f"  Min Images: {min_images}")
        
        try:
            series = nbia.getSeries(
                collection=collection,
                modality=modality,
                bodyPartExamined=body_part,
                manufacturer=manufacturer,
                format="df"
            )
            
            if series is None or series.empty:
                print("\n✗ No results found")
                return None
            
            # Apply image count filter
            if min_images > 0 and 'ImageCount' in series.columns:
                series = series[series['ImageCount'] >= min_images]
            
            print(f"\n✓ Found {len(series)} series matching all criteria")
            
            # Summary
            print("\nResults summary:")
            print(f"  Collections: {series['Collection'].nunique()}")
            print(f"  Patients: {series['PatientID'].nunique()}")
            print(f"  Total Images: {series['ImageCount'].sum() if 'ImageCount' in series.columns else 'Unknown'}")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = self.output_dir / f"advanced_search_{timestamp}.csv"
            series.to_csv(csv_path, index=False)
            print(f"\n✓ Results saved to: {csv_path}")
            
            return series
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        return None
    
    def get_collection_doi(self, collection: str):
        """
        Get DOI and citation information using DataCite API
        
        Args:
            collection: Collection name
        """
        print("\n" + "="*60)
        print(f"GETTING DOI FOR: {collection}")
        print("="*60)
        
        try:
            # Get DOI information from DataCite
            doi_info = datacite.getDOI(collection)
            
            if doi_info:
                print("\n✓ DOI Information Retrieved")
                print(f"\nDOI: {doi_info.get('doi', 'Not found')}")
                print(f"Title: {doi_info.get('title', 'Not found')}")
                print(f"Publisher: {doi_info.get('publisher', 'Not found')}")
                print(f"Publication Year: {doi_info.get('publicationYear', 'Not found')}")
                
                # Generate proper citation
                citation = self._format_citation(collection, doi_info)
                print("\n" + "="*60)
                print("FORMATTED CITATION")
                print("="*60)
                print(citation)
                
                # Save citation
                citation_path = self.output_dir / f"{collection}_citation.txt"
                with open(citation_path, 'w') as f:
                    f.write(citation)
                print(f"\n✓ Citation saved to: {citation_path}")
                
                return doi_info
            
        except Exception as e:
            print(f"\n✗ Error retrieving DOI: {e}")
        
        return None
    
    def _format_citation(self, collection: str, doi_info: Dict) -> str:
        """Format proper citation for a collection"""
        
        authors = doi_info.get('creators', [])
        author_str = ", ".join([a.get('name', '') for a in authors]) if authors else "The Cancer Imaging Archive"
        
        title = doi_info.get('title', collection)
        year = doi_info.get('publicationYear', datetime.now().year)
        doi = doi_info.get('doi', '')
        
        citation = f"""
{author_str}. ({year}). {title}. 
The Cancer Imaging Archive (TCIA). 
https://doi.org/{doi}

Acknowledgment:
Data used in this publication were obtained from The Cancer Imaging Archive (TCIA) 
sponsored by the Cancer Imaging Program, DCCPS, NCI. The Cancer Imaging Archive 
(TCIA) is funded by the Cancer Imaging Program, a part of the United States 
National Cancer Institute.

TCIA Data Usage Policy:
https://wiki.cancerimagingarchive.net/x/c4hF
        """
        
        return citation.strip()


def main():
    """Demonstrate advanced search capabilities"""
    
    print("\n" + "="*60)
    print("ADVANCED TCIA SEARCH DEMONSTRATION")
    print("="*60)
    print("\nLeveraging NBIA v4 REST API")
    print("Reference: https://wiki.cancerimagingarchive.net/")
    
    searcher = AdvancedTCIASearch()
    
    # Demo 1: Search COVID datasets
    print("\n[DEMO 1] Searching for COVID-19 datasets...")
    covid_data = searcher.search_covid_datasets()
    
    # Demo 2: Search lung imaging
    print("\n[DEMO 2] Searching for CT lung imaging...")
    lung_data = searcher.search_lung_imaging(modality='CT')
    
    # Demo 3: Advanced multi-filter search
    print("\n[DEMO 3] Advanced multi-filter search...")
    filtered = searcher.advanced_filter(
        modality='CT',
        body_part='CHEST',
        min_images=10
    )
    
    # Demo 4: Get DOI and citation
    if covid_data is not None and not covid_data.empty:
        collection_name = covid_data.iloc[0]['Collection']
        print(f"\n[DEMO 4] Getting DOI for: {collection_name}")
        searcher.get_collection_doi(collection_name)
    
    print("\n" + "="*60)
    print("✓ ADVANCED SEARCH DEMO COMPLETE")
    print("="*60)
    print("\nAll search results saved to output/ directory")
    print("\nYou can now:")
    print("• Search 200+ collections with advanced filters")
    print("• Get proper DOI citations")
    print("• Filter by multiple criteria simultaneously")
    print("• Export results to CSV for analysis")


if __name__ == "__main__":
    main()

