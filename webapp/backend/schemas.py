"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# ============================================================================
# PATIENT SCHEMAS
# ============================================================================

class PatientBase(BaseModel):
    patient_id: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None

class PatientOut(PatientBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# STUDY SCHEMAS
# ============================================================================

class StudyBase(BaseModel):
    patient_id: str
    study_instance_uid: str
    study_date: Optional[date] = None
    study_description: Optional[str] = None
    modality: Optional[str] = None
    body_part: Optional[str] = None
    institution_name: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_model: Optional[str] = None

class StudyOut(StudyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DICOMMetadataOut(BaseModel):
    id: int
    series_instance_uid: Optional[str]
    sop_instance_uid: Optional[str]
    slice_thickness: Optional[float]
    pixel_spacing: Optional[str]
    rows: Optional[int]
    columns: Optional[int]
    window_center: Optional[float]
    window_width: Optional[float]
    protocol_name: Optional[str]
    
    class Config:
        from_attributes = True

class ProtocolAnalysisOut(BaseModel):
    id: int
    protocol_name: Optional[str]
    manufacturer: Optional[str]
    model_name: Optional[str]
    standardization_score: Optional[float]
    drift_detected: Optional[bool]
    
    class Config:
        from_attributes = True

class QualityMetricsOut(BaseModel):
    id: int
    has_required_tags: Optional[bool]
    has_pixel_data: Optional[bool]
    standardized_orientation: Optional[bool]
    consistent_spacing: Optional[bool]
    compliance_score: Optional[float]
    issues_found: Optional[List[str]]
    
    class Config:
        from_attributes = True

class ImageStatisticsOut(BaseModel):
    id: int
    mean_intensity: Optional[float]
    std_intensity: Optional[float]
    min_intensity: Optional[float]
    max_intensity: Optional[float]
    median_intensity: Optional[float]
    snr: Optional[float]
    contrast: Optional[float]
    main_image_data: Optional[str]  # Base64 encoded image
    histogram_image_data: Optional[str]  # Base64 encoded histogram
    windowed_image_data: Optional[str]  # Base64 encoded windowed image
    
    class Config:
        from_attributes = True

class StudyDetail(BaseModel):
    study: StudyOut
    dicom_metadata: List[DICOMMetadataOut]
    protocol_analysis: Optional[ProtocolAnalysisOut]
    quality_metrics: Optional[QualityMetricsOut]
    image_statistics: Optional[ImageStatisticsOut]
    
    class Config:
        from_attributes = True

# ============================================================================
# AI ANALYSIS SCHEMAS
# ============================================================================

class AIAnalysisBase(BaseModel):
    patient_id: str
    study_id: Optional[int] = None
    model_name: str
    analysis_type: Optional[str] = None
    findings: Optional[str] = None
    confidence_score: Optional[float] = None
    covid_probability: Optional[float] = None
    severity_assessment: Optional[str] = None
    recommendations: Optional[str] = None
    analysis_json: Optional[Dict[str, Any]] = None

class AIAnalysisOut(AIAnalysisBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# DIAGNOSTIC ANALYSIS SCHEMAS
# ============================================================================

class DiagnosticAnalysisBase(BaseModel):
    patient_id: str
    study_id: Optional[int] = None
    covid_score: Optional[int] = None
    covid_probability: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[str] = None
    opacity_features: Optional[Dict[str, Any]] = None
    distribution_features: Optional[Dict[str, Any]] = None
    quantitative_features: Optional[Dict[str, Any]] = None
    clinical_reasoning: Optional[str] = None
    differential_diagnosis: Optional[str] = None
    recommendations: Optional[str] = None

class DiagnosticAnalysisOut(DiagnosticAnalysisBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# BIAS ANALYSIS SCHEMAS
# ============================================================================

class BiasAnalysisOut(BaseModel):
    id: int
    analysis_date: Optional[date]
    total_patients: Optional[int]
    total_studies: Optional[int]
    manufacturer_diversity: Optional[float]
    protocol_diversity: Optional[float]
    bias_risk_level: Optional[str]
    bias_score: Optional[float]
    recommendations: Optional[str]
    metrics_json: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# DETAIL SCHEMAS (with forward references resolved)
# ============================================================================

class PatientDetail(BaseModel):
    patient: PatientOut
    studies: List[StudyOut]
    ai_analyses: List[AIAnalysisOut]
    diagnostic_analysis: Optional[DiagnosticAnalysisOut]
    
    class Config:
        from_attributes = True

