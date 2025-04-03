from flask import Flask, render_template, jsonify
import subprocess
import threading

app = Flask(__name__)

# Function to run iperf3 test on RPI1
def run_iperf_test():
    # Run the iperf3 test on RPI1 (192.168.0.20)
    result = subprocess.check_output(["iperf3", "-c", "192.168.0.20", "-f", "m", "-t", "10"], text=True)
    return result

# Route to display the main page with test results
@app.route('/')
def index():
    return render_template('index.html')

# Route to start the test and get results
@app.route('/start_test')
def start_test():
    # Run the test in a separate thread so the server remains responsive
    def test():
        results = run_iperf_test()
        return results

    # Start the test and return results asynchronously
    test_thread = threading.Thread(target=test)
    test_thread.start()
    return jsonify({"status": "Test started. Please wait for results."})

# Route to retrieve the latest test results (this could be extended to store results)
@app.route('/test_results')
def test_results():
    # Run the iperf3 test and get the result
    results = run_iperf_test()
    return jsonify({"test_results": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
