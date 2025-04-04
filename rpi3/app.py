from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess
import threading

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')  # 👈 Important fix!

@app.route('/')
def index():
    return render_template('index.html')

def ping_device(target_ip):
    process = subprocess.Popen(["ping", target_ip], stdout=subprocess.PIPE, text=True)
    for line in process.stdout:
        socketio.emit('ping_output', {'data': line.strip()})
    process.terminate()

@socketio.on('start_ping')
def handle_start_ping(data):
    target_ip = data.get('ip', '8.8.8.8')
    threading.Thread(target=ping_device, args=(target_ip,)).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
