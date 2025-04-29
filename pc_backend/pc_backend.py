from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# List of devices
# Change these IPs to match your Raspberry Pi IPs
DEVICES = {
    "RPi1": "172.18.18.20",
    "RPi2": "172.18.18.50",
    "RPi3": "192.168.0.60",
}

@app.route('/')
def index():
    return render_template('index.html', devices=DEVICES)

@app.route('/start-test', methods=['POST'])
def start_test():
    data = request.json
    source_device = data.get("source_device")
    target_device = data.get("target_device")
    duration = data.get("duration", 10)

    source_ip = DEVICES.get(source_device)
    target_ip = DEVICES.get(target_device)

    if not source_ip or not target_ip:
        return jsonify({"error": "Invalid device names"}), 400

    try:
        # Sending the test request to the Raspberry Pi server
        response = requests.post(f"http://{source_ip}:6000/start-test", json={
            "target_ip": target_ip,
            "duration": duration
        }, timeout=duration+10)

        # Return the test result from the Raspberry Pi server
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to get test result from source device"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout: The device didn't respond in time"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
