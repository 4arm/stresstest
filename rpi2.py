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

    prev_net_io = current_net_io
    prev_time = current_time

    return {
        "hostname": hostname,
        "ip": ip_address,
        "cpu_usage": psutil.cpu_percent(),
        "ram_used": psutil.virtual_memory().used // (1024 * 1024),
        "temperature": get_temperature(),
        "network_speed": net_speed,
        "iperf3_stats": get_iperf3_stats()  # Get iPerf3 live stats
    }

@app.route('/data', methods=['GET'])
def data():
    return jsonify(get_system_info())

@app.route('/stress', methods=['POST'])
def stress_cpu():
    try:
        subprocess.Popen(["stress-ng", "--cpu", "4", "--timeout", "20s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({"message": "CPU stress test started!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
