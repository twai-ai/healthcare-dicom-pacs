# DICOM-AI Web Application

A comprehensive Single Page Application (SPA) for medical imaging analysis powered by AI, featuring a FastAPI backend, React frontend, and PostgreSQL database.

## 🏗️ Architecture

```
webapp/
├── docker-compose.yml          # Orchestrates all services
├── backend/                    # FastAPI backend
│   ├── Dockerfile
│   ├── main.py                 # API endpoints
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # Database configuration
│   ├── init_db.sql             # Database schema
│   ├── ingest_data.py          # Data population script
│   └── requirements.txt
└── frontend/                   # React SPA
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── public/
    └── src/
        ├── App.js
        ├── api.js              # API client
        └── pages/              # React pages
            ├── Dashboard.js
            ├── Patients.js
            ├── PatientDetail.js
            ├── Analysis.js
            ├── FutureScope.js
            └── About.js
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 4GB+ RAM
- 10GB+ disk space

### Step 1: Environment Setup

Create `.env` file in `webapp/` directory:

```bash
# API Keys (optional for demo)
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Database
DATABASE_URL=postgresql://dicom_user:dicom_pass_2024@db:5432/dicom_ai
```

### Step 2: Build and Start Services

```bash
cd /Users/aeishwary/DICOM-AI/webapp

# Build all services
docker-compose build

# Start all services
docker-compose up -d
```

This will start:
- **Frontend** (React SPA): http://localhost:3000
- **Backend** (FastAPI): http://localhost:8000
- **Backend API Docs**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5432

### Step 3: Initialize Database

The database schema is automatically created on first startup via `init_db.sql`.

### Step 4: Ingest Existing Analysis Data

```bash
# Enter backend container
docker-compose exec backend bash

# Run data ingestion
python ingest_data.py
```

This will populate the database with:
- Patient information
- DICOM metadata
- AI analysis results (Gemini + Groq)
- Diagnostic assessments
- Protocol & bias analysis
- Quality metrics

### Step 5: Access the Application

Open your browser to **http://localhost:3000**

## 📊 Application Features

### Dashboard
- Platform overview statistics
- Bias analysis status
- Modality distribution charts
- COVID-19 probability distribution
- Real-time metrics

### Patients
- Complete patient list
- Patient demographics
- Quick search and filtering
- Detailed patient views

### Patient Detail
- Patient information
- Diagnostic assessments (COVID-19 scoring)
- Multi-model AI analysis results (Gemini + Groq)
- Medical studies and DICOM metadata
- Clinical recommendations

### Analysis
- Protocol standardization analysis
- Bias & generalizability assessment
- Manufacturer distribution
- Body part distribution
- Quality metrics
- Technical recommendations

### Future Scope
- Development roadmap (near-term & long-term)
- Research opportunities
- Technical enhancements
- Collaboration opportunities

### About
- Platform capabilities
- Core features
- Challenges addressed
- Technology stack
- Version information

## 🔧 Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# View logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend
```

**Backend Structure:**
- `main.py`: FastAPI app with all endpoints
- `models.py`: SQLAlchemy ORM models
- `schemas.py`: Pydantic validation schemas
- `database.py`: Database connection
- `ingest_data.py`: Data ingestion script

### Frontend Development

```bash
# Enter frontend container (during development)
cd frontend
npm start

# Or rebuild frontend container
docker-compose up -d --build frontend
```

**Frontend Structure:**
- `App.js`: Main app with routing
- `api.js`: Axios API client
- `pages/`: React page components
- Responsive design with modern CSS

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U dicom_user -d dicom_ai

# View tables
\dt

