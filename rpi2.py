from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import socket
import subprocess

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

def get_system_info():
    """Collects system metrics from Raspberry Pi."""
    cpu_usage = psutil.cpu_percent(interval=1)

    # Get temperature
    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        if "cpu_thermal" in temps:
            temp = temps["cpu_thermal"][0].current
        elif "coretemp" in temps:
            temp = temps["coretemp"][0].current
    except Exception as e:
        print(f"Temperature Error: {e}")

    ram = psutil.virtual_memory()
    net_info = psutil.net_io_counters()
    
    return {
        "hostname": socket.gethostname(),
        "ip": request.remote_addr,
        "cpu_usage": cpu_usage,
        "temperature": temp,
        "ram_total": round(ram.total / (1024 * 1024), 2),
        "ram_used": round(ram.used / (1024 * 1024), 2),
        "ram_free": round(ram.available / (1024 * 1024), 2),
        "network_speed": round((net_info.bytes_sent + net_info.bytes_recv) / (1024 * 1024), 2)
    }

@app.route("/data", methods=["GET"])
def data():
    return jsonify(get_system_info())

@app.route("/start_test", methods=["POST"])
def start_test():
    """Handles stress tests based on host request."""
    data = request.json
    test_type = data.get("test_type")

    if test_type == "RAM":
        ram_size = data.get("ram_size", "100M")
        iterations = data.get("iterations", "1")
        command = f"memtester {ram_size} {iterations}"
    elif test_type == "CPU":
        duration = data.get("duration", "10")
        command = f"stress --cpu 4 --timeout {duration}"
    elif test_type == "DISK":
        file_size = data.get("size", "100M")
        duration = data.get("duration", "10")
        command = f"dd if=/dev/zero of=/tmp/testfile bs={file_size} count=1 && sleep {duration} && rm /tmp/testfile"
    else:
        return jsonify({"status": "error", "message": "Invalid test type"})

    try:
        output = subprocess.getoutput(command)
        return jsonify({"status": "success", "output": output})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
