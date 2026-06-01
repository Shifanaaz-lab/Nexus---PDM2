import re

with open('rul_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace inject_dashboard_css function entirely
css_func_start = content.find('def inject_dashboard_css() -> None:')
css_func_end = content.find('def main() -> None:')

new_css_func = '''def inject_dashboard_css() -> None:
    st.markdown(
        \"\"\"
        <style>
        /* Hyper-Advanced SOC Command Center Theme - Cyberpunk */
        
        /* App Background */
        .stApp { 
            background-color: #080a10;
            background-image: 
                linear-gradient(135deg, rgba(8, 10, 16, 0.95) 0%, rgba(13, 17, 28, 0.95) 50%, rgba(5, 7, 12, 0.98) 100%),
                radial-gradient(ellipse at 80% 20%, rgba(0, 240, 255, 0.15), transparent 45%),
                radial-gradient(ellipse at 15% 85%, rgba(255, 0, 85, 0.15), transparent 45%),
                linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 100% 100%, 40px 40px, 40px 40px;
            background-attachment: fixed;
        }
        
        /* Metric cards (HUD Style) */
        div[data-testid=\"metric-container\"] {
            background: linear-gradient(180deg, rgba(20, 25, 35, 0.7), rgba(10, 15, 25, 0.8));
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-top: 2px solid #00f0ff;
            border-radius: 8px; 
            padding: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.6), inset 0 0 15px rgba(0, 240, 255, 0.05);
            position: relative;
            backdrop-filter: blur(8px);
            transition: all 0.3s ease;
        }
        
        div[data-testid=\"metric-container\"]:hover {
            border-color: rgba(0, 240, 255, 0.6);
            box-shadow: 0 4px 20px rgba(0, 240, 255, 0.2), inset 0 0 20px rgba(0, 240, 255, 0.1);
            transform: translateY(-2px);
        }
        
        /* HUD Corner Accents */
        div[data-testid=\"metric-container\"]::before {
            content: ''; position: absolute; top: -2px; left: -2px; width: 12px; height: 12px; 
            border-top: 2px solid #00f0ff; border-left: 2px solid #00f0ff; border-radius: 8px 0 0 0;
            box-shadow: -2px -2px 8px rgba(0, 240, 255, 0.6);
        }
        div[data-testid=\"metric-container\"]::after {
            content: ''; position: absolute; bottom: -2px; right: -2px; width: 12px; height: 12px; 
            border-bottom: 2px solid #ff0055; border-right: 2px solid #ff0055; border-radius: 0 0 8px 0;
            box-shadow: 2px 2px 8px rgba(255, 0, 85, 0.6);
        }
        
        div[data-testid=\"metric-container\"] label { color: #8b9bb4 !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 2px; text-transform: uppercase; font-family: 'Consolas', 'Courier New', monospace; }
        
        div[data-testid=\"metric-container\"] div[data-testid=\"stMetricValue\"] { 
            background: -webkit-linear-gradient(45deg, #ffffff, #00f0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.2rem !important; font-weight: 700 !important; font-family: 'Consolas', 'Courier New', monospace; 
            text-shadow: 0 0 20px rgba(0,240,255,0.4); 
        }
        
        /* Title area */
        .dashboard-title { 
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 2.0rem; 
            font-weight: 800; 
            margin-bottom: 0.1rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            background: -webkit-linear-gradient(45deg, #00f0ff, #ff0055);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
        }
        .dashboard-subtitle { 
            font-family: 'Consolas', 'Courier New', monospace;
            color: #8b9bb4; 
            font-size: 0.9rem; 
            margin-bottom: 2rem;
            text-transform: uppercase;
            letter-spacing: 4px;
            text-shadow: 0 0 4px rgba(139, 155, 180, 0.4);
        }
        
        /* Section Header */
        .section-header {
            font-family: 'Consolas', monospace; 
            color: #00f0ff; 
            font-size: 1rem; 
            letter-spacing: 3px;
            font-weight: 600;
            padding-bottom: 8px;
            margin-bottom: 12px;
            border-bottom: 1px solid rgba(0, 240, 255, 0.2);
            text-transform: uppercase;
            text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
            position: relative;
        }
        .section-header::after {
            content: ''; position: absolute; bottom: -1px; left: 0; width: 50px; height: 2px; background: #00f0ff;
            box-shadow: 0 0 10px #00f0ff;
        }
        
        /* Status indicator */
        .status-dot { 
            display: inline-block; width: 10px; height: 10px; border-radius: 50%; 
            background: #00f0ff; animation: pulse 2s infinite; margin-right: 8px;
            box-shadow: 0 0 10px #00f0ff, 0 0 20px #00f0ff;
        }
        @keyframes pulse { 0% { opacity: 1; box-shadow: 0 0 10px #00f0ff, 0 0 20px #00f0ff; } 50% { opacity: 0.4; box-shadow: 0 0 2px #00f0ff; } 100% { opacity: 1; box-shadow: 0 0 10px #00f0ff, 0 0 20px #00f0ff; } }
        
        /* Terminal Log Area */
        .alert-log {
            background: linear-gradient(135deg, rgba(15, 5, 10, 0.9), rgba(5, 2, 5, 0.95));
            border: 1px solid rgba(255, 0, 85, 0.3);
            border-left: 3px solid #ff0055;
            border-radius: 6px;
            padding: 12px;
            height: 250px;
            overflow-y: auto;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.85rem;
            color: #d1d5db;
            box-shadow: inset 0 0 20px rgba(255, 0, 85, 0.1), 0 4px 10px rgba(0,0,0,0.5);
        }
        .alert-log::-webkit-scrollbar { width: 6px; }
        .alert-log::-webkit-scrollbar-thumb { background: #ff0055; border-radius: 3px; }
        .alert-log p { margin: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 2px; }
        .log-timestamp { color: #8b9bb4; font-size: 0.75rem;}
        .log-critical { color: #ff0055; font-weight: bold; text-shadow: 0 0 8px rgba(255,0,85,0.5); }
        .log-warning { color: #ffaa00; font-weight: bold; text-shadow: 0 0 8px rgba(255,170,0,0.5); }
        
        /* Streamlit elements overrides */
        hr { border-color: rgba(0, 240, 255, 0.1) !important; margin: 1.5rem 0 !important; }
        
        /* Disable Streamlit's default stale element fading */
        [data-stale=\"true\"] {
            opacity: 1 !important;
            filter: none !important;
            transition: none !important;
        }
        </style>
        \"\"\",
        unsafe_allow_html=True,
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

new_donut = '''            donut = alt.Chart(status_counts).mark_arc(innerRadius=60, stroke="#080a10", strokeWidth=2).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(
                    field="Status", 
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Normal", "Warning", "Critical"],
                        range=["#00f0ff", "#ffaa00", "#ff0055"]
                    ),
                    legend=None
                ),
                tooltip=["Status", "Count"]
            ).properties(height=200)
            
            # Center text for donut chart
            text = alt.Chart(pd.DataFrame({'text': [f"{n_engines} Engines"]})).mark_text(
                radius=0, size=14, color="#00f0ff", fontWeight=700, font="Consolas"
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
                    .mark_bar(color="#ffaa00", opacity=0.85, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        alt.X("RUL (cycles):Q", bin=alt.Bin(maxbins=n_bins), title="Remaining Useful Life", axis=alt.Axis(grid=False, domainWidth=1)),
                        alt.Y("count():Q", title="Frequency", axis=alt.Axis(grid=True, gridColor="rgba(255,255,255,0.05)", gridOpacity=1)),
                    )
                    .properties(height=280)
                    .configure_view(strokeWidth=0)
                    .configure_axis(labelColor="#8b9bb4", titleColor="#8b9bb4", labelFont="Consolas", titleFont="Consolas")
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

new_line = '''                line = alt.Chart(worst_history).mark_line(color="#00f0ff", strokeWidth=3).encode(
                    x=alt.X("time:O", title=None, axis=alt.Axis(grid=False, labelAngle=-45)),
                    y=alt.Y("predicted_rul:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor="rgba(255,255,255,0.05)", gridOpacity=1)),
                    tooltip=["time", "predicted_rul", "failure_probability"]
                )
                area = alt.Chart(worst_history).mark_area(
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='rgba(0, 240, 255, 0.4)', offset=0),
                               alt.GradientStop(color='rgba(0, 240, 255, 0.0)', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X("time:O"), y=alt.Y("predicted_rul:Q")
                )
                line_chart = (area + line).properties(height=230)
                line_chart = line_chart.configure_view(strokeWidth=0).configure_axis(labelColor="#8b9bb4", titleColor="#8b9bb4", labelFont="Consolas", titleFont="Consolas")
                st.altair_chart(line_chart, use_container_width=True)'''

content = content.replace(old_line, new_line)

# Replace dataframe styling (first part)
old_style_colors = '''colors = {
                "critical": "background-color: rgba(220, 38, 38, 0.1); color: #f87171; font-weight: 700; border-left: 2px solid #ef4444; font-family: Consolas, monospace;", 
                "warning": "background-color: rgba(245, 158, 11, 0.1); color: #fbbf24; font-weight: 600; border-left: 2px solid #f59e0b; font-family: Consolas, monospace;", 
                "normal": "color: #34d399; font-family: Consolas, monospace;"
            }'''

new_style_colors = '''colors = {
                "critical": "background-color: rgba(255, 0, 85, 0.15); color: #ff0055; font-weight: 700; border-left: 3px solid #ff0055; font-family: Consolas, monospace; text-shadow: 0 0 5px rgba(255,0,85,0.5);", 
                "warning": "background-color: rgba(255, 170, 0, 0.15); color: #ffaa00; font-weight: 600; border-left: 3px solid #ffaa00; font-family: Consolas, monospace; text-shadow: 0 0 5px rgba(255,170,0,0.5);", 
                "normal": "color: #00f0ff; font-family: Consolas, monospace; text-shadow: 0 0 5px rgba(0,240,255,0.3);"
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
            .set_properties(**{"font-family": "Consolas, monospace", "background-color": "rgba(10, 15, 25, 0.8)", "border-bottom": "1px solid rgba(255,255,255,0.05)", "color": "#d1d5db"})
            .set_properties(subset=["risk_band"], **{"text-align": "center"})
        )'''
content = content.replace(old_style_props, new_style_props)

with open('rul_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
