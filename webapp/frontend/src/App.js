import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, Users, BarChart3, Brain, FileText, Target, Upload } from 'lucide-react';

// Import pages
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import PatientDetail from './pages/PatientDetail';
import Analysis from './pages/Analysis';
import AnalyzeNew from './pages/AnalyzeNew';
import FutureScope from './pages/FutureScope';
import About from './pages/About';

import './App.css';

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: Activity },
    { path: '/analyze', label: 'Upload & Analyze', icon: Upload },
    { path: '/patients', label: 'Patients', icon: Users },
    { path: '/analysis', label: 'Analysis', icon: BarChart3 },
    { path: '/future-scope', label: 'Future Scope', icon: Target },
    { path: '/about', label: 'About', icon: FileText },
  ];
  
  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <Brain size={32} className="logo-icon" />
        <div className="logo-text">
          <h1>DICOM-AI</h1>
          <p>Medical Imaging Platform</p>
        </div>
      </div>
      
      <div className="nav-links">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
      
      <div className="sidebar-footer">
        <div className="version-info">
          <p>Version 1.0.0</p>
          <p className="status">
            <span className="status-dot"></span>
            All Systems Operational
          </p>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze" element={<AnalyzeNew />} />
            <Route path="/patients" element={<Patients />} />
            <Route path="/patients/:patientId" element={<PatientDetail />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/future-scope" element={<FutureScope />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

