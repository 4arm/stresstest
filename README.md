Stress Test Environment
A complete system to stress test CPU, RAM, storage, and network performance for Raspberry Pi and other client devices.
Designed for reliability analysis, peak performance evaluation, and temperature monitoring.

📋 Requirements
Host (Monitoring Machine)
Windows 11 (or compatible Windows OS)

Python 3.10+

pip installed

Libraries:

Flask (for Web GUI)

Plotly (for real-time chart visualization)

psutil (for monitoring local resources)

paramiko (for SSH connections if needed)

Client (Device to Stress Test)
Raspberry Pi (tested on 4B) / Linux-based devices

Ubuntu 20.04+ / Raspberry Pi OS

Python 3 installed

Stress tools installed:

stress

iperf3

sysbench

SSH server enabled (for remote execution)

Network
Stable LAN with minimum 1Gbps bandwidth (tested on TP-Link Omada switch)

Static IP addressing preferred

⚙️ Installation
1. Clone this repository
bash
Copy
Edit
git clone https://github.com/yourusername/stress-test-environment.git
cd stress-test-environment
2. Install Python dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Setup Clients
SSH into the Raspberry Pi / Client device and install necessary tools:

bash
Copy
Edit
sudo apt update
sudo apt install stress iperf3 sysbench
Ensure SSH service is enabled:

bash
Copy
Edit
sudo systemctl enable ssh
sudo systemctl start ssh
🚀 How to Use
1. Start the Web Application
bash
Copy
Edit
python app.py
The web app will be available at:

arduino
Copy
Edit
http://localhost:5000
2. Select Test Modules
From the web interface, you can run:

CPU Stress Test

RAM Stress Test

Disk I/O Stress Test

Network Performance Test (bandwidth & latency)

3. Running Tests
Choose the client device IP.

Select the test type and parameters.

Click Start Test.

Monitor real-time graphs and logs directly on the web page.

4. Exporting Results
After test completion, you can download a:

Full Test Log

Summary Report (Peak CPU %, Highest Temperature, Pass/Fail Status)

🔧 Adjustment Notes (for Specific Devices)

Device	Adjustment Needed
Raspberry Pi (Pi 4B)	Monitor CPU temperature carefully; add active cooling if needed.
Raspberry Pi Zero / W	Reduce stress load (lower thread counts) to prevent thermal throttling.
Older Devices	Use lower stress parameters to avoid unexpected shutdowns.
Non-Pi Linux Devices	Validate installed tools (stress, iperf3, sysbench) before starting.
Custom Stress Parameters:

In config.py, you can adjust:

CPU load (default 4 threads)

RAM stress size (default 256MB)

I/O test size

Network bandwidth limits

Example (for Pi Zero):

python
Copy
Edit
CPU_THREADS = 1
MEMORY_STRESS_SIZE = '64M'
🧪 Test Environment Setup (Reference)

Component	Description
Host	Windows 11 Laptop/Desktop
Switch	TP-Link Omada 1Gbps
Clients	Raspberry Pi 4B, Raspberry Pi 2, Pi Zero W
Network Topology	Star network with static IP addressing
📄 License
MIT License
Feel free to modify and use for your own testing environments.

✨ Future Improvements
Remote client auto-discovery

Scheduled testing

More detailed hardware profiling (GPU, thermal zones)
