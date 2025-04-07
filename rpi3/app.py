from flask import Flask, render_template, request  # <-- Add this import
from flask_socketio import SocketIO, emit
import subprocess
import threading
import re

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

stop_events = {}

@app.route('/')
def index():
    return render_template('index.html')

def ping_device(target_ip, sid):
    stop_event = stop_events[sid] = threading.Event()
    process = subprocess.Popen(["ping", target_ip], stdout=subprocess.PIPE, text=True)
    online = False

    for line in process.stdout:
        if stop_event.is_set():
            break

        line = line.strip()
        socketio.emit('ping_output', {'data': line}, room=sid)

        match = re.search(r'time=([\d.]+) ms', line)
        if match:
            latency = float(match.group(1))
            online = True
            socketio.emit('latency_data', {'latency': latency}, room=sid)

        if "100% packet loss" in line or "Destination Host Unreachable" in line:
            socketio.emit('status', {'online': False}, room=sid)

    process.terminate()
    socketio.emit('status', {'online': online}, room=sid)

@socketio.on('start_ping')
def handle_start_ping(data):
    sid = request.sid
    target_ip = data.get('ip', '8.8.8.8')
    threading.Thread(target=ping_device, args=(target_ip, sid)).start()

@socketio.on('stop_ping')
def handle_stop_ping():
    sid = request.sid
    if sid in stop_events:
        stop_events[sid].set()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
