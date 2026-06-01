# Integrated Predictive Maintenance System

This document provides instructions for running the fully integrated frontend + backend predictive maintenance system.

## System Architecture

- **Backend**: Flask API server (`app.py`) serving telemetry data and predictions
- **Frontend**: Next.js dashboard with real-time data visualization
- **Database**: MongoDB for telemetry storage (optional - will work with mock data)
- **Integration**: CORS-enabled API communication between frontend and backend

## Prerequisites

### Python Dependencies
```bash
pip install flask flask-cors pymongo pandas plotly
```

### Node.js & npm
- Download and install Node.js from https://nodejs.org/
- Verify installation: `node --version` and `npm --version`

## Quick Start

### Option 1: Automated Startup (Windows)
```bash
# Run the batch script
start_system.bat
```

### Option 2: Manual Startup

#### Step 1: Start Backend Server
```bash
# In project root directory
python app.py
```
Backend will start on: `http://localhost:8001`

#### Step 2: Start Frontend Server
```bash
# In a new terminal, navigate to frontend directory
cd frontend
npm install
npm run dev
```
Frontend will start on: `http://localhost:5173`

#### Step 3: Access the Dashboard
Open your browser and go to: `http://localhost:5173`

## API Endpoints

### Main Dashboard Data
- **GET** `/api/telemetry` - Returns complete dashboard telemetry data
- **GET** `/api/maintenance_history` - Returns maintenance history

### Health Check
- **GET** `/health` - System health status

## Frontend Features

### Real-Time Dashboard
- **Fleet Status**: Active engines, critical warnings, system health
- **Engine Grid**: Visual overview of all engines with risk levels
- **Telemetry Charts**: Real-time sensor data visualization
- **RUL Priority Queue**: Engines ranked by remaining useful life
- **Alerts Panel**: System notifications and warnings
- **Analytics Summary**: Model performance and system metrics

### Integration Points
- **API Service**: `/frontend/src/services/api.ts` handles all backend communication
- **Real-time Updates**: Dashboard refreshes every 5 seconds
- **Error Handling**: Graceful fallback when backend is unavailable
- **Loading States**: Visual feedback during data fetching

## Backend Features

### Flask API Server
- **CORS Enabled**: Allows frontend to communicate from localhost:5173
- **MongoDB Integration**: Stores and retrieves telemetry data
- **Real-time Processing**: Live data aggregation and risk assessment
- **Mock Data Support**: Works without database using sample data

### Data Processing
- **Risk Assessment**: Calculates failure probabilities
- **RUL Prediction**: Remaining useful life estimates
- **Alert Generation**: Automatic warning system
- **Analytics**: Model performance metrics

## Configuration

### Environment Variables
```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=engine_telemetry

# Risk Thresholds
WARNING_THRESHOLD=0.5
HIGH_RISK_THRESHOLD=0.85

# Server Port
PORT=8001
```

### Frontend Configuration
```javascript
// In frontend/src/services/api.ts
const API_BASE_URL = 'http://localhost:8001'; // Backend URL
```

## Troubleshooting

### Backend Issues

#### Python not found
- Install Python from https://python.org/
- Add Python to PATH during installation

#### Missing dependencies
```bash
pip install flask flask-cors pymongo pandas plotly
```

#### MongoDB connection errors
- The system will work with mock data if MongoDB is not available
- To install MongoDB: https://www.mongodb.com/try/download/community

### Frontend Issues

#### Node.js not found
- Install Node.js from https://nodejs.org/
- Restart terminal after installation

#### npm install fails
```bash
# Clear npm cache
npm cache clean --force
# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json
# Try again
npm install
```

#### Port already in use
```bash
# Kill processes on ports 5173 and 8001
netstat -ano | findstr :5173
netstat -ano | findstr :8001
# Use taskkill to end the processes
```

### Integration Issues

#### CORS errors
- Ensure backend is running before starting frontend
- Check that backend allows requests from localhost:5173
- Verify both services are running on correct ports

#### Frontend can't reach backend
- Check backend is running on http://localhost:8001
- Try accessing http://localhost:8001/api/telemetry in browser
- Check browser console for network errors

## Development

### Running in Development Mode
```bash
# Backend (development with auto-reload)
export FLASK_ENV=development
python app.py

# Frontend (development with hot reload)
cd frontend
npm run dev
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build
npm start

# Backend production
python app.py  # Uses production settings
```

## File Structure

```
syn-dataset/
├── app.py                          # Flask backend server
├── start_system.bat                # Windows startup script
├── start_integrated_system.py      # Python startup script
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   │   └── api.ts             # API integration layer
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   └── IntegratedDashboard.tsx  # Main dashboard
│   │   │   └── routes.ts          # React Router configuration
│   │   └── main.tsx               # Frontend entry point
│   ├── package.json
│   └── next.config.ts
└── requirements.txt                # Python dependencies
```

## Next Steps

1. **Start the System**: Use `start_system.bat` or manual startup
2. **Access Dashboard**: Open http://localhost:5173
3. **Monitor Data**: Watch real-time telemetry and alerts
4. **Customize**: Modify thresholds and visualization as needed

## Support

If you encounter issues:
1. Check both backend and frontend are running
2. Verify ports 8001 and 5173 are available
3. Check browser console for JavaScript errors
4. Review backend terminal output for API errors

The system is designed to be robust and will work with mock data if the database is not available, making it easy to test and develop with.
