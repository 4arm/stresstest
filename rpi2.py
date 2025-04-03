from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import socket
import time
import threading

app = Flask(__name__)
CORS(app)

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

prev_net_io = psutil.net_io_counters()
prev_time = time.time()
stress_running = False
stress_report = None
network_test_running = False  # Flag to prevent multiple network tests

def get_temperature():
    try:
        sensors = psutil.sensors_temperatures()
        for key in sensors:
            if sensors[key]:
                return sensors[key][0].current
    except Exception:
        pass
    return "Unavailable"

def get_system_info():
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
        "stress_running": stress_running
    }

@app.route('/data', methods=['GET'])
def data():
    return jsonify(get_system_info())

@app.route('/network_test', methods=['POST'])
def network_test():
    global network_test_running
    if network_test_running:
        return jsonify({"message": "Network test is already running"}), 400

    data = request.get_json()
    target_ip = data.get("target_ip")

    if not target_ip:
        return jsonify({"error": "Target IP is required"}), 400

    def run_iperf():
        global network_test_running
        network_test_running = True
        try:
            result = subprocess.run(["iperf3", "-c", target_ip, "-J"], capture_output=True, text=True)
            network_test_running = False
            return jsonify({"result": result.stdout})
        except Exception as e:
            network_test_running = False
            return jsonify({"error": str(e)}), 500

    thread = threading.Thread(target=run_iperf)
    thread.start()
    return jsonify({"message": f"Network test started with {target_ip}"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
