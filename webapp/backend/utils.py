"""
Utility functions for DICOM processing
"""
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Optional
import json

def find_dicom_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Find all DICOM files in a directory"""
    pattern = "**/*" if recursive else "*"
    dicom_files = []
    
    for file in directory.glob(pattern):
        if file.is_file() and not file.name.startswith('.'):
            try:
                # Try to read as DICOM (just header, not pixels)
                pydicom.dcmread(file, stop_before_pixels=True)
                dicom_files.append(file)
            except:
                continue
    
    return dicom_files

def read_dicom(file_path: Path) -> pydicom.Dataset:
    """Read a DICOM file"""
    return pydicom.dcmread(file_path)

def get_metadata(ds: pydicom.Dataset) -> Dict:
    """Extract key metadata from DICOM dataset"""
    metadata = {
        'patient_id': str(ds.get('PatientID', 'Unknown')),
        'patient_name': str(ds.get('PatientName', 'Unknown')),
        'patient_age': str(ds.get('PatientAge', 'Unknown')),
        'patient_sex': str(ds.get('PatientSex', 'Unknown')),
        'study_date': str(ds.get('StudyDate', 'Unknown')),
        'study_time': str(ds.get('StudyTime', 'Unknown')),
        'study_description': str(ds.get('StudyDescription', 'Unknown')),
        'series_description': str(ds.get('SeriesDescription', 'Unknown')),
        'modality': str(ds.get('Modality', 'Unknown')),
        'manufacturer': str(ds.get('Manufacturer', 'Unknown')),
        'institution': str(ds.get('InstitutionName', 'Unknown')),
    }
    
    # Add image-specific metadata if available
    if hasattr(ds, 'Rows'):
        metadata['image_size'] = f"{ds.Rows}x{ds.Columns}"
        metadata['bits_stored'] = ds.get('BitsStored', 'Unknown')
        metadata['pixel_spacing'] = str(ds.get('PixelSpacing', 'Unknown'))
    
    # Add modality-specific metadata
    if ds.Modality == 'CT':
        metadata['slice_thickness'] = str(ds.get('SliceThickness', 'Unknown'))
        metadata['kvp'] = str(ds.get('KVP', 'Unknown'))
        metadata['convolution_kernel'] = str(ds.get('ConvolutionKernel', 'Unknown'))
    
    return metadata

def display_dicom_image(ds: pydicom.Dataset, title: str = None, 
                        window_center: int = None, window_width: int = None,
                        save_path: str = None):
    """Display DICOM image with proper windowing"""
    if not hasattr(ds, 'pixel_array'):
        print("No pixel data in this DICOM file")
        return
    
    img = ds.pixel_array.astype(float)
    
    # Apply rescale if available
    if hasattr(ds, 'RescaleIntercept') and hasattr(ds, 'RescaleSlope'):
        img = img * ds.RescaleSlope + ds.RescaleIntercept
    
    # Apply windowing for better visualization
    if window_center is None and hasattr(ds, 'WindowCenter'):
        window_center = ds.WindowCenter
        if isinstance(window_center, pydicom.multival.MultiValue):
            window_center = window_center[0]
    
    if window_width is None and hasattr(ds, 'WindowWidth'):
        window_width = ds.WindowWidth
        if isinstance(window_width, pydicom.multival.MultiValue):
            window_width = window_width[0]
    
    # Display
    plt.figure(figsize=(10, 10))
    
    if window_center and window_width:
        vmin = window_center - window_width / 2
        vmax = window_center + window_width / 2
        plt.imshow(img, cmap='gray', vmin=vmin, vmax=vmax)
    else:
        plt.imshow(img, cmap='gray')
    
    title_text = title or f"{ds.Modality} - {ds.get('SeriesDescription', 'Unknown')}"
    plt.title(title_text)
    plt.colorbar(label='Intensity')
    plt.axis('off')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Image saved to {save_path}")
    
    plt.close()

def save_metadata_to_json(metadata: Dict, output_path: Path):
    """Save metadata to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to {output_path}")

def print_metadata(metadata: Dict):
    """Pretty print metadata"""
    print("\n" + "="*60)
    print("DICOM METADATA")
    print("="*60)
    for key, value in metadata.items():
        print(f"{key:20s}: {value}")
    print("="*60 + "\n")

