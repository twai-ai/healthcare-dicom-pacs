import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, Activity, Brain, FileText, AlertCircle, CheckCircle, Download, Image as ImageIcon, BarChart2 } from 'lucide-react';
import { apiService } from '../api';
import AIAnalysisDisplay from '../components/AIAnalysisDisplay';

function PatientDetail() {
  const { patientId } = useParams();
  const [patientData, setPatientData] = useState(null);
  const [studyDetails, setStudyDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const handleExportPDF = async () => {
    try {
      window.open(`http://localhost:8000/api/export/pdf/${patientId}`, '_blank');
    } catch (error) {
      console.error('Error exporting PDF:', error);
    }
  };

  useEffect(() => {
    loadPatientData();
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      setLoading(true);
      const patientRes = await apiService.getPatient(patientId);
      setPatientData(patientRes.data);
      
      // Load study details to get images
      if (patientRes.data.studies && patientRes.data.studies.length > 0) {
        const studyId = patientRes.data.studies[0].id;
        const studyRes = await apiService.getStudy(studyId);
        setStudyDetails(studyRes.data);
        console.log('Study details loaded:', studyRes.data);
      }
    } catch (error) {
      console.error('Error loading patient:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !patientData) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  const { patient, studies, ai_analyses, diagnostic_analysis } = patientData;

  return (
    <div>
      <Link to="/patients" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--primary-color)', textDecoration: 'none' }}>
        <ArrowLeft size={16} />
        Back to Patients
      </Link>

      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1>Patient Details</h1>
            <p>{patient.patient_id}</p>
          </div>
          <button onClick={handleExportPDF} className="btn btn-primary">
            <Download size={18} />
            Export PDF Report
          </button>
        </div>
      </div>

      {/* Patient Info */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Patient Information</h2>
          <User size={24} color="var(--primary-color)" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Patient ID</p>
            <p style={{ fontWeight: 600, fontFamily: 'monospace' }}>{patient.patient_id}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Name</p>
            <p style={{ fontWeight: 600 }}>{patient.patient_name || 'N/A'}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Age</p>
            <p style={{ fontWeight: 600 }}>{patient.patient_age ? `${patient.patient_age} years` : 'N/A'}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.25rem' }}>Sex</p>
            <p style={{ fontWeight: 600 }}>{patient.patient_sex || 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Medical Images & Visualizations */}
      {studyDetails && studyDetails.image_statistics && (studyDetails.image_statistics.main_image_data || studyDetails.image_statistics.histogram_image_data) && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Medical Images & Visualizations</h2>
            <ImageIcon size={24} color="var(--primary-color)" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Main DICOM Image */}
            {studyDetails.image_statistics.main_image_data && (
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--gray-800)' }}>
                  <ImageIcon size={18} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
                  DICOM Image
                </h3>
                <img 
                  src={studyDetails.image_statistics.main_image_data} 
                  alt="DICOM Image" 
                  style={{ 
                    width: '100%', 
                    borderRadius: '0.5rem', 
                    border: '2px solid var(--gray-200)',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }} 
                />
              </div>
            )}
            
            {/* Histogram */}
            {studyDetails.image_statistics.histogram_image_data && (
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--gray-800)' }}>
                  <BarChart2 size={18} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
                  Pixel Intensity Distribution
                </h3>
                <img 
                  src={studyDetails.image_statistics.histogram_image_data} 
                  alt="Histogram" 
                  style={{ 
                    width: '100%', 
                    borderRadius: '0.5rem', 
                    border: '2px solid var(--gray-200)',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }} 
                />
                <div style={{ marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--gray-600)' }}>
                  <p>Mean: {studyDetails.image_statistics.mean_intensity?.toFixed(1)}</p>
                  <p>Std Dev: {studyDetails.image_statistics.std_intensity?.toFixed(1)}</p>
                  <p>Range: {studyDetails.image_statistics.min_intensity?.toFixed(0)} - {studyDetails.image_statistics.max_intensity?.toFixed(0)}</p>
                  <p>SNR: {studyDetails.image_statistics.snr?.toFixed(2)}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Diagnostic Analysis */}
      {diagnostic_analysis && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Diagnostic Assessment</h2>
            <FileText size={24} color="var(--warning-color)" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
            <div>
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>COVID-19 Score</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--primary-color)' }}>
                    {diagnostic_analysis.covid_score}/5
                  </div>
                  <span className={`badge ${
                    diagnostic_analysis.covid_score <= 2 ? 'success' :
                    diagnostic_analysis.covid_score === 3 ? 'warning' : 'danger'
                  }`}>
                    {diagnostic_analysis.covid_probability}
                  </span>
                </div>
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Severity</p>
                <p style={{ fontWeight: 600 }}>{diagnostic_analysis.severity || 'N/A'}</p>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Confidence</p>
                <span className="badge info">{diagnostic_analysis.confidence}</span>
              </div>
            </div>
            <div>
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.5rem' }}>Clinical Reasoning</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', lineHeight: 1.6 }}>
                  {diagnostic_analysis.clinical_reasoning || 'N/A'}
                </p>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.5rem' }}>Recommendations</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', lineHeight: 1.6 }}>
                  {diagnostic_analysis.recommendations || 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Analyses - Formatted */}
      {ai_analyses.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">AI Analysis Results - Multi-Model Radiology Reports</h2>
            <Brain size={24} color="var(--primary-color)" />
          </div>
          <p style={{ marginBottom: '1.5rem', color: 'var(--gray-600)', fontSize: '0.9375rem' }}>
            Comprehensive analysis from {ai_analyses.length} AI model{ai_analyses.length > 1 ? 's' : ''} providing independent clinical assessments
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {ai_analyses.map((analysis, index) => (
              <AIAnalysisDisplay key={index} analysis={analysis} />
            ))}
          </div>
        </div>
      )}

      {/* Studies */}
      {studies.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Medical Studies</h2>
            <Activity size={24} color="var(--success-color)" />
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Study Date</th>
                  <th>Modality</th>
                  <th>Body Part</th>
                  <th>Manufacturer</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {studies.map((study, index) => (
                  <tr key={index}>
                    <td>{study.study_date ? new Date(study.study_date).toLocaleDateString() : 'N/A'}</td>
                    <td><span className="badge info">{study.modality}</span></td>
                    <td>{study.body_part || 'N/A'}</td>
                    <td>{study.manufacturer || 'N/A'}</td>
                    <td>{study.study_description || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default PatientDetail;

