# DICOM-AI Web Application - Complete Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions for deploying the DICOM-AI web application, a comprehensive Single Page Application (SPA) for medical imaging analysis.

**Technology Stack:**
- **Frontend**: React 18, Recharts, Responsive Design
- **Backend**: FastAPI, Python 3.9
- **Database**: PostgreSQL 15
- **Infrastructure**: Docker, Docker Compose, Nginx

## 📋 Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows with WSL2
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 10GB+ free space
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### Install Docker

**macOS:**
```bash
brew install --cask docker
# Or download from https://www.docker.com/products/docker-desktop
```

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Windows:**
- Install WSL2
- Download Docker Desktop for Windows

## 🚀 Deployment Steps

### Step 1: Navigate to Project

```bash
cd /Users/aeishwary/DICOM-AI/webapp
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (optional for demo)
nano .env
```

**Minimal Configuration (Demo):**
```env
# No changes needed - works out of the box!
DATABASE_URL=postgresql://dicom_user:dicom_pass_2024@db:5432/dicom_ai
```

**Production Configuration:**
```env
# Change database password!
POSTGRES_PASSWORD=your_secure_password_here

# Add API keys (optional)
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### Step 3: Build Docker Images

```bash
# Build all services
docker-compose build

# Expected build time: 3-5 minutes
```

**Output:**
```
Building db...
Building backend...
Building frontend...
Successfully built!
```

### Step 4: Start All Services

```bash
# Start services in detached mode
docker-compose up -d

# Check status
docker-compose ps
```

**Expected Output:**
```
NAME                    STATUS              PORTS
dicom-ai-db             Up 30 seconds       0.0.0.0:5432->5432/tcp
dicom-ai-backend        Up 30 seconds       0.0.0.0:8000->8000/tcp
dicom-ai-frontend       Up 30 seconds       0.0.0.0:3000->80/tcp
```

### Step 5: Verify Services

```bash
# Check backend health
curl http://localhost:8000/

# Expected: {"status":"healthy","service":"DICOM-AI Platform API"...}

# Check frontend
curl http://localhost:3000/

# Expected: HTML content
```

### Step 6: Initialize Database

The database schema is automatically created on startup via `init_db.sql`.

Verify database:
```bash
docker-compose exec db psql -U dicom_user -d dicom_ai -c "\dt"
```

**Expected Output:**
```
List of relations
 Schema |         Name              | Type  |    Owner
--------+---------------------------+-------+-------------
 public | patients                  | table | dicom_user
 public | studies                   | table | dicom_user
 public | ai_analysis               | table | dicom_user
 public | diagnostic_analysis       | table | dicom_user
 ...
```

### Step 7: Ingest Analysis Data

```bash
# Enter backend container
docker-compose exec backend bash

# Run data ingestion
python ingest_data.py
```

**Expected Output:**
```
======================================================================
DICOM-AI DATA INGESTION
======================================================================

INGESTING PATIENTS AND STUDIES
======================================================================
✓ Loaded 2 records from metadata CSV
✓ Added 2 patients
✓ Added 2 studies

INGESTING AI ANALYSES
======================================================================
✓ Added 6 AI analyses

INGESTING DIAGNOSTIC ANALYSES
======================================================================
✓ Added 2 diagnostic analyses

...

✅ DATA INGESTION COMPLETE!
```

### Step 8: Access the Application

Open your browser to:

- **🌐 Frontend (Main App)**: http://localhost:3000
- **📚 API Documentation**: http://localhost:8000/api/docs
- **🔍 API ReDoc**: http://localhost:8000/api/redoc

## 🎨 Application Tour

### Dashboard (http://localhost:3000)
- Platform statistics (patients, studies, analyses)
- Bias analysis status
- Interactive charts (modality distribution, COVID-19 scores)
- Platform capabilities overview

### Patients (http://localhost:3000/patients)
- Complete patient list with demographics
- Quick search and filtering
- Click "View Details" for comprehensive patient analysis

### Patient Detail (http://localhost:3000/patients/[ID])
- Patient demographics
- COVID-19 diagnostic scoring (1-5 scale)
- Multi-model AI analysis (Gemini + Groq)
- Clinical recommendations
- Medical studies and DICOM metadata

### Analysis (http://localhost:3000/analysis)
- Protocol standardization metrics
- Bias & generalizability assessment
- Manufacturer distribution charts
- Body part distribution
- Technical recommendations

### Future Scope (http://localhost:3000/future-scope)
- Development roadmap (near-term & long-term)
- Research opportunities
- Technical enhancements
- Collaboration opportunities

### About (http://localhost:3000/about)
- Platform overview
- Core features
- Challenges solved
- Technology stack

## 🔍 Verification Checklist

### ✅ Backend Health
```bash
curl http://localhost:8000/api/info | jq
```

Should return:
- `total_patients: 2`
- `total_studies: 2`
- `total_ai_analyses: 6`
- `total_diagnostic_analyses: 2`

### ✅ Database Data
```bash
docker-compose exec db psql -U dicom_user -d dicom_ai -c "SELECT COUNT(*) FROM patients;"
```

Should return: `2`

### ✅ Frontend Access
Open http://localhost:3000 - should see:
- DICOM-AI Platform dashboard
- Statistics showing 2 patients
- Charts and visualizations

## 🛠️ Management Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services
```bash
# Stop all (preserves data)
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Re-ingest data if needed
docker-compose exec backend python ingest_data.py
```

## 🗄️ Database Management

### Access Database
```bash
docker-compose exec db psql -U dicom_user -d dicom_ai
```

### Useful Queries
```sql
-- View patients
SELECT * FROM patients;

