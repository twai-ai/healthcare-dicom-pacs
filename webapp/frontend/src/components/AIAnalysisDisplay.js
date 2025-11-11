import React from 'react';
import { Brain, CheckCircle, AlertCircle, FileText } from 'lucide-react';

function AIAnalysisDisplay({ analysis }) {
  /**
   * Clean markdown formatting from text - COMPREHENSIVE
   */
  const cleanMarkdown = (text) => {
    if (!text) return '';
    
    return text
      // Remove bold markdown (**text**)
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*\*\s*/g, '')
      .replace(/\s*\*\*/g, '')
      // Remove single asterisks (*text*)
      .replace(/\*([^*\n]+)\*/g, '$1')
      // Remove remaining standalone asterisks
      .replace(/\*/g, '')
      // Remove underscores (_text_)
      .replace(/_([^_]+)_/g, '$1')
      .replace(/_/g, '')
      // Remove backticks (`code`)
      .replace(/`([^`]+)`/g, '$1')
      .replace(/`/g, '')
      // Remove markdown headers (###)
      .replace(/#{1,6}\s*/g, '')
      // Remove HTML tags if any
      .replace(/<[^>]+>/g, '')
      // Clean multiple spaces
      .replace(/\s+/g, ' ')
      // Clean multiple newlines
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      .trim();
  };

  /**
   * Parse and format AI analysis text into structured sections
   */
  const parseAnalysis = (text) => {
    if (!text) return { raw: 'No analysis available' };
    
    // Clean markdown first
    const cleanedText = text.replace(/\*\*/g, '');
    
    const sections = {};
    
    // Split by numbered sections or headers
    const lines = cleanedText.split('\n');
    let currentSection = 'summary';
    let currentContent = [];
    
    for (const line of lines) {
      // Check for section headers (e.g., "1. TECHNIQUE & QUALITY", "TECHNIQUE & QUALITY:")
      const sectionMatch = line.match(/^(\d+\.?\s*)?([A-Z][A-Z\s&]+):?\s*$/);
      
      if (sectionMatch && line.length < 100) {
        // Save previous section
        if (currentContent.length > 0) {
          sections[currentSection] = currentContent.join('\n').trim();
        }
        
        // Start new section
        const sectionName = (sectionMatch[2] || sectionMatch[1] || line).trim().toLowerCase();
        currentSection = sectionName.replace(/[^a-z\s]/g, '').replace(/\s+/g, '_');
        currentContent = [];
      } else if (line.trim()) {
        currentContent.push(cleanMarkdown(line));
      }
    }
    
    // Save last section
    if (currentContent.length > 0) {
      sections[currentSection] = currentContent.join('\n').trim();
    }
    
    // If no sections found, return cleaned raw text
    if (Object.keys(sections).length === 0) {
      sections.raw = cleanMarkdown(text);
    }
    
    return sections;
  };

  const sections = parseAnalysis(analysis.findings);
  
  const sectionTitles = {
    'technique_quality': { title: 'Technique & Quality', icon: FileText, color: '#2563eb' },
    'findings': { title: 'Findings', icon: AlertCircle, color: '#f59e0b' },
    'covid_assessment': { title: 'COVID-19 Assessment', icon: Brain, color: '#ef4444' },
    'covid19_assessment': { title: 'COVID-19 Assessment', icon: Brain, color: '#ef4444' },
    'impression': { title: 'Impression', icon: CheckCircle, color: '#10b981' },
    'recommendations': { title: 'Recommendations', icon: CheckCircle, color: '#8b5cf6' },
    'consensus_findings': { title: 'Consensus Findings', icon: CheckCircle, color: '#10b981' },
    'confidence_assessment': { title: 'Confidence Assessment', icon: Brain, color: '#2563eb' },
    'clinical_impression': { title: 'Clinical Impression', icon: FileText, color: '#10b981' },
  };

  return (
    <div style={{
      padding: '1.5rem',
      background: 'white',
      borderRadius: '0.75rem',
      border: '2px solid var(--gray-200)',
      marginBottom: '1rem'
    }}>
      {/* Model Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        paddingBottom: '1rem',
        borderBottom: '2px solid var(--gray-200)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Brain size={24} color="var(--primary-color)" />
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--gray-900)', marginBottom: '0.25rem' }}>
              {analysis.model_name}
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)' }}>
              {analysis.analysis_type === 'ensemble' ? 'Multi-Model Consensus' : 'AI Vision Analysis'}
            </p>
          </div>
        </div>
        <span className="badge success">
          {new Date(analysis.created_at).toLocaleDateString()}
        </span>
      </div>

      {/* Parsed Sections */}
      {Object.keys(sections).length > 1 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {Object.entries(sections).map(([key, content]) => {
            const sectionInfo = sectionTitles[key];
            
            if (!sectionInfo) {
              return null; // Skip unknown sections
            }
            
            const Icon = sectionInfo.icon;
            
            return (
              <div key={key}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '0.75rem'
                }}>
                  <Icon size={18} color={sectionInfo.color} />
                  <h4 style={{
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: sectionInfo.color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    {sectionInfo.title}
                  </h4>
                </div>
                <div style={{
                  paddingLeft: '1.75rem',
                  color: 'var(--gray-700)',
                  lineHeight: 1.8,
                  fontSize: '0.9375rem'
                }}>
                  {content.split('\n').map((line, idx) => {
                    // Clean the line
                    const cleanedLine = cleanMarkdown(line);
                    
                    if (!cleanedLine.trim()) return null;
                    
                    // Format bullet points
                    if (cleanedLine.trim().startsWith('•') || cleanedLine.trim().startsWith('-') || cleanedLine.trim().match(/^\s*\*/)) {
                      return (
                        <div key={idx} style={{
                          display: 'flex',
                          gap: '0.5rem',
                          marginBottom: '0.5rem',
                          paddingLeft: '1rem'
                        }}>
                          <span style={{ color: sectionInfo.color, fontWeight: 600 }}>•</span>
                          <span>{cleanedLine.replace(/^[•\-*]\s*/, '').trim()}</span>
                        </div>
                      );
                    }
                    
                    // Format sub-headers (but not URLs)
                    if (cleanedLine.includes(':') && cleanedLine.length < 100 && !cleanedLine.includes('http') && !cleanedLine.includes('www')) {
                      const colonIndex = cleanedLine.indexOf(':');
                      const label = cleanedLine.substring(0, colonIndex);
                      const value = cleanedLine.substring(colonIndex + 1);
                      
                      return (
                        <div key={idx} style={{ marginBottom: '0.5rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--gray-800)' }}>{label}:</span>
                          <span style={{ marginLeft: '0.5rem' }}>{value.trim()}</span>
                        </div>
                      );
                    }
                    
                    // Regular paragraph
                    return (
                      <p key={idx} style={{ marginBottom: '0.75rem' }}>
                        {cleanedLine}
                      </p>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        // Fallback: Display cleaned text with basic formatting
        <div style={{
          color: 'var(--gray-700)',
          lineHeight: 1.8,
          fontSize: '0.9375rem',
          whiteSpace: 'pre-wrap',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
          {cleanMarkdown(sections.raw || analysis.findings || '')}
        </div>
      )}

      {/* Severity & Recommendations at bottom */}
      {(analysis.severity_assessment || analysis.recommendations) && (
        <div style={{
          marginTop: '1.5rem',
          paddingTop: '1.5rem',
          borderTop: '2px solid var(--gray-200)',
          display: 'grid',
          gridTemplateColumns: analysis.recommendations ? '1fr 2fr' : '1fr',
          gap: '1.5rem'
        }}>
          {analysis.severity_assessment && (
            <div>
              <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-600)', marginBottom: '0.5rem' }}>
                Severity Assessment
              </p>
              <span className={`badge ${
                analysis.severity_assessment.toLowerCase().includes('severe') ? 'danger' :
                analysis.severity_assessment.toLowerCase().includes('moderate') ? 'warning' : 'info'
              }`}>
                {analysis.severity_assessment}
              </span>
            </div>
          )}
          
          {analysis.recommendations && (
            <div>
              <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--gray-600)', marginBottom: '0.5rem' }}>
                Recommendations
              </p>
              <p style={{ color: 'var(--gray-700)', lineHeight: 1.6 }}>
                {analysis.recommendations}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AIAnalysisDisplay;

