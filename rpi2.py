from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import subprocess
import socket

app = Flask(__name__)
CORS(app)

def get_system_info():
    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        for key in temps:
            if temps[key]:  # Get the first available sensor
                temp = temps[key][0].current
                break
    except Exception as e:
        print(f"Temperature Error: {e}")

    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "temperature": temp,
        "ram_used": psutil.virtual_memory().used // (1024 * 1024),  # Convert to MB
        "network_speed": get_network_speed()
    }

def get_network_speed():
    try:
        output = subprocess.check_output("cat /sys/class/net/eth0/speed", shell=True)
        return output.decode().strip() + " Mbps"
    except:
        return "N/A"

@app.route('/data', methods=['GET'])
def data():
    return jsonify(get_system_info())

@app.route('/start_test', methods=['POST'])
def start_test():
    data = request.json
    test_type = data.get("test_type")

    if test_type == "RAM":
        ram_size = data.get("ram_size", "100M")
        iterations = data.get("iterations", "1")
        command = f"sudo memtester {ram_size} {iterations}"
    else:
        return jsonify({"error": "Invalid test type"}), 400

    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return jsonify({"output": output.decode()})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e.output.decode())})

def get_ip():
    return socket.gethostbyname(socket.gethostname())

if __name__ == '__main__':
    app.run(host=get_ip(), port=5000)
