from flask import Flask, render_template
from flask_socketio import SocketIO
import subprocess
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('iperf_result')
def handle_iperf_result(data):
    print("Received iPerf3 results:", data)
    socketio.emit('update_chart', data)  # Send data to HTML frontend

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
