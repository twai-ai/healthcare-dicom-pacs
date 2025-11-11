import React, { useState, useEffect } from 'react';
import { Users, Activity, Brain, BarChart3, AlertTriangle, CheckCircle } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { apiService } from '../api';

function Dashboard() {
  const [platformInfo, setPlatformInfo] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [cohortStats, setCohortStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [infoRes, statsRes, cohortRes] = await Promise.all([
        apiService.getInfo(),
        apiService.getStatisticsOverview(),
        apiService.getCohortStatistics(),
      ]);
      
      setPlatformInfo(infoRes.data);
      setStatistics(statsRes.data);
      setCohortStats(cohortRes.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !platformInfo) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  const { overview, bias_status } = platformInfo;
  
  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div>
      <div className="page-header">
        <h1>Platform Dashboard</h1>
        <p>AI-Powered Medical Imaging Analysis Platform</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Total Patients</span>
            <Users size={24} className="stat-icon" />
          </div>
          <div className="stat-value">{overview.total_patients}</div>
          <div className="stat-description">Active in the system</div>
        </div>

        <div className="stat-card success">
          <div className="stat-header">
            <span className="stat-label">Total Studies</span>
            <Activity size={24} className="stat-icon" style={{color: '#10b981'}} />
          </div>
          <div className="stat-value">{overview.total_studies}</div>
          <div className="stat-description">DICOM studies analyzed</div>
        </div>

        <div className="stat-card warning">
          <div className="stat-header">
            <span className="stat-label">AI Analyses</span>
            <Brain size={24} className="stat-icon" style={{color: '#f59e0b'}} />
          </div>
          <div className="stat-value">{overview.total_ai_analyses}</div>
          <div className="stat-description">Multi-model AI assessments</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Diagnostic Analyses</span>
            <BarChart3 size={24} className="stat-icon" style={{color: '#3b82f6'}} />
          </div>
          <div className="stat-value">{overview.total_diagnostic_analyses}</div>
          <div className="stat-description">Data-driven assessments</div>
        </div>
      </div>

      {/* Bias Status */}
      {bias_status && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Bias Analysis Status</h2>
            {bias_status.risk_level === 'LOW' ? (
              <CheckCircle size={24} color="#10b981" />
            ) : (
              <AlertTriangle size={24} color="#f59e0b" />
            )}
          </div>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: '1rem' }}>
                <span className={`badge ${bias_status.risk_level === 'LOW' ? 'success' : bias_status.risk_level === 'MEDIUM' ? 'warning' : 'danger'}`}>
                  {bias_status.risk_level} RISK
                </span>
              </div>
              <p style={{ color: 'var(--gray-600)', marginBottom: '1rem' }}>
                Bias Score: {(bias_status.bias_score * 100).toFixed(1)}%
              </p>
              <p style={{ color: 'var(--gray-600)' }}>
                {bias_status.risk_level === 'LOW' 
                  ? 'The dataset shows good diversity across manufacturers and protocols.'
                  : 'Consider expanding the dataset to improve diversity and reduce bias.'}
              </p>
            </div>
            <div style={{ width: '120px', height: '120px' }}>
              <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%' }}>
                <path
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke={bias_status.risk_level === 'LOW' ? '#10b981' : bias_status.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444'}
                  strokeWidth="3"
                  strokeDasharray={`${(1 - bias_status.bias_score) * 100}, 100`}
                />
                <text x="18" y="20.35" style={{ fontSize: '0.5em', fill: 'var(--gray-700)', textAnchor: 'middle' }}>
                  {(1 - bias_status.bias_score).toFixed(2)}
                </text>
              </svg>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '1.5rem' }}>
        {/* Modality Distribution */}
        {cohortStats && cohortStats.modality_distribution && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Modality Distribution</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={cohortStats.modality_distribution}
                  dataKey="count"
                  nameKey="modality"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label
                >
                  {cohortStats.modality_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Diagnostic Score Distribution */}
        {statistics && statistics.diagnostic_summary && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">COVID-19 Probability Distribution</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { name: 'Low', value: statistics.diagnostic_summary.score_distribution.low, fill: '#10b981' },
                { name: 'Moderate', value: statistics.diagnostic_summary.score_distribution.moderate, fill: '#f59e0b' },
                { name: 'High', value: statistics.diagnostic_summary.score_distribution.high, fill: '#ef4444' },
              ]}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Platform Features */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h2 className="card-title">Platform Capabilities</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {platformInfo.platform_features.map((feature, index) => (
            <div key={index} style={{
              padding: '1rem',
              background: 'var(--gray-50)',
              borderRadius: '0.5rem',
              borderLeft: '4px solid var(--primary-color)'
            }}>
              <CheckCircle size={20} color="#10b981" style={{ marginBottom: '0.5rem' }} />
              <p style={{ color: 'var(--gray-700)', fontWeight: 500 }}>{feature}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

