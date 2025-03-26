from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import threading

app = Flask(__name__)
CORS(app)

def get_system_info():
    cpu_usage = psutil.cpu_percent(interval=1)

    # Temperature detection
    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        if "cpu_thermal" in temps:
            temp = temps["cpu_thermal"][0].current
        elif "coretemp" in temps:
            temp = temps["coretemp"][0].current
    except Exception as e:
        print(f"Temperature Error: {e}")

    # RAM detection
    try:
        ram_info = psutil.virtual_memory()
        ram_total = ram_info.total / (1024 * 1024)  # MB
        ram_used = ram_info.used / (1024 * 1024)
        ram_free = ram_info.available / (1024 * 1024)
    except Exception as e:
        print(f"RAM Error: {e}")
        ram_total = ram_used = ram_free = "N/A"

    # Network speed
    net_info = psutil.net_io_counters()
    net_speed = (net_info.bytes_sent + net_info.bytes_recv) / (1024 * 1024)  # MB

    return {
        "cpu_usage": cpu_usage,
        "temperature": temp,
        "ram_total": ram_total,
        "ram_used": ram_used,
        "ram_free": ram_free,
        "network_speed": round(net_speed, 2)
    }

@app.route("/data")
def data():
    return jsonify(get_system_info())

def run_memtest(ram_size, iterations):
    return subprocess.run(["memtester", ram_size, str(iterations)], capture_output=True, text=True).stdout

def run_cputest(duration):
    return subprocess.run(["stress", "--cpu", "4", "--timeout", str(duration)], capture_output=True, text=True).stdout

def run_disktest(size, duration):
    return subprocess.run(["stress", "--hdd", "1", "--hdd-bytes", size, "--timeout", str(duration)], capture_output=True, text=True).stdout

@app.route("/start_test", methods=["POST"])
def start_test():
    try:
        data = request.json
        test_type = data.get("test_type", "RAM")  # RAM, CPU, or DISK

        if test_type == "RAM":
            ram_size = data.get("ram_size", "50M")
            iterations = data.get("iterations", "1")
            output = run_memtest(ram_size, iterations)

        elif test_type == "CPU":
            duration = data.get("duration", "10")  # Seconds
            output = run_cputest(duration)

        elif test_type == "DISK":
            size = data.get("size", "10M")  # File size
            duration = data.get("duration", "10")  # Seconds
            output = run_disktest(size, duration)

        else:
            return jsonify({"status": "Error", "error": "Invalid test type"})

        return jsonify({"status": "Test completed", "output": output})

    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