# Query data
SELECT * FROM patients;
SELECT * FROM ai_analysis;
SELECT * FROM diagnostic_analysis;
```

## 📡 API Endpoints

### Platform Info
- `GET /`: Health check
- `GET /api/info`: Platform overview

### Patients
- `GET /api/patients`: List all patients
- `GET /api/patients/{patient_id}`: Get patient details

### Studies
- `GET /api/studies`: List all studies
- `GET /api/studies/{study_id}`: Get study details

### AI Analysis
- `GET /api/ai-analysis`: List AI analyses
- `GET /api/ai-analysis/patient/{patient_id}`: Get patient AI analyses

### Diagnostic Analysis
- `GET /api/diagnostic-analysis`: List diagnostic analyses
- `GET /api/diagnostic-analysis/patient/{patient_id}`: Get patient diagnostic analysis

### Quality & Protocol
- `GET /api/protocol-analysis`: Protocol analysis summary
- `GET /api/bias-analysis`: Bias assessment

### Statistics
- `GET /api/statistics/overview`: Platform statistics
- `GET /api/statistics/cohort`: Cohort-level statistics

### Future Scope
- `GET /api/future-scope`: Development roadmap

Full API documentation: http://localhost:8000/api/docs

## 🗄️ Database Schema

### Main Tables
- `patients`: Patient information
- `studies`: Medical imaging studies
- `dicom_metadata`: DICOM file metadata
- `ai_analysis`: AI model results (Gemini + Groq)
- `diagnostic_analysis`: Data-driven diagnostic assessments
- `protocol_analysis`: Protocol standardization metrics
- `bias_analysis`: Bias & generalizability assessment
- `quality_metrics`: DICOM validation results
- `image_statistics`: Image quality statistics
- `platform_metrics`: Platform usage metrics

## 🛠️ Troubleshooting

### Container Issues

```bash
# View all container status
docker-compose ps

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart db

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Check database connection
docker-compose exec backend python -c "from database import engine; print(engine.url)"
```

### Data Issues

```bash
# Re-run data ingestion
docker-compose exec backend python ingest_data.py

# Check ingested data
docker-compose exec db psql -U dicom_user -d dicom_ai -c "SELECT COUNT(*) FROM patients;"
```

## 📦 Production Deployment

### Security Considerations

1. **Change Default Passwords**
   ```yaml
   POSTGRES_PASSWORD: your_secure_password
   POSTGRES_USER: your_secure_user
   ```

2. **Use Environment Variables**
   - Never commit `.env` file
   - Use secrets management (AWS Secrets Manager, Vault)

3. **Enable HTTPS**
   - Add SSL certificates
   - Configure Nginx for HTTPS

4. **Add Authentication**
   - Implement JWT authentication
   - Add user roles and permissions

### Scaling

- Use **PostgreSQL replication** for high availability
- Add **Redis** for caching
- Use **load balancer** for multiple frontend instances
- Deploy on **Kubernetes** for orchestration

### Monitoring

- Add **Prometheus** for metrics
- Use **Grafana** for dashboards
- Implement **logging aggregation** (ELK stack)
- Set up **alerts** for system health

## 🎯 Use Cases

### Clinical Validation
- Share with radiologists for validation
- Collect feedback on AI analyses
- Compare against expert reads
- Validate diagnostic scoring system

### Research
- Demonstrate platform capabilities
- Collect cohort statistics
- Analyze protocol variations
- Study bias and generalizability

### Investor Demos
- Showcase AI-powered analysis
- Highlight technical capabilities
- Present development roadmap
- Show scalability potential

### IRB/Ethics Review
- Document methodology
- Show compliance features
- Demonstrate de-identification
- Present quality assurance

## 📝 Notes

- **No Authentication**: This is a demo platform. Add authentication for production use.
- **Sample Data**: The platform works with analyzed data from existing analysis pipeline.
- **API Keys**: Gemini and Groq API keys are optional - data can be ingested from previous analyses.
- **Performance**: Designed for 10-1000 patients. Scale infrastructure for larger datasets.

## 🤝 Contributing

This platform is built for validation and collaboration. For suggestions or improvements:

1. Test the platform with your data
2. Validate AI analysis results
3. Provide clinical feedback
4. Suggest additional features

## 📄 License

Built for medical research and clinical validation purposes.

## 📞 Support

For questions about deployment or usage:
- Review API documentation: http://localhost:8000/api/docs
- Check logs: `docker-compose logs -f`
- Verify database: `docker-compose exec db psql -U dicom_user -d dicom_ai`

---

**Version**: 1.0.0  
**Status**: Production-Ready  
**Last Updated**: November 2024

