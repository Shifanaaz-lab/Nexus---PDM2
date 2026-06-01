# React + Flask Integration Guide

## Overview
Successfully integrated React frontend (Vite + TypeScript) with Flask backend for real-time predictive maintenance dashboard.

## Architecture

### Backend (Flask)
- **File**: `app.py`
- **Port**: 8001
- **API Endpoints**:
  - `GET /api/telemetry` - Returns engine data, alerts, charts
  - `GET /api/maintenance_history` - Returns maintenance logs
  - `GET /health` - Health check

### Frontend (React + Vite + TypeScript)
- **Port**: 5173
- **Framework**: Vite + React + TypeScript
- **UI Library**: Lucide React + Recharts

## Integration Components

### 1. API Service Layer (`/frontend/src/services/api.ts`)
```typescript
// Complete API service with TypeScript interfaces
export const apiService = new ApiService();
```

**Features**:
- ✅ Type-safe API calls
- ✅ Error handling
- ✅ Request/response interceptors
- ✅ Base URL configuration
- ✅ All backend endpoints covered

### 2. Custom Hook (`/frontend/src/hooks/useDashboardData.ts`)
```typescript
const { data, loading, error, refetch } = useDashboardData();
```

**Features**:
- ✅ Automatic data fetching
- ✅ Real-time updates (5-second interval)
- ✅ Loading states
- ✅ Error handling
- ✅ Manual refresh capability

### 3. Dashboard Component (`/frontend/src/app/components/DashboardWithAPI.tsx`)
```typescript
export function DashboardWithAPI()
```

**Features**:
- ✅ Real API data integration
- ✅ Loading spinner
- ✅ Error state with retry
- ✅ Real-time telemetry charts
- ✅ Fleet status cards
- ✅ Engine grid visualization
- ✅ RUL priority queue
- ✅ Alerts panel
- ✅ Analytics summary

## Data Flow

```
Flask Backend (app.py)
    ↓ /api/telemetry
React API Service (api.ts)
    ↓ useDashboardData hook
Dashboard Component (DashboardWithAPI.tsx)
    ↓ UI Rendering
User Interface
```

## Key Features Implemented

### 1. Proper API Service Layer
- **TypeScript interfaces** for all API responses
- **Error handling** with try-catch blocks
- **Base URL configuration** for environment flexibility
- **Request/response logging** for debugging

### 2. Data Fetching from /api/telemetry
- **Automatic polling** every 5 seconds
- **Manual refresh** capability
- **Graceful error handling** with retry options
- **Type-safe data handling**

### 3. Dashboard Data Display
- **Fleet Status Cards**: Active engines, critical/warning counts, health score
- **Real-time Telemetry**: Live sensor data charts (3 sensors)
- **Engine Grid**: 12-engine visual overview with risk levels
- **RUL Priority Queue**: Ranked engines by remaining useful life
- **Alerts Panel**: System notifications and warnings
- **Analytics Summary**: Model performance metrics

### 4. Loading + Error States
- **Loading spinner** during initial data fetch
- **Error screen** with retry button
- **Graceful degradation** when backend unavailable
- **Real-time loading indicators** on refresh

## File Structure

```
frontend/src/
├── services/
│   └── api.ts                    # API service layer
├── hooks/
│   └── useDashboardData.ts        # Custom data hook
├── app/
│   ├── components/
│   │   └── DashboardWithAPI.tsx   # Main dashboard component
│   └── routes.ts                  # React Router configuration
└── main.tsx                       # App entry point
```

## API Response Structure

### /api/telemetry Response
```typescript
interface DashboardResponse {
  status: string;
  fleet: {
    active_engines: number;
    critical_count: number;
    warning_count: number;
    total_risk_count: number;
    mean_rul: number;
  };
  alerts: string[];
  engine_grid: Array<{
    id: string;
    rul: number;
    risk: number;
  }>;
  rul_bars: Array<{
    id: string;
    rul: number;
    risk: number;
  }>;
  telemetry_lines: {
    timestamps: string[];
    s1: number[];
    s2: number[];
    s3: number[];
  };
  worst_engine: {
    id: number;
    risk: number;
  };
  analytics_summary: {
    avg_risk: number;
    health_score: number;
    model_precision: number;
    drift_status: string;
  };
  maintenance: {
    immediate: {
      id: string;
      reason: string;
    };
    upcoming: Array<{
      id: string;
      task: string;
      date: string;
    }>;
  };
}
```

## Usage Instructions

### 1. Start Backend
```bash
cd e:\ROBOTICS\syn-dataset
py app.py
```

### 2. Start Frontend
```bash
cd e:\ROBOTICS\syn-dataset\frontend
npm run dev
```

### 3. Access Dashboard
Open: `http://localhost:5173/dashboard`

## Key Improvements

### Before Integration
- ❌ Mock data only
- ❌ No real-time updates
- ❌ Static UI components
- ❌ No error handling

### After Integration
- ✅ Real API data from Flask backend
- ✅ Real-time updates every 5 seconds
- ✅ Dynamic UI based on live data
- ✅ Comprehensive error handling
- ✅ Loading states and retry mechanisms
- ✅ Type-safe data handling
- ✅ Responsive design with live charts

## Technical Details

### CORS Configuration
Backend configured to allow requests from:
- `http://localhost:5173`
- `http://127.0.0.1:5173`

### Error Handling
- **Network errors**: Graceful retry with user feedback
- **API errors**: Clear error messages and retry options
- **Loading states**: Visual feedback during data fetching
- **Fallback data**: System works even when backend temporarily unavailable

### Performance Optimizations
- **Debounced API calls**: Prevent excessive requests
- **Component memoization**: Efficient re-rendering
- **Chart optimization**: Smooth animations with disabled animation for real-time data
- **Memory management**: Proper cleanup of intervals and event listeners

## Testing

### Manual Testing Checklist
- [ ] Backend API returns data
- [ ] Frontend displays real data
- [ ] Loading states work correctly
- [ ] Error states show retry option
- [ ] Real-time updates every 5 seconds
- [ ] Manual refresh button works
- [ ] Charts update with new data
- [ ] Fleet status cards show correct counts
- [ ] Engine grid displays risk levels
- [ ] Alerts panel shows system notifications

### API Testing
```bash
# Test backend API
curl http://localhost:8001/api/telemetry
curl http://localhost:8001/api/maintenance_history
curl http://localhost:8001/health
```

## Next Steps

1. **Enhanced Error Handling**: Add more specific error types and recovery strategies
2. **Data Caching**: Implement local storage for offline functionality
3. **WebSocket Integration**: Replace polling with real-time WebSocket updates
4. **Authentication**: Add user authentication and authorization
5. **Data Export**: Add CSV/PDF export functionality for reports
6. **Mobile Responsive**: Optimize for mobile devices
7. **Performance Monitoring**: Add performance metrics and monitoring

## Troubleshooting

### Common Issues
1. **CORS errors**: Ensure backend allows frontend origin
2. **Connection refused**: Check if backend is running on port 8001
3. **Type errors**: Verify TypeScript interfaces match API responses
4. **Missing data**: Check backend logs for MongoDB connection issues

### Debug Tips
- Check browser console for JavaScript errors
- Check Network tab for failed API requests
- Check backend terminal for Flask errors
- Verify API response structure matches TypeScript interfaces
