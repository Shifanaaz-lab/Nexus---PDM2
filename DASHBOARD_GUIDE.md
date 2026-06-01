# NEXUS Command Center: Operational Guide

This document provides the operational reference for the NEXUS Industrial Aero-Tech Command Center.

## System Architecture
- **Backend**: Flask engine on **Port 8001** (Cloud-ready).
- **Data Source**: MongoDB Atlas `live_predictions` collection.
- **Interface**: Spatially-stable asset grid with **10Hz (0.1s)** telemetry sync.

## High-Fidelity Features
### 1. Ultra-Low Latency Sync (0.1s)
The system is factory-tuned to poll MongoDB every **100 milliseconds**. This provides a smooth, "always-on" visual experience that matches real-world aero-telemetry stream rates. Operators can adjust this via the **Settings** tab if network bandwidth is limited.

The **Risk Alerts** KPI and the **Alerts Tab** are perfectly synchronized. Any engine with a `failure_probability` > 0.5 is logged as a WARNING, and > 0.85 as CRITICAL.

### 2. Intelligent Maintenance Schedule
- **Immediate Attention**: Dynamically selects the engine with the **highest absolute risk** at any given moment.
- **Upcoming Overhauls**: Proactively identifies engines with the **lowest Remaining Useful Life (RUL)** across the rest of the fleet.
- **Unique Selection**: Engines are filtered to ensure the "Immediate" engine does not duplicate in the "Upcoming" list, providing higher fleet visibility.

### 3. Spatial Anchor Asset Grid (HCI)
The primary monitor shows engines E-001 through E-012 in a **Fixed Position Grid**. This allows for "eyes-free" monitoring once the operator is familiar with engine placement.

### 4. Critical Signal Pulsing
Engines with >0.85 risk probability will visually "pulse" on the dashboard. This is an intentional design choice to break human visual adaptations (preventing operators from ignoring "static" red flags).

## Configuration
The system respects the following environment variables:
- `MONGODB_URI`: Connection string for the telemetry data.
- `WARNING_THRESHOLD`: Default `0.5`, determines when an engine turns yellow/warning.
- `HIGH_RISK_THRESHOLD`: Default `0.85`, determines when an engine turns red/critical.

## Getting Started
1. Start the MongoDB service.
2. Run `python real_time_engine_telemetry.py` to begin the data stream.
3. Run `python app.py` to start the command center API.
4. Access the UI at **[http://localhost:8001](http://localhost:8001)**.

## Cloud Deployment (Render.com)
1. Push this project to a **GitHub Repository**.
2. Create a "Blueprint" on **[Render.com](https://render.com)** and connect your repo.
3. Configure the `MONGODB_URI` environment variable with your **MongoDB Atlas** connection string.
4. Your shareable link will be generated automatically!

### Connecting your Local Simulator
Once your app is live, you can send data to it from your local machine by running:
```powershell
$env:MONGODB_URI="your_atlas_connection_string"; python real_time_engine_telemetry.py
```
This ensures your cloud dashboard shows live data!
