from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import socket
import time
import shlex
import threading

app = Flask(__name__)
CORS(app)

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

prev_net_io = psutil.net_io_counters()
prev_time = time.time()

stress_running = False  # Global flag to track stress status

def get_temperature():
    try:
        sensors = psutil.sensors_temperatures()
        for key in sensors:
            if sensors[key]:
                return sensors[key][0].current
    except Exception:
        pass
    return "Unavailable"

def get_iperf3_stats():
    """ Run iPerf3 as a client to monitor ongoing traffic """
    try:
        cmd = "iperf3 -c 192.168.0.50 -t 5 -J"  # Run test for 5 seconds in JSON mode
        result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return str(e)

def get_system_info():
    global prev_net_io, prev_time

    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    time_diff = max(current_time - prev_time, 1)

    net_speed = round(((current_net_io.bytes_sent + current_net_io.bytes_recv) - 
                       (prev_net_io.bytes_sent + prev_net_io.bytes_recv)) / (1024 * 1024 * time_diff), 2)

    return {
        "hostname": hostname,
        "ip": ip_address,
        "cpu_usage": psutil.cpu_percent(),
        "ram_used": psutil.virtual_memory().used // (1024 * 1024),
        "temperature": get_temperature(),
        "network_speed": net_speed,
        "iperf3_stats": get_iperf3_stats(),
        "stress_running": stress_running  # Return stress status
    }

@app.route('/data', methods=['GET'])
def data():
    return jsonify(get_system_info())

@app.route('/stress', methods=['POST'])
def stress_cpu():
    global stress_running

    try:
        data = request.get_json()
        duration = int(data.get("duration", 20))  # Default to 20 seconds if not provided

        if stress_running:
            return jsonify({"message": "Stress test already running!"}), 400

        stress_running = True

        def run_stress():
            global stress_running
            subprocess.run(["stress-ng", "--cpu", "4", "--timeout", f"{duration}s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stress_running = False  # Reset flag after test completes

        threading.Thread(target=run_stress).start()
        return jsonify({"message": f"CPU stress test started for {duration} seconds!"})
    
    except Exception as e:
        stress_running = False
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
