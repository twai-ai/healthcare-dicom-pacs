import React from 'react';
import { Brain, Shield, Zap, Users, CheckCircle, Award } from 'lucide-react';

function About() {
  const features = [
    {
      icon: Brain,
      title: 'Multi-Model AI Analysis',
      description: 'Ensemble approach combining Google Gemini 2.0 Flash and Groq LLaMA 3.3 70B for robust diagnostic insights',
      color: '#2563eb'
    },
    {
      icon: Zap,
      title: 'Data-Driven Diagnostics',
      description: '24 quantitative imaging features with rule-based clinical reasoning for objective assessment',
      color: '#10b981'
    },
    {
      icon: Shield,
      title: 'Quality Assurance',
      description: 'Comprehensive DICOM validation, protocol standardization, and bias mitigation',
      color: '#f59e0b'
    },
    {
      icon: Users,
      title: 'Clinical Validation Ready',
      description: 'Doctor-friendly reports suitable for clinical review and regulatory submission',
      color: '#8b5cf6'
    }
  ];

  const achievements = [
    'Multi-model AI integration (Gemini + Groq)',
    'Triple-layer diagnostic validation',
    'Comprehensive bias assessment',
    'DICOM standardization pipeline',
    'Automated quality metrics',
    'Professional medical reports'
  ];

  const challenges = [
    {
      title: 'DICOM Metadata Under-utilization',
      solution: 'Advanced feature extraction from 50+ DICOM tags',
      status: 'solved'
    },
    {
      title: 'Interoperability & Standardization',
      solution: 'Automated validation and standardization pipeline',
      status: 'solved'
    },
    {
      title: 'Data De-identification / Privacy',
      solution: 'HIPAA-compliant de-identification module',
      status: 'solved'
    },
    {
      title: 'Workflow Integration',
      solution: 'REST API and modular architecture',
      status: 'solved'
    },
    {
      title: 'Data Volume & Infrastructure',
      solution: 'Scalable batch processing with PostgreSQL',
      status: 'solved'
    },
    {
      title: 'Bias & Generalizability',
      solution: 'Comprehensive bias assessment and stratified sampling',
      status: 'solved'
    }
  ];

  return (
    <div>
      <div className="page-header">
        <h1>About DICOM-AI Platform</h1>
        <p>Advanced medical imaging analysis powered by artificial intelligence</p>
      </div>

      {/* Hero Section */}
      <div style={{
        padding: '3rem',
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        borderRadius: '0.75rem',
        color: 'white',
        marginBottom: '2rem',
        textAlign: 'center'
      }}>
        <Brain size={64} style={{ marginBottom: '1rem' }} />
        <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>
          Next-Generation Medical Imaging AI
        </h2>
        <p style={{ fontSize: '1.125rem', opacity: 0.9, maxWidth: '800px', margin: '0 auto' }}>
          A comprehensive platform combining multi-model AI, data-driven diagnostics, and technical quality analysis 
          to deliver robust, validated medical imaging insights.
        </p>
      </div>

      {/* Core Features */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Core Features</h2>
          <Award size={24} color="var(--primary-color)" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} style={{
                padding: '1.5rem',
                background: 'var(--gray-50)',
                borderRadius: '0.75rem',
                borderTop: `4px solid ${feature.color}`
              }}>
                <Icon size={32} color={feature.color} style={{ marginBottom: '1rem' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--gray-900)', marginBottom: '0.5rem' }}>
                  {feature.title}
                </h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', lineHeight: 1.6 }}>
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Achievements */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Key Achievements</h2>
          <CheckCircle size={24} color="var(--success-color)" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          {achievements.map((achievement, index) => (
            <div key={index} style={{
              padding: '1rem',
              background: '#d1fae5',
              borderRadius: '0.5rem',
              borderLeft: '4px solid #10b981',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem'
            }}>
              <CheckCircle size={20} color="#10b981" style={{ flexShrink: 0 }} />
              <p style={{ fontSize: '0.875rem', color: '#065f46', fontWeight: 500 }}>
                {achievement}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Challenges Solved */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Medical Imaging AI Challenges Addressed</h2>
          <Shield size={24} color="var(--primary-color)" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {challenges.map((challenge, index) => (
            <div key={index} style={{
              padding: '1.5rem',
              background: 'white',
              borderRadius: '0.75rem',
              border: '2px solid var(--gray-200)',
              display: 'grid',
              gridTemplateColumns: '2fr 3fr auto',
              gap: '1.5rem',
              alignItems: 'center'
            }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--gray-900)', marginBottom: '0.25rem' }}>
                  {challenge.title}
                </h3>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>
                  {challenge.solution}
                </p>
              </div>
              <div>
                <span className="badge success">
                  <CheckCircle size={14} style={{ marginRight: '0.25rem' }} />
                  SOLVED
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Stack */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Technology Stack</h2>
          <Zap size={24} color="var(--warning-color)" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              AI Models
            </h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Google Gemini 2.0 Flash</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Groq LLaMA 3.3 70B</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Ensemble Consensus</li>
            </ul>
          </div>
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Backend
            </h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• FastAPI</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• PostgreSQL</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• SQLAlchemy ORM</li>
            </ul>
          </div>
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Frontend
            </h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• React 18</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Recharts</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Responsive Design</li>
            </ul>
          </div>
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Medical Imaging
            </h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• PyDICOM</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• NumPy / Pandas</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• TCIA API Integration</li>
            </ul>
          </div>
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-700)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Infrastructure
            </h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Docker / Docker Compose</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• Nginx</li>
              <li style={{ padding: '0.5rem 0', color: 'var(--gray-600)', fontSize: '0.875rem' }}>• RESTful API</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Version Info */}
      <div style={{
        padding: '2rem',
        background: 'var(--gray-50)',
        borderRadius: '0.75rem',
        textAlign: 'center'
      }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginBottom: '0.5rem' }}>
          DICOM-AI Platform
        </p>
        <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--gray-900)', marginBottom: '0.5rem' }}>
          Version 1.0.0
        </p>
        <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>
          Built for clinical validation and research collaboration
        </p>
      </div>
    </div>
  );
}

export default About;

