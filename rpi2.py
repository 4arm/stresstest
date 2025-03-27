from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import socket
import time
import shlex

app = Flask(__name__)
CORS(app)

# Get device hostname and IP
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Network speed tracking
prev_net_io = psutil.net_io_counters()
prev_time = time.time()

def get_system_info():
    global prev_net_io, prev_time
    
    # CPU Temperature Handling
    try:
        temp = psutil.sensors_temperatures().get('cpu_thermal', [{}])[0].get('current', "N/A")
    except:
        temp = "N/A"

    # Real-time Network Speed Calculation
    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    
    time_diff = current_time - prev_time if current_time != prev_time else 1
    net_speed = round(((current_net_io.bytes_sent + current_net_io.bytes_recv) - 
                       (prev_net_io.bytes_sent + prev_net_io.bytes_recv)) / (1024 * 1024 * time_diff), 2)
    
    prev_net_io = current_net_io
    prev_time = current_time

    return {
        "hostname": hostname,
        "ip": ip_address,
        "cpu_usage": psutil.cpu_percent(),
        "ram_used": psutil.virtual_memory().used // (1024 * 1024),  # Convert to MB
        "temperature": temp,
        "network_speed": net_speed  # Real-time speed in MB/s
    }

@app.route('/data', methods=['GET'])
def data():
    return jsonify(get_system_info())

@app.route('/start_test', methods=['POST'])
def start_test():
    data = request.get_json()
    test_type = data.get("test_type")

    if test_type == "RAM":
        ram_size = data.get("ram_size", "100M")
        iterations = data.get("iterations", "1")
        cmd = f"memtester {ram_size} {iterations}"
    else:
        return jsonify({"error": "Invalid test type"}), 400

    try:
        result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
        return jsonify({"output": result.stdout if result.stdout else result.stderr})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
