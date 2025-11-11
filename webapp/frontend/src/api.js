import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Platform info
  getInfo: () => api.get('/info'),
  
  // Patients
  getPatients: () => api.get('/patients'),
  getPatient: (patientId) => api.get(`/patients/${patientId}`),
  
  // Studies
  getStudies: (modality = null) => 
    api.get('/studies', { params: modality ? { modality } : {} }),
  getStudy: (studyId) => api.get(`/studies/${studyId}`),
  
  // AI Analysis
  getAIAnalyses: (modelName = null) => 
    api.get('/ai-analysis', { params: modelName ? { model_name: modelName } : {} }),
  getPatientAIAnalyses: (patientId) => api.get(`/ai-analysis/patient/${patientId}`),
  
  // Diagnostic Analysis
  getDiagnosticAnalyses: () => api.get('/diagnostic-analysis'),
  getPatientDiagnostic: (patientId) => api.get(`/diagnostic-analysis/patient/${patientId}`),
  
  // Protocol & Bias
  getProtocolAnalysis: () => api.get('/protocol-analysis'),
  getBiasAnalysis: () => api.get('/bias-analysis'),
  
  // Statistics
  getStatisticsOverview: () => api.get('/statistics/overview'),
  getCohortStatistics: () => api.get('/statistics/cohort'),
  
  // Future Scope
  getFutureScope: () => api.get('/future-scope'),
};

export default api;

