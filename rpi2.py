from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS
import psutil
import subprocess
import socket
import time
import os
import json

app = Flask(__name__)
CORS(app)

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
RESULT_FILE = "result.json"
rpi1 = "172.18.18.20"
rpi2 = "172.18.18.50"

prev_net_io = psutil.net_io_counters()
prev_time = time.time()
stress_running = False
stress_report = None
network_running = False
network_report = None

def get_temperature():
    try:
        sensors = psutil.sensors_temperatures()
        for key in sensors:
            if sensors[key]:
                return sensors[key][0].current
    except Exception:
        pass
    return "Unavailable"

def get_throughput():
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE, 'r') as f:
                result = json.load(f)
                bps = result['end']['sum_received']['bits_per_second']
                mbps = round(bps / 1_000_000, 2)
                return mbps
        except Exception as e:
            return str(e)
    else:
        return "Result file not found."

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
        "stress_running": stress_running,
        "network_running": network_running,
        "throughput": get_throughput()
    }

@app.route('/data', methods=['GET'])
def data():
    return jsonify(get_system_info())

@app.route('/stress', methods=['POST'])
def stress_test():
    global stress_running, stress_report

    if stress_running:
        return jsonify({"message": "Stress test is already running"}), 400

    data = request.get_json()
    duration = int(data.get("duration", 20))

    start_stats = get_system_info()

    try:
        stress_running = True
        subprocess.Popen(["stress-ng", "--cpu", "4", "--timeout", f"{duration}s"])
        time.sleep(duration)

        end_stats = get_system_info()

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
    
@app.route('/stress_result', methods=['GET'])
def get_stress_result():
    return jsonify(stress_report)

@app.route('/stop_stress', methods=['POST'])
def stop_stress():
    global stress_running, network_running

    if not stress_running | network_running:
        return jsonify({"message": "No stress test is running"}), 400

    try:
        subprocess.run(["pkill", "-f", "stress-ng"])
        subprocess.run(["pkill", "-f", "iperf3"])
        stress_running = False
        network_running = False
        return jsonify({"message": "Stress test stopped successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/report', methods=['GET'])
def get_report():
    if stress_report:
        return jsonify(stress_report)
    return jsonify({"message": "No stress test report available"}), 404

@app.route('/test_network', methods=['POST'])
def run_network_test():
    global network_running, network_report

    if network_running:
        return jsonify({"message": "Network test is already running"}), 400

    data = request.get_json()
    networkDuration = int(data.get("networkDuration", 20))

    try:
        network_running = True
        with open(RESULT_FILE, "w") as outfile:
            subprocess.Popen(
                ["iperf3", "-c", rpi2, "-t", str(networkDuration), "-J"],
                stdout=outfile
            )

        time.sleep(networkDuration)  # Wait for iperf3 to finish
        network_running = False
        return jsonify({"status": "success", "message": "Network test completed."})

    except Exception as e:
        network_running = False
        return jsonify({"status": "error", "message": str(e)})


@app.route('/get-result', methods=['GET'])
def getresult():
    return jsonify({"throughput": get_throughput()})

@app.route('/network_metrics', methods=['GET'])
def get_network_metrics():
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE, 'r') as f:
                result = json.load(f)
                summary = result.get("end", {}).get("sum_received", {})
                sender = result.get("end", {}).get("sum_sent", {})

                throughput_mbps = round(summary.get("bits_per_second", 0) / 1_000_000, 2)
                retransmits = sender.get("retransmits", "Unavailable")
                rtt_ms = round(result.get("end", {}).get("streams", [{}])[0].get("receiver", {}).get("mean_rtt", 0) / 1000, 2)
                cpu_utilization = result.get("end", {}).get("cpu_utilization_percent", {}).get("remote_total")
                return jsonify({
                    "client_ip": result.get("start", {}).get("connected", [{}])[0].get("local_host"),
                    "server_ip": result.get("start", {}).get("connected", [{}])[0].get("remote_host"),
                    "timestamp": result.get("start", {}).get("timestamp", {}).get("time"),
                    "sent_bytes": summary.get("bytes", 0),
                    "received_bytes": summary.get("bytes", 0),
                    "cpu_utilization": round(cpu_utilization, 2),
                    "throughput_mbps": throughput_mbps,
                    "retransmits": retransmits,
                    "rtt_ms": rtt_ms
                })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": "Result file not found."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)