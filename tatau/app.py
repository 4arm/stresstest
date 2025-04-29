from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/start-test', methods=['POST'])
def start_test():
    data = request.get_json()
    device_ip = data.get('device_ip')

    try:
        # Example: simple ping test, replace with iperf3 if you want
        result = subprocess.run(
            ['ping', '-c', '4', device_ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({'status': 'success', 'output': result.stdout})
        else:
            return jsonify({'status': 'error', 'output': result.stderr})

    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'output': 'Test timed out.'})
    except Exception as e:
        return jsonify({'status': 'error', 'output': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
