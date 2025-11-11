"""
Image Processing and Visualization
Generates images, histograms, and visualizations from DICOM data
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import pydicom
from PIL import Image
from pathlib import Path
import io
import base64

class ImageProcessor:
    """Process DICOM images for web display"""
    
    @staticmethod
    def dicom_to_png_base64(dicom_path: str) -> str:
        """Convert DICOM to PNG and encode as base64 for web display"""
        try:
            ds = pydicom.dcmread(dicom_path)
            pixel_array = ds.pixel_array
            
            # Normalize to 0-255
            pixel_array = ((pixel_array - pixel_array.min()) / 
                          (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            
            # Convert to PIL Image
            img = Image.fromarray(pixel_array)
            
            # Resize if too large (max 800px)
            if max(img.size) > 800:
                ratio = 800 / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error converting DICOM to PNG: {e}")
            return None
    
    @staticmethod
    def generate_histogram_base64(pixel_array: np.ndarray) -> str:
        """Generate histogram and return as base64"""
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            
            # Create histogram
            ax.hist(pixel_array.flatten(), bins=50, color='#2563eb', alpha=0.7, edgecolor='black')
            ax.set_xlabel('Pixel Intensity', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('Pixel Intensity Distribution', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add statistics
            mean_val = np.mean(pixel_array)
            std_val = np.std(pixel_array)
            ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.0f}')
            ax.axvline(mean_val + std_val, color='orange', linestyle=':', linewidth=1.5, label=f'±1 Std Dev')
            ax.axvline(mean_val - std_val, color='orange', linestyle=':', linewidth=1.5)
            ax.legend()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='PNG', dpi=100, bbox_inches='tight')
            plt.close()
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error generating histogram: {e}")
            return None
    
    @staticmethod
    def generate_analysis_images(dicom_path: str) -> dict:
        """Generate all visualization images for a DICOM file"""
        try:
            ds = pydicom.dcmread(dicom_path)
            pixel_array = ds.pixel_array
            
            # 1. Main image
            main_image = ImageProcessor.dicom_to_png_base64(dicom_path)
            
            # 2. Histogram
            histogram = ImageProcessor.generate_histogram_base64(pixel_array)
            
            # 3. Windowed image (if applicable)
            windowed_image = None
            if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
                try:
                    window_center = float(ds.WindowCenter)
                    window_width = float(ds.WindowWidth)
                    
                    # Apply windowing
                    img_min = window_center - window_width / 2
                    img_max = window_center + window_width / 2
                    
                    windowed = np.clip(pixel_array, img_min, img_max)
                    windowed = ((windowed - img_min) / (img_max - img_min) * 255).astype(np.uint8)
                    
                    img = Image.fromarray(windowed)
                    if max(img.size) > 800:
                        ratio = 800 / max(img.size)
                        img = img.resize(tuple(int(dim * ratio) for dim in img.size), Image.Resampling.LANCZOS)
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    windowed_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
                except:
                    pass
            
            return {
                'main_image': main_image,
                'histogram': histogram,
                'windowed_image': windowed_image,
                'has_images': True
            }
            
        except Exception as e:
            print(f"Error generating analysis images: {e}")
            return {
                'has_images': False,
                'error': str(e)
            }

