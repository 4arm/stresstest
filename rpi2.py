from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import socket
import time
import shlex

app = Flask(__name__)
CORS(app)

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

prev_net_io = psutil.net_io_counters()
prev_time = time.time()
stress_running = False  # Track stress test status

def get_temperature():
    """Get system temperature (if available)"""
    try:
        sensors = psutil.sensors_temperatures()
        for key in sensors:
            if sensors[key]:
                return sensors[key][0].current
    except Exception:
        pass
    return "Unavailable"

def get_system_info():
    """Fetch system stats including CPU, RAM, temperature, and network speed"""
    global prev_net_io, prev_time, stress_running

    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    time_diff = max(current_time - prev_time, 1)

    net_speed = round(((current_net_io.bytes_sent + current_net_io.bytes_recv) - 
                       (prev_net_io.bytes_sent + prev_net_io.bytes_recv)) / (1024 * 1024 * time_diff), 2)

    prev_net_io = current_net_io
    prev_time = current_time

    return {
        "hostname": hostname,
        "ip": ip_address,
        "cpu_usage": psutil.cpu_percent(),
        "ram_used": psutil.virtual_memory().used // (1024 * 1024),
        "temperature": get_temperature(),
        "network_speed": net_speed,
        "stress_running": stress_running  # Send stress test status to frontend
    }

@app.route('/data', methods=['GET'])
def data():
    """Return system info"""
    return jsonify(get_system_info())

@app.route('/stress', methods=['POST'])
def stress_test():
    """Start stress-ng CPU test with user-defined duration"""
    global stress_running

    if stress_running:
        return jsonify({"message": "Stress test is already running"}), 400

    data = request.get_json()
    duration = data.get("duration", 20)  # Default to 20 seconds if not provided

    try:
        stress_running = True
        subprocess.Popen(["stress-ng", "--cpu", "4", "--timeout", f"{duration}s"])  # Start stress test
        return jsonify({"message": f"Stress test started for {duration} seconds"}), 200
    except Exception as e:
        stress_running = False
        return jsonify({"error": str(e)}), 500

@app.route('/stop_stress', methods=['POST'])
def stop_stress():
    """Stop stress-ng CPU test"""
    global stress_running

    if not stress_running:
        return jsonify({"message": "No stress test is running"}), 400

    try:
        subprocess.run(["pkill", "-f", "stress-ng"])  # Kill any running stress-ng process
        stress_running = False
        return jsonify({"message": "Stress test stopped successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
