from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess

app = Flask(__name__)
CORS(app)

def get_system_info():
    cpu_usage = psutil.cpu_percent(interval=1)

    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        if "cpu_thermal" in temps:
            temp = temps["cpu_thermal"][0].current
        elif "coretemp" in temps:
            temp = temps["cpu_thermal"][0].current

    except Exeption as e:
        print_(f"Temperature error: {e}")
        temp = "N/A"

    ram_info = psutil.virtual_memory()
    ram_free = ram_info.available / (1024 * 1024)  # Convert to MB

    net_info = psutil.net_io_counters()
    net_speed = (net_info.bytes_sent + net_info.bytes_recv) / (1024 * 1024)  # Convert to MB

    return {
        "cpu_usage": cpu_usage,
        "temperature": temp,
        "ram_space": ram_free,
        "network_speed": round(net_speed, 2)
    }

@app.route("/data")
def data():
    return jsonify(get_system_info())

@app.route("/start_test", methods=["POST"])
def start_test():
    try:
        # Run memtester with 50MB memory for 1 iteration
        result = subprocess.run(["memtester", "50M", "1"], capture_output=True, text=True)
        return jsonify({"status": "Test completed", "output": result.stdout})
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

