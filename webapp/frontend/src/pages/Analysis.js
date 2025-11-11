import React, { useState, useEffect } from 'react';
import { BarChart3, Activity, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { apiService } from '../api';

function Analysis() {
  const [protocolAnalysis, setProtocolAnalysis] = useState(null);
  const [biasAnalysis, setBiasAnalysis] = useState(null);
  const [cohortStats, setCohortStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalysisData();
  }, []);

  const loadAnalysisData = async () => {
    try {
      setLoading(true);
      const [protocolRes, biasRes, cohortRes] = await Promise.all([
        apiService.getProtocolAnalysis(),
        apiService.getBiasAnalysis(),
        apiService.getCohortStatistics(),
      ]);
      
      setProtocolAnalysis(protocolRes.data);
      setBiasAnalysis(biasRes.data);
      setCohortStats(cohortRes.data);
    } catch (error) {
      console.error('Error loading analysis:', error);
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
        <h1>Technical Analysis</h1>
        <p>Protocol standardization, bias assessment, and quality metrics</p>
      </div>

      {/* Protocol Analysis Summary */}
      {protocolAnalysis && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-header">
                <span className="stat-label">Total Protocols</span>
                <Activity size={24} className="stat-icon" />
              </div>
              <div className="stat-value">{protocolAnalysis.summary.total_protocols}</div>
              <div className="stat-description">Imaging protocols analyzed</div>
            </div>

            <div className="stat-card warning">
              <div className="stat-header">
                <span className="stat-label">Drift Detected</span>
                <AlertTriangle size={24} className="stat-icon" style={{color: '#f59e0b'}} />
              </div>
              <div className="stat-value">{protocolAnalysis.summary.drift_detected}</div>
              <div className="stat-description">Protocol variations found</div>
            </div>

            <div className="stat-card success">
              <div className="stat-header">
                <span className="stat-label">Standardization</span>
                <CheckCircle size={24} className="stat-icon" style={{color: '#10b981'}} />
              </div>
              <div className="stat-value">
                {(protocolAnalysis.summary.avg_standardization_score * 100).toFixed(0)}%
              </div>
              <div className="stat-description">Average standardization score</div>
            </div>
          </div>

          {/* Manufacturer Distribution */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Manufacturer Distribution</h2>
              <BarChart3 size={24} color="var(--primary-color)" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={protocolAnalysis.manufacturer_distribution}>
                <XAxis dataKey="manufacturer" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* Bias Analysis */}
      {biasAnalysis && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Bias & Generalizability Assessment</h2>
            {biasAnalysis.bias_risk_level === 'LOW' ? (
              <CheckCircle size={24} color="#10b981" />
            ) : (
              <AlertTriangle size={24} color="#f59e0b" />
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
            <div>
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Risk Level</p>
                <span className={`badge ${
                  biasAnalysis.bias_risk_level === 'LOW' ? 'success' :
                  biasAnalysis.bias_risk_level === 'MEDIUM' ? 'warning' : 'danger'
                }`}>
                  {biasAnalysis.bias_risk_level}
                </span>
              </div>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Bias Score</p>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--gray-900)' }}>
                  {(biasAnalysis.bias_score * 100).toFixed(1)}%
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Dataset Size</p>
                <p style={{ fontWeight: 600 }}>
                  {biasAnalysis.total_patients} patients<br />
                  {biasAnalysis.total_studies} studies
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>Diversity Metrics</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-700)', marginBottom: '0.25rem' }}>
                  Manufacturer: {(biasAnalysis.manufacturer_diversity * 100).toFixed(0)}%
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-700)' }}>
                  Protocol: {(biasAnalysis.protocol_diversity * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            <div>
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.5rem' }}>
                  Assessment
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', lineHeight: 1.6 }}>
                  {biasAnalysis.bias_risk_level === 'LOW' 
                    ? 'The dataset demonstrates good diversity across manufacturers, protocols, and acquisition parameters. The risk of scanner-specific bias is minimal.'
                    : biasAnalysis.bias_risk_level === 'MEDIUM'
                    ? 'The dataset shows moderate diversity. Consider expanding data collection to include more varied scanner types and protocols to improve generalizability.'
                    : 'The dataset has limited diversity. High risk of overfitting to specific scanner configurations. Urgent need for more diverse data collection.'}
                </p>
              </div>

              {biasAnalysis.recommendations && (
                <div style={{
                  padding: '1rem',
                  background: '#fef3c7',
                  borderRadius: '0.5rem',
                  borderLeft: '4px solid #f59e0b'
                }}>
                  <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#92400e', marginBottom: '0.5rem' }}>
                    Recommendations
                  </p>
                  <p style={{ fontSize: '0.875rem', color: '#92400e', lineHeight: 1.6 }}>
                    {biasAnalysis.recommendations}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cohort Statistics */}
      {cohortStats && cohortStats.body_part_distribution && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Body Part Distribution</h2>
            <TrendingUp size={24} color="var(--success-color)" />
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Body Part</th>
                  <th>Count</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {cohortStats.body_part_distribution.map((item, index) => {
                  const total = cohortStats.body_part_distribution.reduce((sum, i) => sum + i.count, 0);
                  const percentage = ((item.count / total) * 100).toFixed(1);
                  
                  return (
                    <tr key={index}>
                      <td style={{ fontWeight: 600 }}>{item.body_part}</td>
                      <td>{item.count}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                          <div style={{
                            flex: 1,
                            height: '8px',
                            background: 'var(--gray-200)',
                            borderRadius: '4px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${percentage}%`,
                              height: '100%',
                              background: 'var(--primary-color)'
                            }} />
                          </div>
                          <span style={{ minWidth: '50px', textAlign: 'right' }}>{percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Analysis;

