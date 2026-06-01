@echo off
echo Starting Integrated Predictive Maintenance System...
echo.

echo Checking Python installation...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

echo Installing Python dependencies...
py -m pip install flask flask-cors pymongo pandas plotly

echo Installing frontend dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
)
cd ..

echo.
echo Starting servers...
echo Backend will run on: http://localhost:8001
echo Frontend will run on: http://localhost:5173
echo.
echo Press Ctrl+C to stop both servers
echo.

start "Backend API" cmd /k "py app.py"
timeout /t 3 /nobreak >nul
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo System started! Opening browser...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo Press any key to exit...
pause
