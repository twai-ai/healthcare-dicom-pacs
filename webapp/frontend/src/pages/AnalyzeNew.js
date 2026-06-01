import React, { useState } from 'react';
import { Upload, FileText, Brain, Activity, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { apiService } from '../api';
import axios from 'axios';
import AIAnalysisDisplay from '../components/AIAnalysisDisplay';

function AnalyzeNew() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [engineStatus, setEngineStatus] = useState(null);

  React.useEffect(() => {
    loadEngineStatus();
  }, []);

  const loadEngineStatus = async () => {
    try {
      const response = await axios.get('/api/analysis/status');
      setEngineStatus(response.data);
    } catch (error) {
      console.error('Error loading engine status:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.name.endsWith('.dcm')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please select a DICOM file (.dcm)');
        setSelectedFile(null);
      }
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) return;

    setAnalyzing(true);
    setError(null);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(
        '/api/analysis/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Upload & Analyze</h1>
        <p>Upload DICOM files for real-time AI-powered analysis</p>
      </div>

      {/* Engine Status */}
      {engineStatus && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <h2 className="card-title">Analysis Engine Status</h2>
            <CheckCircle size={24} color="#10b981" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Status</p>
              <span className="badge success">{engineStatus.status}</span>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>DICOM Processing</p>
              <span className="badge success">✓ Ready</span>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Gemini AI</p>
              <span className={`badge ${engineStatus.capabilities.gemini_ai ? 'success' : 'warning'}`}>
                {engineStatus.capabilities.gemini_ai ? '✓ Enabled' : '○ Disabled'}
              </span>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Groq AI</p>
              <span className={`badge ${engineStatus.capabilities.groq_ai ? 'success' : 'warning'}`}>
                {engineStatus.capabilities.groq_ai ? '✓ Enabled' : '○ Disabled'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Upload Section */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Upload DICOM File</h2>
          <Upload size={24} color="var(--primary-color)" />
        </div>

        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <input
            type="file"
            accept=".dcm"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            id="file-input"
          />
          <label
            htmlFor="file-input"
            style={{
              display: 'inline-block',
              padding: '3rem',
              border: '2px dashed var(--gray-300)',
              borderRadius: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
              width: '100%',
              maxWidth: '600px',
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--primary-color)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--gray-300)'}
          >
            <Upload size={48} color="var(--gray-400)" style={{ marginBottom: '1rem' }} />
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.5rem' }}>
              Click to upload DICOM file
            </p>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-500)' }}>
              or drag and drop
            </p>
          </label>

          {selectedFile && (
            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'var(--gray-50)',
              borderRadius: '0.5rem',
              display: 'inline-block'
            }}>
              <FileText size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
              <span style={{ fontWeight: 600 }}>{selectedFile.name}</span>
              <span style={{ marginLeft: '1rem', color: 'var(--gray-500)', fontSize: '0.875rem' }}>
                ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
          )}

          {error && (
            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              background: '#fee2e2',
              borderRadius: '0.5rem',
              color: '#991b1b',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              justifyContent: 'center'
            }}>
              <AlertCircle size={20} />
              {error}
            </div>
          )}

          {selectedFile && !analyzing && (
            <button
              onClick={handleUploadAndAnalyze}
              className="btn btn-primary"
              style={{ marginTop: '1.5rem', padding: '1rem 2rem', fontSize: '1rem' }}
            >
              <Brain size={20} style={{ marginRight: '0.5rem' }} />
              Analyze with AI
            </button>
          )}

          {analyzing && (
            <div style={{ marginTop: '2rem' }}>
              <Loader size={48} color="var(--primary-color)" style={{ animation: 'spin 1s linear infinite' }} />
              <p style={{ marginTop: '1rem', color: 'var(--gray-600)' }}>
                Analyzing with AI models... This may take 30-60 seconds
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {results && results.status === 'complete' && (
        <div>
          {/* Metadata */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Patient Information</h2>
              <Activity size={24} color="var(--success-color)" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>Patient ID</p>
                <p style={{ fontWeight: 600, fontFamily: 'monospace' }}>{results.metadata.patient_id}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>Age</p>
                <p style={{ fontWeight: 600 }}>{results.metadata.patient_age || 'N/A'}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>Sex</p>
                <p style={{ fontWeight: 600 }}>{results.metadata.patient_sex}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>Modality</p>
                <span className="badge info">{results.metadata.modality}</span>
              </div>
            </div>
          </div>

          {/* Diagnostic Analysis */}
          {results.diagnostic && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Data-Driven Diagnostic Assessment</h2>
                <CheckCircle size={24} color="var(--success-color)" />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                <div>
                  <div style={{ marginBottom: '1.5rem' }}>
                    <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>COVID-19 Score</p>
                    <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--primary-color)' }}>
                      {results.diagnostic.covid_score}/5
                    </div>
                    <span className={`badge ${
                      results.diagnostic.covid_score <= 2 ? 'success' : 
                      results.diagnostic.covid_score === 3 ? 'warning' : 'danger'
                    }`}>
                      {results.diagnostic.covid_probability}
                    </span>
                  </div>
                  <div>
                    <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Severity</p>
                    <p style={{ fontWeight: 600 }}>{results.diagnostic.severity}</p>
                  </div>
                  <div style={{ marginTop: '1rem' }}>
                    <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Confidence</p>
                    <span className="badge info">{results.diagnostic.confidence}</span>
                  </div>
                </div>
                <div>
                  <div style={{ marginBottom: '1.5rem' }}>
                    <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Clinical Reasoning</p>
                    <p style={{ color: 'var(--gray-700)', lineHeight: 1.6 }}>
                      {results.diagnostic.clinical_reasoning}
                    </p>
                  </div>
                  <div>
                    <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Recommendations</p>
                    <p style={{ color: 'var(--gray-700)', lineHeight: 1.6 }}>
                      {results.diagnostic.recommendations}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Analyses - Formatted */}
          {results.ai_analysis && results.ai_analysis.models && Object.keys(results.ai_analysis.models).length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">AI Analysis Results - Real-Time Radiology Reports</h2>
                <Brain size={24} color="var(--primary-color)" />
              </div>
              <p style={{ marginBottom: '1.5rem', color: 'var(--gray-600)', fontSize: '0.9375rem' }}>
                Fresh analysis from AI models - {Object.keys(results.ai_analysis.models).length} model{Object.keys(results.ai_analysis.models).length > 1 ? 's' : ''} analyzed this image
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {Object.entries(results.ai_analysis.models).map(([modelKey, modelResult], index) => (
                  <AIAnalysisDisplay 
                    key={index} 
                    analysis={{
                      model_name: modelResult.model || modelKey,
                      analysis_type: modelKey,
                      findings: modelResult.analysis || modelResult.error || 'No analysis available',
                      created_at: new Date().toISOString(),
                      severity_assessment: modelResult.severity,
                      recommendations: modelResult.recommendations
                    }} 
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* No AI Models Message */}
          {results.ai_analysis && results.ai_analysis.error && (
            <div style={{
              padding: '1.5rem',
              background: '#fef3c7',
              borderRadius: '0.75rem',
              borderLeft: '4px solid #f59e0b'
            }}>
              <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#92400e', marginBottom: '0.5rem' }}>
                AI Models Not Available
              </p>
              <p style={{ fontSize: '0.875rem', color: '#92400e' }}>
                {results.ai_analysis.error}. Data-driven diagnostic analysis was performed successfully.
              </p>
            </div>
          )}

          {/* Success Message */}
          <div style={{
            padding: '1.5rem',
            background: '#d1fae5',
            borderRadius: '0.75rem',
            borderLeft: '4px solid #10b981',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <CheckCircle size={24} color="#10b981" />
            <div>
              <p style={{ fontWeight: 600, color: '#065f46', marginBottom: '0.25rem' }}>
                Analysis Complete!
              </p>
              <p style={{ fontSize: '0.875rem', color: '#047857' }}>
                Results have been saved to the database. View in the Patients section.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnalyzeNew;

