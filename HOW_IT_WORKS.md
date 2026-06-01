# How the NEXUS Command Center Works

This document explains the **architecture**, **data flow**, and **logic** of the high-fidelity predictive maintenance system.

---

## 1. The Big Picture

```mermaid
graph TD
    A[Telemetry Simulator (10Hz)] -->|Batched sensor drift + XGBoost| B[(MongoDB Atlas)]
    B -->|High-Speed Aggregation| C[Flask Industrial API]
    C -->|sub-100ms JSON stream| D[Command Center UI]
    D -->|Spatially Stable DOM| E[Operator Console]
```

- **Simulator** (`real_time_engine_telemetry.py`): Simulates a fleet of 100 aero-engines. Generates 10 batches per second (10Hz) to represent real-world high-frequency sensor intake.
- **Backend API** (`app.py`): Uses optimized MongoDB aggregations to fetch the latest state of all 100 engines in a single efficient call.
- **Frontend** (`templates/index.html`): Implements **Spatial Stability** and **Ultra-Fast Polling (100ms)**. Unlike consumer dashboards that "re-sort" and jump, NEXUS locks assets to a fixed grid (E-001 to E-012) while updating their risk levels every 0.1s in place.

---

## 2. Telemetry and Feature Engineering

The simulator acts as the "Hardware Layer," generating synthetic degradation (sensor drift + noise) for a fleet of 100 aero-engines.

- **Features**: The model (XGBoost) requires engineered features (rolling means, standard deviations, lags, and trends). 
- **Health Heuristics**: 
    - **RUL**: Direct output of the trained XGBoost model.
    - **Failure Probability**: A heuristic derived from the engine's current cycle relative to its theoretical design life (Life Ratio).

---

## 3. High-Fidelity Logic Engines

### A. Dynamic Alert Synchronization
The **Risk Alerts KPI** and the **Alerts Log** in the "Alerts" tab are physical mirrors of each other.
- **Trigger**: Any engine with a `failure_probability` > 0.5 (WARNING) or > 0.85 (CRITICAL).
- **Sync**: The backend (`app.py`) generates a `total_risk_count` field which the frontend uses to ensure the KPI count always matches the number of rows in the log.

### B. Intelligent Maintenance Schedule
The "Maintenance Schedule" component uses a multi-tier selection algorithm:
1.  **Immediate Attention**: Locked to the engine with the **highest absolute failure probability** across the entire 100-engine fleet.
2.  **Upcoming Tasks**: Identifies the next two engines with the **lowest Remaining Useful Life (RUL)**.
3.  **Conflict Resolution**: The system filters out the "Immediate" engine from the "Upcoming" list to ensure you see varied, actionable data across the fleet.

---

## 4. Visual Execution (UI/UX)
- **SOC Command Center Palette**: Deep Navy, Black, and Cyan-glow. 
- **Spatial Consistency**: The core asset grid maintains a constant sort order. This is a critical HCI feature for industrial operators who monitor specific assets visually over long shifts.
- **High-Fidelity Pulse**: Critical states trigger CSS `@keyframes` pulsing rather than static color changes, increasing the "conspicuousness" of risks without cluttering the UI.

---

## 5. Summary Table

| Element | Logic Source | UI Indication |
|---------|--------------|---------------|
| **Risk Alerts KPI** | `df_latest[risk > 0.5]` | Synchronized with Alerts Tab |
| **Fleet RUL Dist** | Fleet-wide `predicted_rul` | Interactive Plotly Histogram |
| **Asset Grid** | Head(12) sorted by risk | Click-to-open Engine Reports |
| **Maintenance** | Top 1 (Risk) + Top 2 (RUL) | Unique Engine Targeting |
| **Telemetry Lines** | Last 30 cycles of "Worst Engine" | Real-time Sensor Trends |
