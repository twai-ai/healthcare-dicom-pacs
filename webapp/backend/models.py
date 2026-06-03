"""
SQLAlchemy ORM models for DICOM-AI Platform
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(255), unique=True, nullable=False, index=True)
    patient_name = Column(String(255))
    patient_age = Column(Integer)
    patient_sex = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    studies = relationship("Study", back_populates="patient")
    ai_analyses = relationship("AIAnalysis", back_populates="patient")
    diagnostic_analyses = relationship("DiagnosticAnalysis", back_populates="patient")

class Study(Base):
    __tablename__ = "studies"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(255), ForeignKey("patients.patient_id"))
    study_instance_uid = Column(String(255), unique=True, nullable=False)
    study_date = Column(Date)
    study_description = Column(Text)
    modality = Column(String(50), index=True)
    body_part = Column(String(100))
    institution_name = Column(String(255))
    manufacturer = Column(String(255))
    manufacturer_model = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="studies")
    dicom_metadata = relationship("DICOMMetadata", back_populates="study")
    ai_analyses = relationship("AIAnalysis", back_populates="study")
    diagnostic_analyses = relationship("DiagnosticAnalysis", back_populates="study")
    protocol_analyses = relationship("ProtocolAnalysis", back_populates="study")
    quality_metrics = relationship("QualityMetrics", back_populates="study")
    image_statistics = relationship("ImageStatistics", back_populates="study")

class DICOMMetadata(Base):
    __tablename__ = "dicom_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    series_instance_uid = Column(String(255))
    sop_instance_uid = Column(String(255), unique=True)
    image_path = Column(Text)
    slice_thickness = Column(Float)
    pixel_spacing = Column(String(50))
    rows = Column(Integer)
    columns = Column(Integer)
    window_center = Column(Float)
    window_width = Column(Float)
    kvp = Column(Float)
    exposure_time = Column(Float)
    protocol_name = Column(String(255))
    metadata_json = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    study = relationship("Study", back_populates="dicom_metadata")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(255), ForeignKey("patients.patient_id"), index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    model_name = Column(String(100), index=True)
    analysis_type = Column(String(50))
    findings = Column(Text)
    confidence_score = Column(Float)
    covid_probability = Column(Float)
    severity_assessment = Column(String(50))
    recommendations = Column(Text)
    analysis_json = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="ai_analyses")
    study = relationship("Study", back_populates="ai_analyses")

class DiagnosticAnalysis(Base):
    __tablename__ = "diagnostic_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(255), ForeignKey("patients.patient_id"), index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    covid_score = Column(Integer)
    covid_probability = Column(String(50))
    severity = Column(String(50))
    confidence = Column(String(50))
    opacity_features = Column(JSONB)
    distribution_features = Column(JSONB)
    quantitative_features = Column(JSONB)
    clinical_reasoning = Column(Text)
    differential_diagnosis = Column(Text)
    recommendations = Column(Text)
    findings_json = Column(JSONB)
    engine_version = Column(String(32))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="diagnostic_analyses")
    study = relationship("Study", back_populates="diagnostic_analyses")


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(255))
    version = Column(String(32))
    source = Column(String(64))
    task = Column(String(128))
    stats_json = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())


class GroundTruthLabel(Base):
    __tablename__ = "ground_truth_labels"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(128), index=True, nullable=False)
    study_instance_uid = Column(String(255), index=True, nullable=False)
    patient_id = Column(String(255))
    pattern_score_gt = Column(Integer)
    pattern_label_gt = Column(String(64))
    severity_gt = Column(String(128))
    covid_label = Column(String(64))
    reader_id = Column(String(128))
    source = Column(String(64))
    provenance_json = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    dataset_id = Column(String(128), index=True)
    engine_version = Column(String(32))
    output_path = Column(Text)
    metrics_json = Column(JSONB)
    git_commit = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())

class ProtocolAnalysis(Base):
    __tablename__ = "protocol_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    protocol_name = Column(String(255))
    manufacturer = Column(String(255))
    model_name = Column(String(255))
    slice_thickness = Column(Float)
    pixel_spacing = Column(String(50))
    kvp = Column(Float)
    standardization_score = Column(Float)
    drift_detected = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    study = relationship("Study", back_populates="protocol_analyses")

class BiasAnalysis(Base):
    __tablename__ = "bias_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_date = Column(Date)
    total_patients = Column(Integer)
    total_studies = Column(Integer)
    manufacturer_diversity = Column(Float)
    protocol_diversity = Column(Float)
    bias_risk_level = Column(String(50))
    bias_score = Column(Float)
    recommendations = Column(Text)
    metrics_json = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

class QualityMetrics(Base):
    __tablename__ = "quality_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    has_required_tags = Column(Boolean)
    has_pixel_data = Column(Boolean)
    standardized_orientation = Column(Boolean)
    consistent_spacing = Column(Boolean)
    compliance_score = Column(Float)
    issues_found = Column(ARRAY(Text))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    study = relationship("Study", back_populates="quality_metrics")

class ImageStatistics(Base):
    __tablename__ = "image_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    mean_intensity = Column(Float)
    std_intensity = Column(Float)
    min_intensity = Column(Float)
    max_intensity = Column(Float)
    median_intensity = Column(Float)
    snr = Column(Float)
    contrast = Column(Float)
    histogram_json = Column(JSONB)
    # Image data (base64 encoded)
    main_image_data = Column(Text)  # Main DICOM image as base64
    histogram_image_data = Column(Text)  # Histogram as base64
    windowed_image_data = Column(Text)  # Windowed image as base64
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    study = relationship("Study", back_populates="image_statistics")

class PlatformMetrics(Base):
    __tablename__ = "platform_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_date = Column(Date, unique=True)
    total_patients = Column(Integer)
    total_studies = Column(Integer)
    total_analyses = Column(Integer)
    ai_analyses_count = Column(Integer)
    diagnostic_analyses_count = Column(Integer)
    avg_processing_time = Column(Float)
    metrics_json = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

