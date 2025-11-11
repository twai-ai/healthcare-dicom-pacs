import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, Calendar, Activity } from 'lucide-react';
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
        <p>View all patients and their medical imaging data</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Patient List</h2>
          <span className="badge info">{patients.length} Total</span>
        </div>

        {patients.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--gray-500)' }}>
            <User size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
            <p>No patients found</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Run the data ingestion script to populate the database
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Patient ID</th>
                  <th>Name</th>
                  <th>Age</th>
                  <th>Sex</th>
                  <th>Date Added</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {patients.map(patient => (
                  <tr key={patient.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <User size={16} color="var(--gray-400)" />
                        <span style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {patient.patient_id}
                        </span>
                      </div>
                    </td>
                    <td>{patient.patient_name || 'N/A'}</td>
                    <td>{patient.patient_age ? `${patient.patient_age}Y` : 'N/A'}</td>
                    <td>
                      <span className="badge info">{patient.patient_sex || 'N/A'}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Calendar size={14} color="var(--gray-400)" />
                        <span style={{ fontSize: '0.875rem' }}>
                          {new Date(patient.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </td>
                    <td>
                      <Link 
                        to={`/patients/${patient.patient_id}`}
                        className="btn btn-primary"
                        style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
                      >
                        <Activity size={14} />
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Patients;

