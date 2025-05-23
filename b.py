import os
import signal
import subprocess
from flask import Flask, send_file, jsonify, request
import json
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Track the external process globally
process = None

@app.route('/packets')
def get_packets():
    try:
        with open('packets.json') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_test', methods=['POST'])
def start_test():
    global process
    if process is None or process.poll() is not None:
        try:
            process = subprocess.Popen(['sudo', 'python3', 'a.py'])
            return jsonify({'status': 'started'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'already running'})

@app.route('/stop_test', methods=['POST'])
def stop_test():
    global process
    if process and process.poll() is None:
        try:
            os.kill(process.pid, signal.SIGTERM)
            process = None
            return jsonify({'status': 'stopped'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'not running'})


PACKETS_DIR = "packets"
EXCEL_FILE = "packet_database.xlsx"

@app.route("/get_excel")
def get_excel():
    return send_file(EXCEL_FILE, as_attachment=True)

@app.route("/list_logs")
def list_logs():
    if not os.path.exists(EXCEL_FILE):
        return jsonify([])

    df = pd.read_excel(EXCEL_FILE)
    logs = df.to_dict(orient="records")
    return jsonify(logs)

@app.route("/get_log")
def get_log():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "Invalid path"}), 400
    with open(path, "r") as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
