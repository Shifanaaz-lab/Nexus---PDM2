# AI-Based Predictive Maintenance System for Industrial Equipment

NEXUS is a full-stack predictive maintenance platform designed to monitor industrial assets and engine fleets through real-time telemetry analysis, machine learning-based Remaining Useful Life (RUL) prediction, failure risk assessment, and intelligent maintenance planning.

The system combines a Flask backend, React-based command center dashboard, MongoDB data storage, and XGBoost machine learning models to provide actionable maintenance insights and fleet-wide operational visibility.

The platform supports telemetry simulation, real-time monitoring, maintenance scheduling, analytics reporting, and predictive health assessment through an integrated web interface.

## Features

### Predictive Maintenance
- Remaining Useful Life (RUL) Prediction
- Failure Probability Estimation
- Engine Health Assessment
- Predictive Risk Classification

### Machine Learning
- XGBoost Regression Models
- Quantile-Based Uncertainty Prediction
- Advanced Feature Engineering
- Cross-Engine Validation
- Model Performance Evaluation

### Real-Time Monitoring
- Live Telemetry Simulation
- Fleet Health Tracking
- Engine Status Monitoring
- Dynamic Risk Assessment

### Alert Management
- Critical Risk Detection
- Automated Alert Generation
- Alert Acknowledgement Workflow
- Failure Warning System

### Maintenance Operations
- Maintenance Scheduling
- Maintenance History Tracking
- Automated Maintenance Recommendations
- Service Completion Monitoring

### Dashboard & Analytics
- Fleet Overview Dashboard
- Telemetry Visualization
- Analytics Reporting
- Performance Monitoring
- RUL Priority Queue

### Security & User Management
- User Registration
- Authentication System
- Session Management
- Role-Based User Access

### Data Management
- MongoDB Integration
- Prediction History Storage
- Engine State Persistence
- Analytics Data Collection

## System Architecture

Telemetry Simulator
        │
        ▼
Feature Engineering Pipeline
        │
        ▼
XGBoost Prediction Engine
        │
        ├── RUL Prediction
        ├── Risk Assessment
        └── Uncertainty Estimation
        │
        ▼
MongoDB Database
        │
        ▼
Flask REST API
        │
        ▼
AI-Based PDM Dashboard


## Technology Stack

### Frontend
- React
- Vite
- TypeScript
- Material UI
- Radix UI
- Recharts

### Backend
- Flask
- Flask-CORS
- Python

### Machine Learning
- XGBoost
- Scikit-Learn
- NumPy
- Pandas

### Database
- MongoDB

### Deployment
- Render
- GitHub

NEXUS-PDM/
│
├── frontend/
├── dataset/
├── models/
├── performance_results/
├── guidelines/
│
├── app.py
├── main.py
├── rul_dashboard.py
├── start_integrated_system.py
│
├── enhanced_feature_engineering.py
├── optimized_model_training.py
├── streaming_data_pipeline.py
├── cross_engine_model_trainer.py
├── model_performance_evaluator.py
├── model_evaluation_monitoring.py
│
├── evaluate.py
├── cross_validate.py
├── learning_curve.py
│
├── requirements.txt
├── render.yaml
├── Procfile
└── README.md

## Running the System

### Backend

```bash
python app.py

### Backend runs on :
```bash
 http://localhost:8001

### Frontend
cd frontend
npm install
npm run dev

Frontend runs on:
http://localhost:5173

Access Dashboard
http://localhost:5173


---

# API Endpoints

```markdown
## API Endpoints

### Telemetry & Monitoring
GET /api/telemetry

### Analytics
GET /api/analytics

### Engine Details
GET /api/engine/<engine_id>

### Maintenance
GET /api/maintenance_history
POST /api/schedule_maintenance

### Alerts
POST /api/acknowledge_alert
POST /api/clear_alert

### Authentication
POST /api/register
POST /api/login
POST /api/logout
POST /api/validate_session

### Health Check
GET /health

## Applications

- Industrial Equipment Monitoring
- Predictive Maintenance Systems
- Fleet Health Management
- Manufacturing Operations
- Reliability Engineering
- Condition-Based Maintenance
- Asset Performance Monitoring

## Future Enhancements

- IoT Device Integration
- Cloud Deployment
- Explainable AI (XAI)
- Deep Learning Prognostics
- Multi-Facility Fleet Monitoring
- Edge Computing Support
- Advanced Maintenance Optimization

## Author

Shifanaaz Abdulsab Nadaf
Computer Science Engineer
AI/ML • Predictive Maintenance • Software Development

