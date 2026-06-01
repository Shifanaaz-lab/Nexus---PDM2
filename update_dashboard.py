import re

with open('rul_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace inject_dashboard_css function entirely
css_func_start = content.find('def inject_dashboard_css() -> None:')
css_func_end = content.find('def main() -> None:')

new_css_func = '''def inject_dashboard_css() -> None:
    st.markdown(
        """
        <style>
        /* Hyper-Advanced UI - Dark Teal Cyberpunk / Factory Engineering HUD */
        
        /* App Background */
        .stApp { 
            background-color: #04090f;
            background-image: 
                radial-gradient(circle at 50% 10%, rgba(20, 60, 80, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 10% 80%, rgba(0, 200, 255, 0.05) 0%, transparent 30%),
                linear-gradient(rgba(38, 208, 206, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(38, 208, 206, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
            background-attachment: fixed;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        /* Metric cards (HUD Style) */
        div[data-testid="metric-container"] {
            background: rgba(10, 15, 22, 0.85);
            border: 1px solid rgba(80, 200, 255, 0.15);
            border-top: 1px solid #26d0ce;
            border-bottom: 1px solid rgba(80, 200, 255, 0.05);
            border-radius: 2px; 
            padding: 1rem;
            box-shadow: inset 0 0 15px rgba(38, 208, 206, 0.02);
            position: relative;
            backdrop-filter: blur(4px);
            transition: all 0.2s ease;
        }
        
        /* HUD Corner Accents - Minimal tech dots */
        div[data-testid="metric-container"]::before {
            content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 4px; background: #26d0ce;
            box-shadow: 0 0 5px #26d0ce;
        }
        div[data-testid="metric-container"]::after {
            content: ''; position: absolute; top: 0; right: 0; width: 4px; height: 4px; background: #26d0ce;
            box-shadow: 0 0 5px #26d0ce;
        }
        
        div[data-testid="metric-container"] label { color: #6e849c !important; font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 1px; text-transform: uppercase; font-family: 'Consolas', 'Courier New', monospace; }
        
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { 
            color: #d1e8ef !important;
            font-size: 1.8rem !important; font-weight: 400 !important; font-family: 'Courier New', monospace; 
            text-shadow: 0 0 10px rgba(38, 208, 206, 0.3); 
        }
        
        /* Title area */
        .dashboard-title { 
            font-family: 'Courier New', monospace;
            font-size: 1.6rem; 
            font-weight: 700; 
            margin-bottom: 0.1rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #d1e8ef;
            text-shadow: 0 0 8px rgba(38, 208, 206, 0.4);
        }
        .dashboard-subtitle { 
            font-family: 'Consolas', monospace;
            color: #6e849c; 
            font-size: 0.8rem; 
            margin-bottom: 2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        /* Section Header */
        .section-header {
            font-family: 'Consolas', monospace; 
            color: #26d0ce; 
            font-size: 0.85rem; 
            letter-spacing: 2px;
            font-weight: 400;
            padding-bottom: 6px;
            margin-bottom: 12px;
            border-bottom: 1px solid rgba(38, 208, 206, 0.2);
            text-transform: uppercase;
            text-shadow: 0 0 5px rgba(38, 208, 206, 0.3);
            position: relative;
            display: inline-block;
        }
        .section-header::after {
            content: ''; position: absolute; bottom: -1px; left: 0; width: 30px; height: 1px; background: #26d0ce;
            box-shadow: 0 0 5px #26d0ce;
        }
        
        /* Status indicator */
        .status-dot { 
            display: inline-block; width: 6px; height: 6px; border-radius: 50%; 
            background: #26d0ce; animation: pulse 3s infinite; margin-right: 8px;
            box-shadow: 0 0 8px #26d0ce;
        }
        @keyframes pulse { 0% { opacity: 1; box-shadow: 0 0 8px #26d0ce; } 50% { opacity: 0.3; box-shadow: 0 0 2px #26d0ce; } 100% { opacity: 1; box-shadow: 0 0 8px #26d0ce; } }
        
        /* Terminal Log Area */
        .alert-log {
            background: rgba(8, 12, 18, 0.9);
            border: 1px solid rgba(38, 208, 206, 0.15);
            border-left: 2px solid #ef4444;
            border-radius: 0px;
            padding: 12px;
            height: 250px;
            overflow-y: auto;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.75rem;
            color: #92a4b8;
        }
        .alert-log::-webkit-scrollbar { width: 4px; }
        .alert-log::-webkit-scrollbar-thumb { background: #507b8c; }
        .alert-log p { margin: 4px 0; border-bottom: 1px dashed rgba(80, 200, 255, 0.1); padding-bottom: 2px; }
        .log-timestamp { color: #507b8c; font-size: 0.70rem;}
        .log-critical { color: #e64a4a; font-weight: normal; text-shadow: 0 0 5px rgba(230,74,74,0.4); }
        .log-warning { color: #de8b14; font-weight: normal; text-shadow: 0 0 5px rgba(222,139,20,0.4); }
        
        /* Streamlit elements overrides */
        hr { border-color: rgba(38, 208, 206, 0.1) !important; margin: 1.5rem 0 !important; }
        
        /* Disable Streamlit's default stale element fading */
        [data-stale="true"] {
            opacity: 1 !important;
            filter: none !important;
            transition: none !important;
        }
        </style>
        """
    )
'''

content = content[:css_func_start] + new_css_func + content[css_func_end:]

content = content.replace(
    '<p class="dashboard-title">Predictive Maintenance · Engine RUL Monitor</p>',
    '<div class="dashboard-title">Predictive Maintenance · Engine RUL Monitor</div>'
)
content = content.replace(
    '<p class="dashboard-subtitle">Real-time remaining useful life and failure probability across the fleet</p>',
    '<div class="dashboard-subtitle">Real-time remaining useful life and failure probability across the fleet</div>'
)

# Replace Tier headers
content = re.sub(r"<h4.*?PLATFORM HEALTH</h4>", "<div class='section-header'>PLATFORM HEALTH</div>", content)
content = re.sub(r"<h4.*?FLEET DIAGNOSTICS</h4>", "<div class='section-header'>FLEET DIAGNOSTICS</div>", content)
content = re.sub(r"<h4.*?FLEET RUL DISTRIBUTION</h4>", "<div class='section-header'>FLEET RUL DISTRIBUTION</div>", content)
content = re.sub(r"<h4.*?CRITICAL ENGINE TRAJECTORY</h4>", "<div class='section-header'>CRITICAL ENGINE TRAJECTORY</div>", content)
content = re.sub(r"<h4.*?REAL-TIME SOC SYSTEM LOG</h4>", "<div class='section-header'>REAL-TIME SOC SYSTEM LOG</div>", content)
content = re.sub(r"<h4.*?LIVE TELEMETRY STREAM</h4>", "<div class='section-header'>LIVE TELEMETRY STREAM</div>", content)

# Replace Donut
old_donut = '''            donut = alt.Chart(status_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(
                    field="Status", 
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Normal", "Warning", "Critical"],
                        range=["#10b981", "#f59e0b", "#ef4444"]
                    ),
                    legend=None
                ),
                tooltip=["Status", "Count"]
            ).properties(height=200)
            
            # Center text for donut chart
            text = alt.Chart(pd.DataFrame({'text': [f"{n_engines} Engines"]})).mark_text(
                radius=0, size=14, color="#f8fafc", fontWeight=600
            ).encode(text='text')'''

new_donut = '''            donut = alt.Chart(status_counts).mark_arc(innerRadius=60, stroke="#0a0f16", strokeWidth=1).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(
                    field="Status", 
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Normal", "Warning", "Critical"],
                        range=["#26d0ce", "#de8b14", "#e64a4a"]
                    ),
                    legend=None
                ),
                tooltip=["Status", "Count"]
            ).properties(height=200)
            
            # Center text for donut chart
            text = alt.Chart(pd.DataFrame({'text': [f"{n_engines} Engines"]})).mark_text(
                radius=0, size=12, color="#d1e8ef", fontWeight=400, font="Consolas"
            ).encode(text='text')'''

content = content.replace(old_donut, new_donut)

# Replace Histogram
old_hist = '''                chart = (
                    alt.Chart(hist_df)
                    .mark_bar(color="#38bdf8", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                    .encode(
                        alt.X("RUL (cycles):Q", bin=alt.Bin(maxbins=n_bins), title="Remaining Useful Life", axis=alt.Axis(grid=False, domainWidth=1)),
                        alt.Y("count():Q", title="Frequency", axis=alt.Axis(grid=True, gridColor="#1e293b", gridOpacity=0.5)),
                    )
                    .properties(height=280)
                    .configure_view(strokeWidth=0)
                    .configure_axis(labelColor="#94a3b8", titleColor="#94a3b8")
                )'''

new_hist = '''                chart = (
                    alt.Chart(hist_df)
                    .mark_bar(color="#26d0ce", opacity=0.8, size=4)
                    .encode(
                        alt.X("RUL (cycles):Q", bin=alt.Bin(maxbins=n_bins), title="Remaining Useful Life", axis=alt.Axis(grid=False, domainWidth=1, domainColor="#334a5e")),
                        alt.Y("count():Q", title="Frequency", axis=alt.Axis(grid=True, gridColor="rgba(38, 208, 206, 0.05)", gridOpacity=1, domainColor="#334a5e")),
                    )
                    .properties(height=280)
                    .configure_view(strokeWidth=0)
                    .configure_axis(labelColor="#6e849c", titleColor="#507b8c", labelFont="Consolas", titleFont="Consolas", tickColor="#334a5e")
                )'''

content = content.replace(old_hist, new_hist)

# Replace Line Chart
old_line = '''                line_chart = (
                    alt.Chart(worst_history)
                    .mark_line(color="#06b6d4", strokeWidth=2)
                    .encode(
                        x=alt.X("time:O", title=None, axis=alt.Axis(grid=False, labelAngle=-45)),
                        y=alt.Y("predicted_rul:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor="#1e293b", gridOpacity=0.5)),
                        tooltip=["time", "predicted_rul", "failure_probability"]
                    )
                    .properties(height=230)
                    .configure_view(strokeWidth=0)
                    .configure_axis(labelColor="#64748b", titleColor="#64748b", labelFont="Consolas", titleFont="Consolas")
                )
                st.altair_chart(line_chart, use_container_width=True)'''

new_line = '''                line = alt.Chart(worst_history).mark_line(color="#de8b14", strokeWidth=1.5).encode(
                    x=alt.X("time:O", title=None, axis=alt.Axis(grid=False, labelAngle=-45, domainColor="#334a5e")),
                    y=alt.Y("predicted_rul:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor="rgba(38, 208, 206, 0.05)", gridOpacity=1, domainColor="#334a5e")),
                    tooltip=["time", "predicted_rul", "failure_probability"]
                )
                point = alt.Chart(worst_history).mark_circle(color="#26d0ce", size=20).encode(
                    x=alt.X("time:O"), y=alt.Y("predicted_rul:Q")
                )
                area = alt.Chart(worst_history).mark_area(
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='rgba(222, 139, 20, 0.2)', offset=0),
                               alt.GradientStop(color='rgba(222, 139, 20, 0.0)', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X("time:O"), y=alt.Y("predicted_rul:Q")
                )
                line_chart = (area + line + point).properties(height=230)
                line_chart = line_chart.configure_view(strokeWidth=0).configure_axis(labelColor="#6e849c", titleColor="#507b8c", labelFont="Consolas", titleFont="Consolas", tickColor="#334a5e")
                st.altair_chart(line_chart, use_container_width=True)'''

content = content.replace(old_line, new_line)

# Replace dataframe styling
old_style_colors = '''colors = {
                "critical": "background-color: rgba(220, 38, 38, 0.1); color: #f87171; font-weight: 700; border-left: 2px solid #ef4444; font-family: Consolas, monospace;", 
                "warning": "background-color: rgba(245, 158, 11, 0.1); color: #fbbf24; font-weight: 600; border-left: 2px solid #f59e0b; font-family: Consolas, monospace;", 
                "normal": "color: #34d399; font-family: Consolas, monospace;"
            }'''

new_style_colors = '''colors = {
                "critical": "background-color: rgba(230, 74, 74, 0.1); color: #e64a4a; font-weight: normal; border-left: 2px solid #e64a4a; font-family: Consolas, monospace; text-shadow: 0 0 5px rgba(230,74,74,0.3);", 
                "warning": "background-color: rgba(222, 139, 20, 0.1); color: #de8b14; font-weight: normal; border-left: 2px solid #de8b14; font-family: Consolas, monospace; text-shadow: 0 0 5px rgba(222,139,20,0.3);", 
                "normal": "color: #26d0ce; font-family: Consolas, monospace;"
            }'''
content = content.replace(old_style_colors, new_style_colors)

# Replace dataframe styling properties
old_style_props = '''        styled = (
            display.style.format({"predicted_rul": "{:.1f}"})
            .map(lambda v: style_risk_band(v), subset=["risk_band"])
            .set_properties(**{"font-family": "Consolas, monospace", "background-color": "#030712", "border-bottom": "1px solid #1e293b", "color": "#d1d5db"})
            .set_properties(subset=["risk_band"], **{"text-align": "center"})
        )'''

new_style_props = '''        styled = (
            display.style.format({"predicted_rul": "{:.1f}"})
            .map(lambda v: style_risk_band(v), subset=["risk_band"])
            .set_properties(**{"font-family": "Consolas, monospace", "background-color": "transparent", "border-bottom": "1px dashed rgba(38, 208, 206, 0.15)", "color": "#92a4b8"})
            .set_properties(subset=["risk_band"], **{"text-align": "center"})
        )'''
content = content.replace(old_style_props, new_style_props)

with open('rul_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
