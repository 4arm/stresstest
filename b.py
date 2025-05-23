import os
import signal
import subprocess
from flask import Flask, jsonify
import json
from flask_cors import CORS

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
