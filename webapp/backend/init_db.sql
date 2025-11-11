-- DICOM AI Platform Database Schema
-- PostgreSQL initialization script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) UNIQUE NOT NULL,
    patient_name VARCHAR(255),
    patient_age INTEGER,
    patient_sex VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Studies table
CREATE TABLE IF NOT EXISTS studies (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES patients(patient_id),
    study_instance_uid VARCHAR(255) UNIQUE NOT NULL,
    study_date DATE,
    study_description TEXT,
    modality VARCHAR(50),
    body_part VARCHAR(100),
    institution_name VARCHAR(255),
    manufacturer VARCHAR(255),
    manufacturer_model VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DICOM Metadata table
CREATE TABLE IF NOT EXISTS dicom_metadata (
    id SERIAL PRIMARY KEY,
    study_id INTEGER REFERENCES studies(id),
    series_instance_uid VARCHAR(255),
    sop_instance_uid VARCHAR(255) UNIQUE,
    image_path TEXT,
    slice_thickness FLOAT,
    pixel_spacing VARCHAR(50),
    rows INTEGER,
    columns INTEGER,
    window_center FLOAT,
    window_width FLOAT,
    kvp FLOAT,
    exposure_time FLOAT,
    protocol_name VARCHAR(255),
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Analysis Results table
CREATE TABLE IF NOT EXISTS ai_analysis (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES patients(patient_id),
    study_id INTEGER REFERENCES studies(id),
    model_name VARCHAR(100),
    analysis_type VARCHAR(50),
    findings TEXT,
    confidence_score FLOAT,
    covid_probability FLOAT,
    severity_assessment VARCHAR(50),
    recommendations TEXT,
    analysis_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnostic Analysis Results table
CREATE TABLE IF NOT EXISTS diagnostic_analysis (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES patients(patient_id),
    study_id INTEGER REFERENCES studies(id),
    covid_score INTEGER,
    covid_probability VARCHAR(50),
    severity VARCHAR(50),
    confidence VARCHAR(50),
    opacity_features JSONB,
    distribution_features JSONB,
    quantitative_features JSONB,
    clinical_reasoning TEXT,
    differential_diagnosis TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Protocol Analysis table
CREATE TABLE IF NOT EXISTS protocol_analysis (
    id SERIAL PRIMARY KEY,
    study_id INTEGER REFERENCES studies(id),
    protocol_name VARCHAR(255),
    manufacturer VARCHAR(255),
    model_name VARCHAR(255),
    slice_thickness FLOAT,
    pixel_spacing VARCHAR(50),
    kvp FLOAT,
    standardization_score FLOAT,
    drift_detected BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bias Analysis table
CREATE TABLE IF NOT EXISTS bias_analysis (
    id SERIAL PRIMARY KEY,
    analysis_date DATE,
    total_patients INTEGER,
    total_studies INTEGER,
    manufacturer_diversity FLOAT,
    protocol_diversity FLOAT,
    bias_risk_level VARCHAR(50),
    bias_score FLOAT,
    recommendations TEXT,
    metrics_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Metrics table
CREATE TABLE IF NOT EXISTS quality_metrics (
    id SERIAL PRIMARY KEY,
    study_id INTEGER REFERENCES studies(id),
    has_required_tags BOOLEAN,
    has_pixel_data BOOLEAN,
    standardized_orientation BOOLEAN,
    consistent_spacing BOOLEAN,
    compliance_score FLOAT,
    issues_found TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Image Statistics table
CREATE TABLE IF NOT EXISTS image_statistics (
    id SERIAL PRIMARY KEY,
    study_id INTEGER REFERENCES studies(id),
    mean_intensity FLOAT,
    std_intensity FLOAT,
    min_intensity FLOAT,
    max_intensity FLOAT,
    median_intensity FLOAT,
    snr FLOAT,
    contrast FLOAT,
    histogram_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platform Metrics table (for dashboard)
CREATE TABLE IF NOT EXISTS platform_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE UNIQUE,
    total_patients INTEGER,
    total_studies INTEGER,
    total_analyses INTEGER,
    ai_analyses_count INTEGER,
    diagnostic_analyses_count INTEGER,
    avg_processing_time FLOAT,
    metrics_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_patient_id ON patients(patient_id);
CREATE INDEX IF NOT EXISTS idx_studies_patient_id ON studies(patient_id);
CREATE INDEX IF NOT EXISTS idx_studies_modality ON studies(modality);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_patient_id ON ai_analysis(patient_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_model ON ai_analysis(model_name);
CREATE INDEX IF NOT EXISTS idx_diagnostic_patient_id ON diagnostic_analysis(patient_id);
CREATE INDEX IF NOT EXISTS idx_dicom_metadata_study_id ON dicom_metadata(study_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to patients table
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial platform metrics
INSERT INTO platform_metrics (metric_date, total_patients, total_studies, total_analyses, ai_analyses_count, diagnostic_analyses_count, avg_processing_time)
VALUES (CURRENT_DATE, 0, 0, 0, 0, 0, 0.0)
ON CONFLICT (metric_date) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'DICOM-AI Database initialized successfully!';
    RAISE NOTICE 'Schema version: 1.0';
    RAISE NOTICE 'Tables created: 11';
END $$;

