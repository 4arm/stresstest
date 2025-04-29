from datetime import datetime
from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS
import psutil
import subprocess
import socket
import time
import os
import json
import shutil

app = Flask(__name__)
CORS(app)

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
RESULT_FILE = "result.json"
rpi1 = "172.18.18.20"
rpi2 = "192.168.0.50"

prev_net_io = psutil.net_io_counters()
prev_time = time.time()
stress_running = False
stress_report = None
network_running = False
network_report = None
duration = 0
total, used, free = shutil.disk_usage("/")
cpu_test_data_store = {
    "timestamp": [],
    "cpu_usage": [],
    "temperature": [],
    "Network_speed": [],
    "disk_usage": []
}
read_speed = 0
write_speed = 0

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

def get_disk_io_speed(interval=1):
    disk_io_start = psutil.disk_io_counters()
    time.sleep(interval)
    disk_io_end = psutil.disk_io_counters()

    read_bytes = disk_io_end.read_bytes - disk_io_start.read_bytes
    write_bytes = disk_io_end.write_bytes - disk_io_start.write_bytes

    read_speed = round(read_bytes / (1024 * 1024) / interval, 2)  # MB/s
    write_speed = round(write_bytes / (1024 * 1024) / interval, 2)  # MB/s

    return read_speed, write_speed

def get_system_info():
    global prev_net_io, prev_time, stress_running, net_speed

    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    time_diff = max(current_time - prev_time, 1)

    net_speed = round(((current_net_io.bytes_sent + current_net_io.bytes_recv) -
                       (prev_net_io.bytes_sent + prev_net_io.bytes_recv)) / (1024 * 1024 * time_diff), 2)

    prev_net_io = current_net_io
    prev_time = current_time
    system_info = {
        "status": "online",
        "hostname": hostname,
        "ip": ip_address,
        "cpu_usage": psutil.cpu_percent(),
        "ram_used": psutil.virtual_memory().used // (1024 * 1024),
        "temperature": get_temperature(),
        "network_speed": net_speed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "stress_running": stress_running,
        "network_running": network_running,
        "throughput": get_throughput(),
        "read_speed": read_speed,
        "write_speed": write_speed,
    }
    return (system_info)

def store_cpu_test_data(duration):
    global cpu_test_data_store

    cpu_test_data_store["timestamp"].clear()
    cpu_test_data_store["cpu_usage"].clear()
    cpu_test_data_store["temperature"].clear()
    cpu_test_data_store["Network_speed"].clear()
    cpu_test_data_store["disk_usage"].clear()

    for i in range(duration-1):
        cpu_usage = psutil.cpu_percent(interval=1)
        temperature = get_temperature()
        network_speed = get_system_info()["network_speed"]
        disk_usage = psutil.disk_usage('/').percent

        cpu_test_data_store["timestamp"].append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        cpu_test_data_store["cpu_usage"].append(cpu_usage)
        cpu_test_data_store["temperature"].append(temperature)
        cpu_test_data_store["Network_speed"].append(network_speed)
        cpu_test_data_store["disk_usage"].append(disk_usage)

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
        store_cpu_test_data(duration)

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

STRESS_RESULT_FILE = "stress_result.json"
def append_to_stress_result(entry):
    if os.path.exists(STRESS_RESULT_FILE):
        with open(STRESS_RESULT_FILE, 'r') as f:
            try:
                stress_result = json.load(f)
            except json.JSONDecodeError:
                stress_result = []
    else:
        stress_result = []
    stress_result.append(entry)

    with open(STRESS_RESULT_FILE, 'w') as f:
        json.dump(stress_result, f, indent=4)


@app.route('/stress_result', methods=['GET'])
def get_stress_result():
    stress_result = {"report": stress_report,
                    "data": cpu_test_data_store}
    append_to_stress_result(stress_result)
    return jsonify(stress_result)

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

ALERT_FILE = "alert.json"
def append_to_alert_log(entry):
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, 'r') as f:
            try:
                alerts = json.load(f)
            except json.JSONDecodeError:
                alerts = []
    else:
        alerts = []
    alerts.append(entry)

    with open(ALERT_FILE, 'w') as f:
        json.dump(alerts, f, indent=4)

@app.route('/alerts', methods=['GET'])
def get_alerts():
    global net_speed
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    alerts = []

    # Temperature
    cpu_temp = get_temperature()
    if cpu_temp != "Unavailable" and cpu_temp > 80:
        entry = {
            "time": current_time,
            "device": rpi1,
            "type": "Temperature",
            "message": f"High CPU temperature: {cpu_temp:.1f}°C"
        }
        append_to_alert_log(entry)

    # CPU Usage
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 90:
        entry = {
            "time": current_time,
            "device": rpi1,
            "type": "Usage",
            "message": f"High CPU usage: {cpu_usage:.1f}%"
        }
        append_to_alert_log(entry)

    # RAM Usage
    ram_usage = psutil.virtual_memory().percent
    if ram_usage > 90:
        entry = {
            "time": current_time,
            "device": rpi1,
            "type": "Usage",
            "message": f"High RAM usage: {ram_usage:.1f}%"
        }
        append_to_alert_log(entry)

    # Net Speed check (assumes net_speed is updated elsewhere)
    if net_speed > 90:
        entry = {
            "time": current_time,
            "device": rpi1,
            "type": "Net Speed",
            "message": f"High Network Speed: {net_speed:.1f} Mbps"
        }
        append_to_alert_log(entry)

    # Read the latest alert history from file
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, 'r') as f:
            try:
                alerts = json.load(f)
            except json.JSONDecodeError:
                alerts = []

    return jsonify({"alerts": alerts[-50:]}), 200

HISTORY_FILE = "history.json"
previous_stress_running = False
previous_network_running = False

def append_to_history_log(entry):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []
    history.append(entry)

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

@app.route('/history', methods=['GET'])
def get_history():
    global stress_running, network_running
    global previous_stress_running, previous_network_running

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Stress test logging
    if stress_running and not previous_stress_running:
        log = {
            "time": current_time,
            "device": rpi1,
            "type": "CPU Test",
            "message": "Stress test started"
        }
        append_to_history_log(log)
    elif not stress_running and previous_stress_running:
        log = {
            "time": current_time,
            "device": rpi1,
            "type": "CPU Test",
            "message": "Stress test stopped"
        }
        append_to_history_log(log)
    previous_stress_running = stress_running

    # Network test logging
    if network_running and not previous_network_running:
        log = {
            "time": current_time,
            "device": rpi1,
            "type": "Network Test",
            "message": "Network test started"
        }
        append_to_history_log(log)
    elif not network_running and previous_network_running:
        log = {
            "time": current_time,
            "device": rpi1,
            "type": "Network Test",
            "message": "Network test stopped"
        }
        append_to_history_log(log)
    previous_network_running = network_running

    # Read full history from file
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                full_history = json.load(f)
            except json.JSONDecodeError:
                full_history = []
    else:
        full_history = []

    return jsonify({"histories": full_history[-50:]}), 200

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