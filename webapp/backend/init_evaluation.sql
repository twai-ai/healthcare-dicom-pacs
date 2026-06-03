-- Evaluation layer extensions (ATRISI DICOM-AI)
ALTER TABLE diagnostic_analysis
    ADD COLUMN IF NOT EXISTS findings_json JSONB,
    ADD COLUMN IF NOT EXISTS engine_version VARCHAR(32);

CREATE TABLE IF NOT EXISTS evaluation_datasets (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(255),
    version VARCHAR(32),
    source VARCHAR(64),
    task VARCHAR(128),
    stats_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ground_truth_labels (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(128) NOT NULL,
    study_instance_uid VARCHAR(255) NOT NULL,
    patient_id VARCHAR(255),
    pattern_score_gt INTEGER,
    pattern_label_gt VARCHAR(64),
    severity_gt VARCHAR(128),
    covid_label VARCHAR(64),
    reader_id VARCHAR(128),
    source VARCHAR(64),
    provenance_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, study_instance_uid, reader_id)
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(64) UNIQUE NOT NULL,
    dataset_id VARCHAR(128),
    engine_version VARCHAR(32),
    output_path TEXT,
    metrics_json JSONB,
    git_commit VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ground_truth_dataset ON ground_truth_labels(dataset_id);
CREATE INDEX IF NOT EXISTS idx_ground_truth_study ON ground_truth_labels(study_instance_uid);
