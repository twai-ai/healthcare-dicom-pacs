import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, Calendar, AlertCircle, Rocket, Users, Brain } from 'lucide-react';
import { apiService } from '../api';

function FutureScope() {
  const [futureScope, setFutureScope] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFutureScope();
  }, []);

  const loadFutureScope = async () => {
    try {
      setLoading(true);
      const response = await apiService.getFutureScope();
      setFutureScope(response.data);
    } catch (error) {
      console.error('Error loading future scope:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !futureScope) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  const priorityColors = {
    'HIGH': { bg: '#fef2f2', border: '#ef4444', text: '#991b1b' },
    'MEDIUM': { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
    'LOW': { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
  };

  return (
    <div>
      <div className="page-header">
        <h1>Future Scope & Roadmap</h1>
        <p>Platform development plan and research opportunities</p>
      </div>

      {/* Near Term Goals */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Near-Term Development (1-6 Months)</h2>
          <Rocket size={24} color="var(--primary-color)" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {futureScope.near_term.map((item, index) => (
            <div key={index} style={{
              padding: '1.5rem',
              background: priorityColors[item.priority].bg,
              borderRadius: '0.75rem',
              borderLeft: `4px solid ${priorityColors[item.priority].border}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'start', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--gray-900)', marginBottom: '0.5rem' }}>
                  {item.title}
                </h3>
                <span className={`badge ${item.priority === 'HIGH' ? 'danger' : item.priority === 'MEDIUM' ? 'warning' : 'info'}`}>
                  {item.priority}
                </span>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', lineHeight: 1.6, marginBottom: '1rem' }}>
                {item.description}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: priorityColors[item.priority].text }}>
                <Calendar size={14} />
                <span>{item.timeline}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Long Term Goals */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Long-Term Vision (6-24 Months)</h2>
          <Target size={24} color="var(--success-color)" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {futureScope.long_term.map((item, index) => (
            <div key={index} style={{
              padding: '1.5rem',
              background: 'white',
              borderRadius: '0.75rem',
              border: '2px solid var(--gray-200)',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--primary-color)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--gray-200)'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--gray-900)' }}>
                  {item.title}
                </h3>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span className={`badge ${item.priority === 'HIGH' ? 'danger' : item.priority === 'MEDIUM' ? 'warning' : 'info'}`}>
                    {item.priority}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--gray-600)' }}>
                    <Calendar size={14} />
                    <span>{item.timeline}</span>
                  </div>
                </div>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', lineHeight: 1.6 }}>
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Research Opportunities */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Research Opportunities</h2>
          <Brain size={24} color="var(--primary-color)" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          {futureScope.research_opportunities.map((opportunity, index) => (
            <div key={index} style={{
              padding: '1rem',
              background: 'var(--gray-50)',
              borderRadius: '0.5rem',
              display: 'flex',
              alignItems: 'start',
              gap: '0.75rem'
            }}>
              <TrendingUp size={20} color="var(--primary-color)" style={{ flexShrink: 0, marginTop: '0.125rem' }} />
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-700)', lineHeight: 1.6 }}>
                {opportunity}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Enhancements */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Technical Enhancements</h2>
          <Users size={24} color="var(--success-color)" />
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          {futureScope.technical_enhancements.map((enhancement, index) => (
            <div key={index} style={{
              padding: '0.625rem 1rem',
              background: 'white',
              border: '2px solid var(--primary-color)',
              borderRadius: '9999px',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: 'var(--primary-color)'
            }}>
              {enhancement}
            </div>
          ))}
        </div>
      </div>

      {/* Call to Action */}
      <div style={{
        padding: '2rem',
        background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
        borderRadius: '0.75rem',
        color: 'white',
        textAlign: 'center'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>
          Ready to Collaborate?
        </h2>
        <p style={{ fontSize: '1rem', opacity: 0.9, marginBottom: '1.5rem' }}>
          This platform is ready for clinical validation, research partnerships, and commercial deployment.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <div style={{
            padding: '1rem 1.5rem',
            background: 'white',
            borderRadius: '0.5rem',
            color: 'var(--primary-color)',
            fontWeight: 600
          }}>
            Clinical Validation Partners
          </div>
          <div style={{
            padding: '1rem 1.5rem',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '0.5rem',
            fontWeight: 600
          }}>
            Research Collaborators
          </div>
          <div style={{
            padding: '1rem 1.5rem',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '0.5rem',
            fontWeight: 600
          }}>
            Industry Partners
          </div>
        </div>
      </div>
    </div>
  );
}

export default FutureScope;

