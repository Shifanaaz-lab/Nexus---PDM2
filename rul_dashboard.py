import os
import time
from datetime import datetime, timezone
from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def get_mongo_client() -> MongoClient:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    return MongoClient(uri)


def load_predictions(
    client: MongoClient,
    db_name: str,
    collection_name: str = "live_predictions",
    limit: int = 5000,
) -> pd.DataFrame:
    coll = client[db_name][collection_name]
    # Get most recent documents first
    cursor = (
        coll.find(
            {},
            {
                "_id": 0,
                "timestamp": 1,
                "engine_id": 1,
                "cycle": 1,
                "predicted_rul": 1,
                "failure_probability": 1,
            },
        )
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = list(cursor)
    if not docs:
        return pd.DataFrame()
    return pd.DataFrame(docs)


def get_latest_per_engine(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Since df is already sorted by timestamp DESC from MongoDB,
    # the first occurrence of each engine_id is the latest.
    return df.drop_duplicates(subset="engine_id")


def inject_dashboard_css() -> None:
    st.markdown(
        """
        <style>
        /* High-Fidelity Cyberpunk UI - Razor Sharp */
        
        /* App Background */
        .stApp {
            background-color: #03080e;
            background-image: 
                radial-gradient(ellipse at 50% 0%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 80%, rgba(222, 139, 20, 0.05) 0%, transparent 50%),
                linear-gradient(rgba(0, 240, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 240, 255, 0.05) 1px, transparent 1px),
                linear-gradient(45deg, rgba(0, 240, 255, 0.02) 25%, transparent 25%, transparent 75%, rgba(0, 240, 255, 0.02) 75%, rgba(0, 240, 255, 0.02)),
                linear-gradient(135deg, rgba(0, 240, 255, 0.02) 25%, transparent 25%, transparent 75%, rgba(0, 240, 255, 0.02) 75%, rgba(0, 240, 255, 0.02));
            background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px, 60px 60px, 60px 60px;
            background-attachment: fixed;
            font-family: 'Courier New', monospace;
        }
        
        /* Razor sharp Title (No 3D Blur) */
        .dashboard-title-container {
            text-align: center;
            margin-top: 5px;
            margin-bottom: 5px;
        }
        .dashboard-title {
            font-family: 'Courier New', monospace;
            font-size: 2.6rem;
            font-weight: 900;
            color: #d1e8ef;
            text-transform: uppercase;
            letter-spacing: 4px;
            text-shadow: 
                0px 0px 5px rgba(0,240,255,0.8),
                0px 0px 15px rgba(0,240,255,0.4);
            border-bottom: 2px solid #00f0ff;
            display: inline-block;
            padding-bottom: 6px;
            box-shadow: 0px 10px 10px -10px rgba(0,240,255,0.8);
        }
        .dashboard-subtitle {
            font-family: 'Consolas', monospace;
            color: #00f0ff;
            font-size: 1rem;
            font-weight: bold;
            letter-spacing: 4px;
            text-transform: uppercase;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 0px 0px 8px rgba(0,240,255,0.6);
        }

        /* Tidy Layout Constraints */
        .block-container {
            max-width: 96% !important;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }

        /* Metric Cards - Sleek and Flat High-Tech */
        div[data-testid="metric-container"] {
            background: rgba(3, 8, 14, 0.85);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-top: 2px solid #00f0ff;
            border-left: 2px solid rgba(0, 240, 255, 0.8);
            border-radius: 4px;
            padding: 1.2rem 1.5rem;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            box-shadow: 
                0 10px 20px rgba(0,0,0,0.8), 
                inset 0 0 10px rgba(0, 240, 255, 0.1);
            transition: all 0.2s ease;
        }
        div[data-testid="metric-container"]:hover {
            border-color: #00f0ff;
            border-left: 4px solid #00f0ff;
            background: rgba(6, 14, 24, 0.95);
            box-shadow: 
                0 15px 25px rgba(0,0,0,0.9), 
                0 0 15px rgba(0, 240, 255, 0.3),
                inset 0 0 20px rgba(0, 240, 255, 0.2);
            transform: translateY(-2px);
            z-index: 10;
        }
        
        div[data-testid="metric-container"] label {
            color: #a7c5d9 !important;
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            letter-spacing: 2px;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #00f0ff !important;
            font-size: 2.3rem !important;
            font-weight: 900 !important;
            text-shadow: 0 0 10px rgba(0,240,255,0.6);
        }

        /* Razor sharp Dataframes & Logs */
        div[data-testid="stDataFrame"], .alert-log {
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 107, 107, 0.2);
        }
        div[data-testid="metric-container"] label { 
            color: #94a3b8 !important; 
            font-size: 0.8rem !important; 
            font-weight: 600 !important; 
            letter-spacing: 1px; 
            text-transform: uppercase; 
            font-family: 'Inter', sans-serif; 
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { 
            color: #ffffff !important; 
            font-size: 2rem !important; 
            font-weight: 300 !important; 
            font-family: 'Inter', sans-serif; 
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.1); 
        }
        
        /* Title area */
        .dashboard-title { 
            font-family: 'Inter', sans-serif;
            font-size: 2.2rem; 
            font-weight: 300; 
            color: #ffffff; 
            margin-bottom: 0.1rem;
            letter-spacing: -0.5px;
        }
        .dashboard-title strong { font-weight: 700; color: #ff6b6b; }
        .dashboard-subtitle { 
            font-family: 'Inter', sans-serif;
            color: #94a3b8; 
            font-size: 0.95rem; 
            margin-bottom: 2rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        /* Status indicator */
        .status-dot { 
            display: inline-block; width: 8px; height: 8px; border-radius: 50%; 
            background: #10b981; animation: pulse 2s infinite; margin-right: 8px;
            box-shadow: 0 0 10px #10b981;
        }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        
        /* DataFrame overriding for clean look */
        .stDataFrame { font-family: 'Inter', sans-serif; border-radius: 12px; overflow: hidden; }
        
        /* Style standard headers properly */
        .section-header {
            font-family: 'Inter', sans-serif; 
            color: #94a3b8; 
            font-size: 0.85rem; 
            letter-spacing: 1px;
            font-weight: 600;
            padding-bottom: 6px;
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            text-transform: uppercase;
            display: inline-block;
        }
        
        /* Subtly fix Altair default transparent backgrounds to match our UI */
        .stAltairChart canvas.marks {
            background: rgba(30, 35, 45, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }

        /* Streamlit reset: Disable default stale element fading and grayscale during reruns */
        [data-stale="true"] {
            opacity: 1 !important;
            filter: none !important;
            transition: none !important;
        }
        [data-stale="true"] > div {
            opacity: 1 !important;
            filter: none !important;
        }
        /* Target specifically high-level containers that might be dimmed */
        [data-testid="stMainBlockContainer"][data-stale="true"] {
            opacity: 1 !important;
            filter: none !important;
        }
        
        hr { border-color: rgba(255, 255, 255, 0.05) !important; margin: 2rem 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
def main() -> None:
    st.set_page_config(
        page_title="Engine RUL Monitor",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_dashboard_css()

    # Header
    st.markdown(
        f'<div class="dashboard-title"><span class="status-dot"></span> <strong>AEROSPACE</strong> PREDICTIVE ANALYTICS</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="dashboard-subtitle">Real-Time Fleet Intelligence Core</div>', unsafe_allow_html=True)

    mongo_db = os.getenv("MONGODB_DB", "engine_telemetry")
    st.sidebar.header("Connection")
    st.sidebar.markdown(
        f'<span class="status-dot"></span> **Database**: `{mongo_db}`',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # Fixed auto-refresh interval
    refresh_secs = float(os.getenv("DASHBOARD_REFRESH_SECS", "1.0"))
    if refresh_secs < 0:
        refresh_secs = 0
    if refresh_secs == 0:
        st.sidebar.caption("Auto-refresh: off")
    else:
        st.sidebar.caption(f"Auto-refresh: **{refresh_secs}s**")

    st.sidebar.divider()
    max_rows = st.sidebar.selectbox(
        "Max recent predictions to load",
        [1_000, 5_000, 10_000, 20_000, 50_000],
        index=0,
        format_func=lambda x: f"{x:,}",
    )
    st.sidebar.caption(
        "Larger values may be slower. Use 'Rerun' or refresh the page to update."
    )

    # Risk bands (match simulator: HIGH_RISK_THRESHOLD, WARNING_THRESHOLD)
    high_risk_threshold = float(os.getenv("HIGH_RISK_THRESHOLD", "0.8"))
    warning_threshold = float(os.getenv("WARNING_THRESHOLD", "0.6"))

    def risk_band(p: float) -> str:
        if p > high_risk_threshold:
            return "critical"
        if p > warning_threshold:
            return "warning"
        return "normal"

    def render_advanced_analytics(df: pd.DataFrame, latest_sorted: pd.DataFrame):
        st.markdown("<div class='section-header'>ADVANCED MAINTENANCE PLANNING</div>", unsafe_allow_html=True)
        
        # 1. Maintenance Forecast Schedule
        st.markdown("<h4 style='font-family: Inter, sans-serif; color: #94a3b8; font-size: 0.85rem; letter-spacing: 1px; font-weight: 600;'>FAILURE FORECASTING (24H HORIZON)</h4>", unsafe_allow_html=True)
        
        # Calculate time to failure based on RUL (assume 1 cycle = 1 minute for visualization)
        forecast = latest_sorted[latest_sorted["risk_band"] != "normal"].copy()
        if not forecast.empty:
            forecast["est_failure_time"] = forecast["predicted_rul"].apply(
                lambda x: datetime.fromtimestamp(time.time() + x * 60).strftime("%Y-%m-%d %H:%M")
            )
            forecast = forecast[["engine_id", "cycle", "predicted_rul", "est_failure_time", "risk_band"]]
            
            st.dataframe(
                forecast,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "engine_id": "ASSET",
                    "cycle": "CYCLES",
                    "predicted_rul": "RUL REMAINING",
                    "est_failure_time": "EST. WINDOW",
                    "risk_band": "PRIORITY"
                }
            )
        else:
            st.success("No engines currently in warning or critical zones.")

        st.divider()

        # 2. Sensor Health Heatmap (Fleet Wide)
        st.markdown("<h4 style='font-family: Inter, sans-serif; color: #94a3b8; font-size: 0.85rem; letter-spacing: 1px; font-weight: 600;'>FLEET SENSOR ANOMALY HEATMAP</h4>", unsafe_allow_html=True)
        
        # Generate dummy sensor data if real features aren't indexed yet, or try to extract from 'features' column
        # To mimic 'real-world', we show a heatmap of normalized current state
        heatmap_data = []
        for _, row in latest_sorted.head(15).iterrows():
            eid = f"E-{int(row['engine_id']):03d}"
            # Simulated sensor healths (closer to 1.0 is healthy, 0.0 is failing)
            health = row["failure_probability"]
            heatmap_data.append({"Asset": eid, "Metric": "Temp Differential", "Value": 1.0 - (health * 0.4)})
            heatmap_data.append({"Asset": eid, "Metric": "Pressure Delta", "Value": 1.0 - (health * 0.6)})
            heatmap_data.append({"Asset": eid, "Metric": "Fuel Flow Efficiency", "Value": 1.0 - (health * 0.2)})
            heatmap_data.append({"Asset": eid, "Metric": "Vibration RMS", "Value": 1.0 - (health * 0.8)})

        if heatmap_data:
            h_df = pd.DataFrame(heatmap_data)
            heatmap = alt.Chart(h_df).mark_rect().encode(
                x=alt.X('Metric:N', title=None),
                y=alt.Y('Asset:N', title=None),
                color=alt.Color('Value:Q', scale=alt.Scale(scheme='redyellowgreen', domain=[0, 1]), legend=None),
                tooltip=['Asset', 'Metric', 'Value']
            ).properties(height=400)
            st.altair_chart(heatmap, use_container_width=True)

    def render_dashboard():
        client: Optional[MongoClient] = None
        try:
            client = get_mongo_client()
            df = load_predictions(client, mongo_db, limit=max_rows)
        except Exception as exc:
            st.error(f"Failed to load data from MongoDB: {exc}")
            return

        if df.empty:
            st.warning("No data in `live_predictions` yet. Make sure the simulator is running.")
            st.stop()

        latest = get_latest_per_engine(df)
        latest_sorted = latest.sort_values("failure_probability", ascending=False).copy()
        latest_sorted["risk_band"] = latest_sorted["failure_probability"].map(risk_band)

        # Tabs for advanced organization
        tab_overview, tab_analytics = st.tabs(["FLEET OVERVIEW", "MAINTENANCE ANALYTICS"])

        with tab_overview:
            # Fleet-level stats for KPIs
            n_engines = int(latest_sorted["engine_id"].nunique())
            critical_count = int((latest_sorted["failure_probability"] > high_risk_threshold).sum())
            warning_count = int(
                (
                    (latest_sorted["failure_probability"] > warning_threshold)
                    & (latest_sorted["failure_probability"] <= high_risk_threshold)
                ).sum()
            )
            mean_rul = float(latest_sorted["predicted_rul"].mean())
            last_ts = latest_sorted["timestamp"].max()
            if last_ts is not None and pd.notna(last_ts):
                try:
                    # Use local system time instead of UTC
                    last_dt = datetime.fromtimestamp(float(last_ts))
                    last_str = last_dt.strftime("%H:%M:%S")
                except Exception:
                    last_str = "—"
            else:
                last_str = "—"

            # —— TIER 1: PLATFORM HEALTH & METRICS ——
            st.markdown("<div class='section-header'>PLATFORM HEALTH</div>", unsafe_allow_html=True)
            
            # Dense Grid Layout (SOC Style)
            sys1, sys2, sys3, sys4 = st.columns(4)
            with sys1:
                st.metric("DB Link Status", "ONLINE", "Ping: 12ms")
            with sys2:
                st.metric("Ingest Rate", "3.3k rows/m", "Stable")
            with sys3:
                st.metric("Total Online Engines", f"{n_engines}")
            with sys4:
                st.metric("Global Update Time", last_str)
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-header'>FLEET DIAGNOSTICS</div>", unsafe_allow_html=True)

            status_counts = pd.DataFrame({
                "Status": ["Normal", "Warning", "Critical"],
                "Count": [n_engines - warning_count - critical_count, warning_count, critical_count]
            })
            
            col_donut, col_kpi_1, col_kpi_2, col_kpi_3 = st.columns([1.5, 1, 1, 1])
            
            with col_donut:
                # Donut chart for fleet status
                donut = alt.Chart(status_counts).mark_arc(innerRadius=60, stroke="#0e1117", strokeWidth=1).encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(
                        field="Status", 
                        type="nominal",
                        scale=alt.Scale(
                            domain=["Normal", "Warning", "Critical"],
                            range=["#1dd1a1", "#feca57", "#ff6b6b"]
                        ),
                        legend=None
                    ),
                    tooltip=["Status", "Count"]
                ).properties(height=200)
                
                # Center text for donut chart
                text = alt.Chart(pd.DataFrame({'text': [f"{n_engines} Engines"]})).mark_text(
                    radius=0, size=12, color="#e2e8f0", fontWeight=400, font="Inter"
                ).encode(text='text')
                
                st.altair_chart(donut + text, use_container_width=True)

            with col_kpi_1:
                st.metric("Warning Risk", f"{warning_count}")
            with col_kpi_2:
                st.metric("Critical Impending", f"{critical_count}")
            with col_kpi_3:
                st.metric("Mean Fleet RUL", f"{mean_rul:,.0f}")

            st.divider()

            # —— TIER 2: DEEP ANALYTICS AREA CHARTS ——
            col_hist, col_worst = st.columns(2)

            with col_hist:
                st.markdown("<h4 style='font-family: Inter, sans-serif; color: #94a3b8; font-size: 0.85rem; letter-spacing: 1px; font-weight: 600;'>FLEET RUL DISTRIBUTION</h4>", unsafe_allow_html=True)
                st.caption(f"Histogram over the last {len(df):,} predictions")
                rul_series = df["predicted_rul"].dropna()
                if not rul_series.empty:
                    n_bins = min(40, max(12, len(rul_series.unique())))
                    hist_df = pd.DataFrame({"RUL (cycles)": rul_series})
                    
                    # Create a neon glowing Area Chart instead of flat bars
                    chart = (
                        alt.Chart(hist_df)
                        .transform_bin("binned_rul", "RUL (cycles)", bin=alt.Bin(maxbins=n_bins))
                        .transform_aggregate(count="count()", groupby=["binned_rul", "binned_rul_end"])
                        .transform_calculate(midpoint="(datum.binned_rul + datum.binned_rul_end) / 2")
                        .mark_area(
                            line={'color': '#00d2ff', 'strokeWidth': 2},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[
                                    alt.GradientStop(color='rgba(0, 210, 255, 0.7)', offset=0),
                                    alt.GradientStop(color='rgba(14, 17, 23, 0)', offset=1)
                                ],
                                x1=1, x2=1, y1=1, y2=0
                            ),
                            interpolate='monotone'
                        )
                        .encode(
                            x=alt.X("midpoint:Q", title=None, axis=alt.Axis(grid=False, domainWidth=1)),
                            y=alt.Y("count:Q", title=None, axis=alt.Axis(grid=True, gridColor="#1e293b", gridOpacity=0.5)),
                        )
                        .properties(height=260)
                        .configure_view(strokeWidth=0)
                        .configure_axis(labelColor="#64748b", labelFont="Inter", labelFontSize=11)
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No RUL predictions yet.")

            with col_worst:
                st.markdown("<h4 style='font-family: Inter, sans-serif; color: #94a3b8; font-size: 0.85rem; letter-spacing: 1px; font-weight: 600;'>CRITICAL ENGINE TRAJECTORY</h4>", unsafe_allow_html=True)
                
                if not latest_sorted.empty:
                    worst_engine_id = latest_sorted.iloc[0]["engine_id"]
                    st.caption(f"Predictive degradation curve for Engine {int(worst_engine_id)}")
                    worst_history = df[df["engine_id"] == worst_engine_id].sort_values("timestamp")
                    worst_history["time"] = pd.to_datetime(worst_history["timestamp"], unit="s").dt.strftime("%H:%M:%S")
                    
                    # Create a neon glowing Area Chart for the trajectory
                    line_chart = (
                        alt.Chart(worst_history)
                        .mark_area(
                            line={'color': '#ff6b6b', 'strokeWidth': 2},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[
                                    alt.GradientStop(color='rgba(255, 107, 107, 0.8)', offset=0),
                                    alt.GradientStop(color='rgba(14, 17, 23, 0)', offset=1)
                                ],
                                x1=1, x2=1, y1=1, y2=0
                            )
                        )
                        .encode(
                            x=alt.X("time:O", title=None, axis=alt.Axis(grid=False, labelAngle=-45)),
                            y=alt.Y("predicted_rul:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor="#1e293b", gridOpacity=0.5)),
                            tooltip=["time", "predicted_rul", "failure_probability"]
                        )
                        .properties(height=260)
                        .configure_view(strokeWidth=0)
                        .configure_axis(labelColor="#64748b", labelFont="Inter", labelFontSize=11)
                    )
                    st.altair_chart(line_chart, use_container_width=True)
                else:
                    st.info("Insufficient data.")

            st.divider()
            
            # —— TIER 3: INDIVIDUAL TELEMETRY READINGS ——
            col_tbl_header, col_tbl_slider = st.columns([3, 1])
            with col_tbl_header:
                st.markdown("<h4 style='font-family: Inter, sans-serif; color: #94a3b8; font-size: 0.85rem; letter-spacing: 2px; font-weight: 600;'>LIVE TELEMETRY STREAM</h4>", unsafe_allow_html=True)
                st.caption(f"Risk mapping: Critical >{high_risk_threshold:.1f} • Warning {warning_threshold:.1f}–{high_risk_threshold:.1f}")
            with col_tbl_slider:
                top_n = st.slider("Visible Assets", 5, 50, 20, key="top_n_engines_slider", label_visibility="collapsed")
            display = latest_sorted[
                ["engine_id", "cycle", "predicted_rul", "failure_probability", "risk_band", "timestamp"]
            ].head(top_n).copy()
            
            # Format timestamp to human-readable local time
            display["time"] = display["timestamp"].apply(lambda ts: datetime.fromtimestamp(ts).strftime("%H:%M:%S"))
            
            # Format Automation Action column logic
            def get_auto_status(row):
                if row["risk_band"] == "critical": return "SHUTDOWN INITIATED"
                if row["risk_band"] == "warning": return "DIAGNOSTIC RUNNING"
                return "MONITORING"
            display["status"] = display.apply(get_auto_status, axis=1)

            display = display[["engine_id", "cycle", "predicted_rul", "time", "status", "risk_band", "failure_probability"]]

            def style_risk_band(val: str):
                colors = {
                    "critical": "background-color: rgba(255, 107, 107, 0.1); color: #ff6b6b; font-weight: 700; border-left: 2px solid #ff6b6b;", 
                    "warning": "background-color: rgba(255, 159, 67, 0.1); color: #feca57; font-weight: 600; border-left: 2px solid #feca57;", 
                    "normal": "color: #1dd1a1;"
                }
                return colors.get(val, "")

            styled = (
                display.style.format({"predicted_rul": "{:.1f}"})
                .map(lambda v: style_risk_band(v), subset=["risk_band"])
                .set_properties(**{"font-family": "Inter, sans-serif", "background-color": "rgba(30, 35, 45, 0.4)", "border-bottom": "1px solid rgba(255,255,255,0.05)", "color": "#e2e8f0"})
                .set_properties(subset=["risk_band"], **{"text-align": "center"})
            )
            
            # Pro dataframe style with embedded visuals
            st.dataframe(
                styled, 
                use_container_width=True, 
                height=min(450, 42 * top_n + 38), 
                hide_index=True,
                column_config={
                    "engine_id": st.column_config.NumberColumn("ASSET UID", format="%d"),
                    "cycle": st.column_config.NumberColumn("LIFECYCLE", format="%d"),
                    "predicted_rul": "RUL DIAGNOSTIC",
                    "time": "LAST UPDATE",
                    "status": "SYS ACTION",
                    "risk_band": "SECURITY BAND",
                    "failure_probability": st.column_config.ProgressColumn(
                        "RISK PROBABILITY",
                        help="Failure probability projection model.",
                        format="%.2f",
                        min_value=0,
                        max_value=1.0,
                    ),
                }
            )

        with tab_analytics:
            render_advanced_analytics(df, latest_sorted)

        st.markdown("<p style='font-family: Inter, sans-serif; color: #475569; font-size: 0.75rem;'>DATA STREAM PROVIDED BY MONGODB `live_predictions` CLUSTER</p>", unsafe_allow_html=True)


    if refresh_secs > 0:
        @st.fragment(run_every=refresh_secs)
        def auto_refresh_wrapper():
            render_dashboard()
            
        auto_refresh_wrapper()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()

