from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/telemetry')
def api_telemetry():
    mock_data = {
        "fleet": {
            "active_engines": 12,
            "critical_count": 3
        },
        "alerts": [
            "[14:23:45] CRITICAL: Engine E-001 high vibration detected",
            "[14:22:30] WARNING: Engine E-003 temperature above normal",
            "[14:21:15] CRITICAL: Engine E-007 pressure drop detected"
        ],
        "engine_grid": [
            {"id": "E-001", "health": 85, "status": "normal", "risk": 0.15},
            {"id": "E-002", "health": 92, "status": "normal", "risk": 0.08}
        ],
        "rul_bars": [
            {"id": "E-001", "rul": 85},
            {"id": "E-002", "rul": 92}
        ],
        "telemetry_lines": {
            "timestamps": ["14:20:00", "14:20:30", "14:21:00"],
            "s1": [60, 62, 58],
            "s2": [50, 52, 48],
            "s3": [40, 42, 38]
        }
    }
    return jsonify(mock_data)

if __name__ == '__main__':
    print("Starting Flask server...")
    print("API will be available at: http://localhost:5000/api/telemetry")
    app.run(host='0.0.0.0', port=5000, debug=False)