-- View AI analyses
SELECT patient_id, model_name, findings 
FROM ai_analysis;

-- View diagnostic assessments
SELECT patient_id, covid_score, covid_probability, severity 
FROM diagnostic_analysis;

-- View bias analysis
SELECT * FROM bias_analysis 
ORDER BY created_at DESC LIMIT 1;
```

### Backup Database
```bash
docker-compose exec db pg_dump -U dicom_user dicom_ai > backup.sql
```

### Restore Database
```bash
docker-compose exec -T db psql -U dicom_user dicom_ai < backup.sql
```

## 📊 Adding Your Own Data

### Option 1: Use Existing Analysis Results

Place your analysis outputs in `/Users/aeishwary/DICOM-AI/test-code/output/`:
- `dicom_metadata.csv`
- `multi_model_gemini_analyses.json`
- `multi_model_groq_analyses.json`
- `diagnostic_analysis_results.json`
- `protocol_analysis.json`
- `bias_analysis.json`

Then re-run ingestion:
```bash
docker-compose exec backend python ingest_data.py
```

### Option 2: Direct Database Insert

```bash
docker-compose exec db psql -U dicom_user -d dicom_ai

INSERT INTO patients (patient_id, patient_age, patient_sex) 
VALUES ('NEW-PATIENT-001', 45, 'M');
```

## 🔒 Security for Production

### 1. Change Database Password
```yaml
# docker-compose.yml
environment:
  POSTGRES_PASSWORD: your_secure_password_here
```

### 2. Enable HTTPS
Add SSL certificates and update `nginx.conf`:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ...
}
```

### 3. Add Authentication
Implement JWT authentication in backend:
```python
# backend/main.py
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/patients", dependencies=[Depends(security)])
def get_patients():
    ...
```

### 4. Use Environment Secrets
Use AWS Secrets Manager, HashiCorp Vault, or similar.

## 🚀 Production Deployment Options

### Option 1: Single Server (DigitalOcean, AWS EC2)

```bash
# Install Docker on server
ssh user@your-server
curl -fsSL https://get.docker.com | sh

# Clone repository
git clone https://github.com/your-repo/DICOM-AI.git
cd DICOM-AI/webapp

# Configure environment
cp .env.example .env
nano .env  # Add production credentials

# Deploy
docker-compose up -d

# Setup automatic updates
# Use watchtower or similar
```

### Option 2: Kubernetes

Create Kubernetes manifests:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dicom-ai-backend
spec:
  replicas: 3
  ...
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Option 3: Cloud Platforms

- **AWS**: ECS, RDS, CloudFront
- **Google Cloud**: Cloud Run, Cloud SQL
- **Azure**: Container Instances, Azure Database

## 📈 Monitoring & Scaling

### Add Monitoring
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

### Scale Services
```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3

# Add load balancer
# Use nginx or HAProxy
```

## 🐛 Troubleshooting

### Issue: Port Already in Use
```bash
# Find process using port
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Kill process or change port in docker-compose.yml
```

### Issue: Database Connection Failed
```bash
# Check database status
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Issue: Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend
```

### Issue: No Data Showing
```bash
# Re-run data ingestion
docker-compose exec backend python ingest_data.py

# Verify data
docker-compose exec db psql -U dicom_user -d dicom_ai -c "SELECT COUNT(*) FROM patients;"
```

## ✅ Success Indicators

Your deployment is successful when:

- ✅ All 3 containers running (`docker-compose ps`)
- ✅ Frontend accessible at http://localhost:3000
- ✅ Backend API docs at http://localhost:8000/api/docs
- ✅ Dashboard shows 2+ patients with data
- ✅ Patient detail pages show AI analyses
- ✅ Charts and visualizations render correctly
- ✅ No errors in logs (`docker-compose logs`)

## 📞 Getting Help

### View Application Logs
```bash
docker-compose logs -f --tail=100
```

### Check Service Health
```bash
docker-compose ps
curl http://localhost:8000/
curl http://localhost:8000/api/info
```

### Access Container Shell
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
docker-compose exec db bash
```

## 🎉 You're Ready!

Your DICOM-AI platform is now deployed and ready for:
- ✅ Clinical validation
- ✅ Research demonstrations
- ✅ Investor presentations
- ✅ Development and testing

**Next Steps:**
1. Share http://localhost:3000 with stakeholders
2. Collect feedback on UI/UX
3. Validate AI analysis results
4. Plan production deployment

---

**Platform**: DICOM-AI Web Application  
**Version**: 1.0.0  
**Status**: Production-Ready  
**Support**: Review README.md for detailed documentation

