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
stress_running = False
stress_report = None  # Store the last stress test report

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
        "stress_running": stress_running
    }

@app.route('/data', methods=['GET'])
def data():
    """Return system info"""
    return jsonify(get_system_info())

@app.route('/stress', methods=['POST'])
def stress_test():
    """Start stress-ng CPU test with user-defined duration"""
    global stress_running, stress_report

    if stress_running:
        return jsonify({"message": "Stress test is already running"}), 400

    data = request.get_json()
    duration = int(data.get("duration", 20))  # Default to 20 seconds if not provided

    # Record system stats before starting
    start_stats = get_system_info()
    
    try:
        stress_running = True
        subprocess.Popen(["stress-ng", "--cpu", "4", "--timeout", f"{duration}s"])  # Start stress test
        time.sleep(duration)  # Wait for completion
        
        # Record system stats after completion
        end_stats = get_system_info()
        
        # Generate stress test report
        stress_report = {
            "duration": duration,
            "start": {
                "cpu_usage": start_stats["cpu_usage"],
                "ram_used": start_stats["ram_used"],
                "temperature": start_stats["temperature"]
            },
            "end": {
                "cpu_usage": end_stats["cpu_usage"],
                "ram_used": end_stats["ram_used"],
                "temperature": end_stats["temperature"]
            },
            "message": "Stress test completed!"
        }

        stress_running = False
        return jsonify({"message": f"Stress test completed in {duration} seconds"}), 200
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

@app.route('/report', methods=['GET'])
def get_report():
    """Return the last stress test report"""
    if stress_report:
        return jsonify(stress_report)
    return jsonify({"message": "No stress test report available"}), 404

@app.route('/network_test', methods=['POST'])
def network_test():
    """Run network test between rpi1 and rpi2"""
    try:
        # Run iperf3 between rpi1 and rpi2
        result = subprocess.run(
            ["iperf3", "-c", "192.168.0.50", "-t", "10"],  # Test for 10 seconds
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({"error": "Network test failed", "details": result.stderr}), 500
        
        # Parse the result to extract useful data (e.g., throughput)
        output = result.stdout
        # Example of parsing throughput:
        lines = output.splitlines()
        for line in lines:
            if "sender" in line:
                throughput = line.split()[-2]  # Extract the throughput value
                break
        
        return jsonify({
            "message": "Network test completed",
            "throughput": throughput,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)