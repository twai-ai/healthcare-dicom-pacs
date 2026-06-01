import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, Activity, Brain, FileText, Download } from 'lucide-react';
import { apiService } from '../api';
import AIAnalysisDisplay from '../components/AIAnalysisDisplay';
import ScanViewer from '../components/ScanViewer';

function PatientDetail() {
  const { patientId } = useParams();
  const [patientData, setPatientData] = useState(null);
  const [loading, setLoading] = useState(true);

  const handleExportPDF = () => {
    window.open(`/api/export/pdf/${patientId}`, '_blank');
  };

  useEffect(() => {
    loadPatientData();
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      setLoading(true);
      const patientRes = await apiService.getPatient(patientId);
      setPatientData(patientRes.data);
    } catch (error) {
      console.error('Error loading patient:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !patientData) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  const { patient, studies, ai_analyses, diagnostic_analysis, image_statistics } = patientData;
  const primaryStudy = studies?.[0];
  const scanTitle = primaryStudy
    ? `${primaryStudy.modality || 'X-Ray'} — ${primaryStudy.study_description || 'Chest scan'}`
    : 'Chest X-Ray Scan';

  return (
    <div>
      <Link to="/patients" className="back-link">
        <ArrowLeft size={16} />
        Back to Patients
      </Link>

      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Patient Details</h1>
            <p>{patient.patient_id}</p>
          </div>
          <button onClick={handleExportPDF} className="btn btn-primary" type="button">
            <Download size={18} />
            Export PDF Report
          </button>
        </div>
      </div>

      {/* Scan viewer — primary position at top */}
      <div className="card scan-card">
        <div className="card-header">
          <h2 className="card-title">Medical Imaging Scan</h2>
          {primaryStudy && (
            <span className="badge info">{primaryStudy.modality}</span>
          )}
        </div>
        <ScanViewer
          imageStatistics={image_statistics}
          title={scanTitle}
        />
      </div>

      {/* Patient demographics */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Patient Information</h2>
          <User size={24} color="var(--primary-color)" />
        </div>
        <div className="patient-info-grid">
          <div>
            <p className="field-label">Patient ID</p>
            <p className="field-value field-value--mono">{patient.patient_id}</p>
          </div>
          <div>
            <p className="field-label">Name</p>
            <p className="field-value">{patient.patient_name || 'N/A'}</p>
          </div>
          <div>
            <p className="field-label">Age</p>
            <p className="field-value">{patient.patient_age ? `${patient.patient_age} years` : 'N/A'}</p>
          </div>
          <div>
            <p className="field-label">Sex</p>
            <p className="field-value">{patient.patient_sex || 'N/A'}</p>
          </div>
        </div>
      </div>

      {diagnostic_analysis && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Diagnostic Assessment</h2>
            <FileText size={24} color="var(--warning-color)" />
          </div>
          <div className="diagnostic-grid">
            <div>
              <p className="field-label">COVID-19 Score</p>
              <div className="covid-score-row">
                <div className="covid-score-value">
                  {diagnostic_analysis.covid_score}/5
                </div>
                <span className={`badge ${
                  diagnostic_analysis.covid_score <= 2 ? 'success' :
                  diagnostic_analysis.covid_score === 3 ? 'warning' : 'danger'
                }`}>
                  {diagnostic_analysis.covid_probability}
                </span>
              </div>
              <p className="field-label" style={{ marginTop: '1rem' }}>Severity</p>
              <p className="field-value">{diagnostic_analysis.severity || 'N/A'}</p>
              <p className="field-label" style={{ marginTop: '1rem' }}>Confidence</p>
              <span className="badge info">{diagnostic_analysis.confidence}</span>
            </div>
            <div>
              <p className="field-label">Clinical Reasoning</p>
              <p className="field-text">{diagnostic_analysis.clinical_reasoning || 'N/A'}</p>
              <p className="field-label" style={{ marginTop: '1rem' }}>Recommendations</p>
              <p className="field-text">{diagnostic_analysis.recommendations || 'N/A'}</p>
            </div>
          </div>
        </div>
      )}

      {ai_analyses.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">AI Analysis Results</h2>
            <Brain size={24} color="var(--primary-color)" />
          </div>
          <p className="card-intro">
            Analysis from {ai_analyses.length} model{ai_analyses.length > 1 ? 's' : ''}
          </p>
          <div className="ai-analysis-list">
            {ai_analyses.map((analysis, index) => (
              <AIAnalysisDisplay key={index} analysis={analysis} />
            ))}
          </div>
        </div>
      )}

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
                {studies.map((study) => (
                  <tr key={study.id}>
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
