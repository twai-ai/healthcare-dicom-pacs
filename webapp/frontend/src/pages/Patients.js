import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, Calendar, Activity, Image as ImageIcon } from 'lucide-react';
import { apiService } from '../api';

function Patients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPatients();
      setPatients(response.data);
    } catch (error) {
      console.error('Error loading patients:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1>Patients</h1>
        <p>View all patients and their chest imaging scans</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Patient List</h2>
          <span className="badge info">{patients.length} Total</span>
        </div>

        {patients.length === 0 ? (
          <div className="empty-state">
            <User size={48} />
            <p>No patients found</p>
            <p className="empty-state-hint">Run data ingestion to populate the database</p>
          </div>
        ) : (
          <div className="patient-card-grid">
            {patients.map((patient) => (
              <article key={patient.id} className="patient-card">
                <div className="patient-card-scan">
                  {patient.scan_thumbnail ? (
                    <img
                      src={patient.scan_thumbnail}
                      alt={`Scan for ${patient.patient_id}`}
                      className="patient-card-thumbnail"
                    />
                  ) : (
                    <div className="patient-card-scan-placeholder">
                      <ImageIcon size={32} />
                      <span>No preview</span>
                    </div>
                  )}
                  {patient.modality && (
                    <span className="patient-card-modality">{patient.modality}</span>
                  )}
                </div>
                <div className="patient-card-body">
                  <h3 className="patient-card-id">{patient.patient_id}</h3>
                  {patient.study_description && (
                    <p className="patient-card-study">{patient.study_description}</p>
                  )}
                  <div className="patient-card-meta">
                    <span>{patient.patient_age ? `${patient.patient_age}Y` : '—'}</span>
                    <span>{patient.patient_sex || '—'}</span>
                    {patient.covid_score != null && (
                      <span className={`badge ${
                        patient.covid_score <= 2 ? 'success' :
                        patient.covid_score === 3 ? 'warning' : 'danger'
                      }`}>
                        COVID {patient.covid_score}/5
                      </span>
                    )}
                  </div>
                  <div className="patient-card-footer">
                    <span className="patient-card-date">
                      <Calendar size={14} />
                      {new Date(patient.created_at).toLocaleDateString()}
                    </span>
                    <Link
                      to={`/patients/${patient.patient_id}`}
                      className="btn btn-primary btn-sm"
                    >
                      <Activity size={14} />
                      View scan & details
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Patients;
