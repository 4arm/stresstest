import subprocess
import socketio
import time

SERVER_URL = "http://172.18.18.2:5000"  # Host Flask server
RPI2_IP = "192.168.0.50"  # Target RPI2
HOST_IP = "172.18.18.2"  # Target Host
sio = socketio.Client()

def run_iperf(target_ip):
    """Run iPerf3 test and extract the speed."""
    result = subprocess.run(
        ["iperf3", "-c", target_ip, "-t", "2", "-J"],
        capture_output=True, text=True
    )
    try:
        json_data = json.loads(result.stdout)
        speed_mbps = json_data["end"]["sum_received"]["bits_per_second"] / 1e6  # Convert to Mbps
        return round(speed_mbps, 2)
    except (KeyError, json.JSONDecodeError):
        return 0

def send_results():
    while True:
        speed_rpi2 = run_iperf(RPI2_IP)
        speed_host = run_iperf(HOST_IP)
        
        data = {
            "speed_rpi2": speed_rpi2,
            "speed_host": speed_host
        }
        print("Sending:", data)
        sio.emit('iperf_result', data)
        time.sleep(5)  # Run every 5 seconds

try:
    sio.connect(SERVER_URL)
    send_results()
except Exception as e:
    print("Failed to connect:", e)
