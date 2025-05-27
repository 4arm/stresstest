// Get IP and hostname from URL
const urlParams = new URLSearchParams(window.location.search);
const rpi_ip = urlParams.get('ip');
const hostname = urlParams.get('hostname');

// Set IP and hostname in DOM
document.getElementById('ip').innerText = rpi_ip;
document.getElementById('hostname').innerText = hostname;

 
const temperatureGauge = document.getElementById('temperature');
const cpuUsageGauge = document.getElementById('cpu_usage');
const ramUsageGauge = document.getElementById('ram_usage');
const networkSpeedGauge = document.getElementById('network_speed');
const readSpeedGauge = document.getElementById('read_speed');
const writeSpeedGauge = document.getElementById('write_speed');

 
const stressStatus = document.getElementById("stress-status");
const networkStatus = document.getElementById("network-status");
 
 
function updateGauge() {
 
 	fetch(`http://${rpi_ip}:5000/data`)
 		.then(res => res.json())
 		.then(data => {
 			// Log the data for debugging
 			const temperature = data.temperature; // Make sure this matches your API
 			const cpu_usage = data.cpu_usage;     // Make sure this matches your API
 			const ram_used = data.ram_used;     // Make sure this matches your API
 			const network_speed = data.network_speed; // Make sure this matches your API
			const read_speed = data.read_speed; // Make sure this matches your API		
			const write_speed = data.write_speed; // Make sure this matches your API
 
 			console.log("ip: ", rpi_ip);
 
 			stressStatus.innerText = data.stress_running ? "Stress Test Running" : "No Stress Test Running";
 			stressStatus.className = `status ${data.stress_running ? "good" : "not-running"}`;
 
 			networkStatus.innerText = data.network_running ? "Network Test Running" : "No Network Test Running";
 			networkStatus.className = `status ${data.network_running ? "good" : "not-running"}`;
 
 			const maxTemp = 100;
 			const maxCPU = 100;
 			const maxRAM = 4000;
 			const maxNetworkSpeed = 1000; // Example max speed in Mbps
			const maxReadSpeed = 100000; // Example max read speed in MB/s
			const maxWriteSpeed = 100000; // Example max write speed in MB/s
 
  
 			// Calculate angles
 			const tempAngle = Math.min(180, (temperature / maxTemp) * 180);
 			const cpuAngle = Math.min(180, (cpu_usage / maxCPU) * 180);
 			const ramAngle = Math.min(180, (ram_used / maxRAM) * 180);
 			const networkAngle = Math.min(180, (network_speed / maxNetworkSpeed) * 180);
			const readAngle = Math.min(180, (read_speed / maxReadSpeed) * 180);
			const writeAngle = Math.min(180, (write_speed / maxWriteSpeed) * 180);
 
 			// Update gauge rotations
 			document.getElementById('temp-gauge').style.transform = `rotate(${tempAngle}deg)`;
 			document.getElementById('cpu-gauge').style.transform = `rotate(${cpuAngle}deg)`;
 			document.getElementById('ram-gauge').style.transform = `rotate(${ramAngle}deg)`;
 			document.getElementById('network-gauge').style.transform = `rotate(${networkAngle}deg)`;
			document.getElementById('read-speed-gauge').style.transform = `rotate(${readAngle}deg)`;
			document.getElementById('write-speed-gauge').style.transform = `rotate(${writeAngle}deg)`;
 
 			// Update text
 			temperatureGauge.innerText = `Temp ${temperature}°C`;
 			cpuUsageGauge.innerText = `CPU ${cpu_usage}%`;
 			ramUsageGauge.innerText = `RAM ${ram_used}MB`;
 			networkSpeedGauge.innerText = `Net Speed ${network_speed}Mbps`;
			readSpeedGauge.innerText = `Read Speed ${read_speed}MB/s`;
			writeSpeedGauge.innerText = `Write Speed ${write_speed}MB/s`;
 
 			// Update status classes
 			// temperatureGauge.className = getStatusClass(temperature, 70, 90);
 			// cpuUsageGauge.className = getStatusClass(cpu_usage, 70, 90);
 			// ramUsageGauge.className = getStatusClass(ram_used, 3000, 3500);
 			// networkSpeedGauge.className = getStatusClass(network_speed, 800, 900);

 
 		})
 		.catch(err => {
 		console.error("Failed to fetch data:", err);
 		});
}

function stressTest() {
 	const duration = document.getElementById("duration").value || 20;
 	const notification = document.getElementById("notification");
 	const stressButton = document.getElementById("stress-btn");
 	const stopButton = document.getElementById("stop-btn");
 
 	stressButton.disabled = true;
 	stopButton.disabled = false;
 	notification.innerText = `Stress test starting for ${duration} seconds...`;
 
 	startCountdown(duration, rpi_ip, "notification", "stress-btn", "stop-btn");
 
 	fetch(`http://${rpi_ip}:5000/stress`, {
 			method: "POST",
 			headers: { "Content-Type": "application/json" },
 			body: JSON.stringify({ duration })
 		})
 		.then(response => response.json())
 		.then(data => {
 			notification.innerText = data.message;
 		})
 		.catch(err => console.log(err));
}
 
function stopTest(ctx) {
 	const { rpi_ip, notificationId, stressBtnId, stopBtnId } = ctx;
 	const notification = document.getElementById(notificationId);
 	const stressButton = document.getElementById(stressBtnId);
 	const stopButton = document.getElementById(stopBtnId);
 
 	fetch(`http://${rpi_ip}:5000/stop_stress`, { method: "POST" })
 		.then(response => response.json())
 		.then(data => {
 			notification.innerText = "Stress test stopped!";
 			if (countdownTimers[rpi_ip]) {
 				clearInterval(countdownTimers[rpi_ip]);
 				delete countdownTimers[rpi_ip];
 			}
 			stressButton.disabled = false;
 			stopButton.disabled = true;
 		})
 		.catch(err => {
 			console.error("Error stopping test:", err);
 			notification.innerText = "Failed to stop stress test.";
 		});
}
 
let countdownTimers = {};
 
function startCountdown(duration, rpi_ip, notificationId, stressBtnId, stopBtnId) {
 	const notification = document.getElementById(notificationId);
 	let timeLeft = duration;
 
 	if (countdownTimers[rpi_ip]) {
 		clearInterval(countdownTimers[rpi_ip]);
 	}
 
 	notification.innerText = `Stress test running... ${timeLeft}s left`;
 
 	countdownTimers[rpi_ip] = setInterval(() => {
 		timeLeft--;
 
 		if (timeLeft <= 0) {
 			clearInterval(countdownTimers[rpi_ip]);
 			notification.innerText = "Stress test completed!";
 			document.getElementById(stressBtnId).disabled = false;
 			document.getElementById(stopBtnId).disabled = true;
 		} else {
 			notification.innerText = `Stress test running... ${timeLeft}s left`;
 		}
 	}, 1000);
}
 
async function fetchStressReport() {
      try {
        const response = await fetch(`http://${rpi_ip}:5000/stress_result`);
        const jsonData = await response.json();
        renderCombinedChart(jsonData);
      } catch (error) {
        console.error('Failed to fetch or render data:', error);
      }
    }

    function renderCombinedChart(data) {
      const timestamps = data.data.timestamp;
      const cpuData = data.data.cpu_usage;
      const tempData = data.data.temperature;

      const canvas = document.getElementById('combinedChart');
      if (!(canvas instanceof HTMLCanvasElement)) {
        console.error("Canvas element not found or invalid");
        return;
      }

      const ctx = canvas.getContext('2d');

      // Clear previous chart if needed
      if (window.combinedChartInstance) {
        window.combinedChartInstance.destroy();
      }

      window.combinedChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: timestamps,
          datasets: [
            {
              label: 'CPU Usage (%)',
              data: cpuData,
              borderColor: 'rgba(255, 99, 132, 1)',
              yAxisID: 'y1',
              fill: false,
              tension: 0.3
            },
            {
              label: 'Temperature (°C)',
              data: tempData,
              borderColor: 'rgba(54, 162, 235, 1)',
              yAxisID: 'y2',
              fill: false,
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          interaction: {
            mode: 'index',
            intersect: false
          },
          stacked: false,
          scales: {
            y1: {
              type: 'linear',
              position: 'left',
              title: {
                display: true,
                text: 'CPU Usage (%)'
              },
              min: 0,
              max: 100
            },
            y2: {
              type: 'linear',
              position: 'right',
              title: {
                display: true,
                text: 'Temperature (°C)'
              },
              min: 20,
              max: 80,
              grid: {
                drawOnChartArea: false
              }
            },
            x: {
              title: {
                display: true,
                text: 'Timestamp'
              },
              ticks: {
                maxRotation: 90,
                minRotation: 45
              }
            }
          }
        }
      });
    }
 
function fetchNetworkReport() {
 	const reportElement = document.getElementById("network-report");
 
 	fetch(`http://${rpi_ip}:5000/network_metrics`)
 
 		.then(response => response.json())
 		.then(data => {
 			if (data.error) {
 				reportElement.innerText = `Error: ${data.error}`;
 			} else {
 				reportElement.innerHTML = `
 					<div>
 						<!-- Start Section -->
 						<div class="section">
 							<h2><i class="fas fa-play-circle"></i> Start Information</h2>
 							<div class="data" id="start-section">
 								<div>
 									<i class="fas fa-laptop"></i>
 									<p>
 										<strong>Client:</strong>
 									</p>
 									<p>${data.client_ip}</p>
 								</div>
 								<div>
 									<i class="fas fa-network-wired"></i>
 									<p>
 										<strong>Server:</strong>
 									</p>
 									<p>${data.server_ip}</p>
 								</div>
 								<div>
 									<i class="fas fa-clock"></i>
 									<p>
 										<strong>Timestamp:</strong>
 									</p>
 									<p>${data.timestamp}</p>
 								</div>
 							</div>
 							</div>
 						
 							<!-- Interval Section -->
 							<div class="section">
 							<h2><i class="fas fa-tachometer-alt"></i> Interval Performance</h2>
 							<div class="data" id="interval-section">
 								<div>
 									<i class="fas fa-arrow-alt-circle-up"></i>
 									<p><strong>Bandwidth:</strong></p>
 									<p>${data.throughput_mbps} Mbps</p>
 								</div>
 								<div>
 									<i class="fas fa-recycle"></i>
 									<p><strong>Retransmits:</strong></p>
 									<p>${data.retransmits}</p>    
 								</div>
 								<div>
 									<i class="fas fa-random"></i>
 									<p><strong>RTT:</strong></p>
 									<p>${data.rtt_ms} ms</p>    
 								</div>
 							</div>
 							</div>
 						
 							<!-- End Section -->
 							<div class="section">
 							<h2><i class="fas fa-stop-circle"></i> End Information</h2>
 							<div class="data" id="end-section">
 								<div>
 									<i class="fas fa-arrow-circle-right"></i>
 									<p><strong>Sent Bytes:</strong></p>
 									<p>${data.sent_bytes}</p>
 								</div>
 								<div>
 									<i class="fas fa-arrow-circle-left"></i>
 									<p><strong>Received Bytes:</strong></p>
 									<p>${data.received_bytes}</p>    
 								</div>
 								<div>
 									<i class="fas fa-percent"></i>
 									<p><strong>CPU Utilization:</strong></p>
 									<p>${data.cpu_utilization}%</p>    
 								</div>
 							</div>
 						</div>
 					</div>
 				`;
 			}
 		})
 		.catch(err => {
 			console.log(err);
 			reportElement.innerText = "Error fetching network test report.";
 		});
}
 
function getStatusClass(value, warningThreshold, criticalThreshold) {
 	if (value >= criticalThreshold) return "critical";
 	if (value >= warningThreshold) return "warning";
 	return "good";
}
 
setInterval(updateGauge, 2000);
 
function toggleDropdown() {
 	const dropdown = document.getElementById("dropdownMenu");
 	dropdown.style.display = dropdown.style.display === "flex" ? "none" : "flex";
}
 
   // Close dropdown when clicking outside
window.addEventListener("click", function(e) {
 	const btn = document.querySelector(".monitor-dash-btn");
 	const dropdown = document.getElementById("dropdownMenu");
 	if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
 	  dropdown.style.display = "none";
 	}
});

let countdownInterval;
let remainingTime = 0;

function runNetworkTest() {
    const duration = parseInt(document.getElementById('network-duration').value) || 20;
    const targetIp = document.getElementById('target-ip').value || '172.18.18.50';

    if (!targetIp) {
      alert("Please enter a target IP address.");
      return;
    }

    document.getElementById('network-status').textContent = "Running...";
    document.getElementById('networkNotification').textContent = `Running test to ${targetIp}`;
    document.getElementById('stop-network-btn').disabled = false;

    // Start countdown timer
    remainingTime = duration;
    updateCountdown();
    countdownInterval = setInterval(() => {
      remainingTime--;
      updateCountdown();
      if (remainingTime <= 0) clearInterval(countdownInterval);
    }, 1000);

    fetch(`http://${rpi_ip}:5000/start_network_test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_ip: targetIp, duration: duration })
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById('networkNotification').textContent = data.message;
    })
    .catch(err => {
      clearInterval(countdownInterval);
      document.getElementById('network-status').textContent = "Error";
      document.getElementById('networkNotification').textContent = "Failed to start test.";
    });
  }

  function stopNetworkTest() {
    fetch(`http://${rpi_ip}:5000/stop_network_test`, {
      method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById('networkNotification').textContent = data.message || "Stopped.";
      document.getElementById('network-status').textContent = "Stopped";
      document.getElementById('stop-network-btn').disabled = true;
      clearInterval(countdownInterval);
    })
    .catch(err => {
      document.getElementById('networkNotification').textContent = "Failed to stop test.";
    });
}

function fetchNetworkReport() {
	const reportElement = document.getElementById("network-report");

	fetch(`http://${rpi_ip}:5000/network_metrics`)

		.then(response => response.json())
		.then(data => {
			if (data.error) {
				reportElement.innerText = `Error: ${data.error}`;
			} else {
				reportElement.innerHTML = `
					<div>
						<!-- Start Section -->
						<div class="section">
							<h2><i class="fas fa-play-circle"></i> Start Information</h2>
							<div class="data" id="start-section">
								<div>
									<i class="fas fa-laptop"></i>
									<p>
										<strong>Client:</strong>
									</p>
									<p>${data.client_ip}</p>
								</div>
								<div>
									<i class="fas fa-network-wired"></i>
									<p>
										<strong>Server:</strong>
									</p>
									<p>${data.server_ip}</p>
								</div>
								<div>
									<i class="fas fa-clock"></i>
									<p>
										<strong>Timestamp:</strong>
									</p>
									<p>${data.timestamp}</p>
								</div>
							</div>
							</div>
						
							<!-- Interval Section -->
							<div class="section">
							<h2><i class="fas fa-tachometer-alt"></i> Interval Performance</h2>
							<div class="data" id="interval-section">
								<div>
									<i class="fas fa-arrow-alt-circle-up"></i>
									<p><strong>Bandwidth:</strong></p>
									<p>${data.throughput_mbps} Mbps</p>
								</div>
								<div>
									<i class="fas fa-recycle"></i>
									<p><strong>Retransmits:</strong></p>
									<p>${data.retransmits}</p>    
								</div>
								<div>
									<i class="fas fa-random"></i>
									<p><strong>RTT:</strong></p>
									<p>${data.rtt_ms} ms</p>    
								</div>
							</div>
							</div>
						
							<!-- End Section -->
							<div class="section">
							<h2><i class="fas fa-stop-circle"></i> End Information</h2>
							<div class="data" id="end-section">
								<div>
									<i class="fas fa-arrow-circle-right"></i>
									<p><strong>Sent Bytes:</strong></p>
									<p>${data.sent_bytes}</p>
								</div>
								<div>
									<i class="fas fa-arrow-circle-left"></i>
									<p><strong>Received Bytes:</strong></p>
									<p>${data.received_bytes}</p>    
								</div>
								<div>
									<i class="fas fa-percent"></i>
									<p><strong>CPU Utilization:</strong></p>
									<p>${data.cpu_utilization}%</p>    
								</div>
							</div>
						</div>
					</div>
				`;
			}
		})
		.catch(err => {
			console.log(err);
			reportElement.innerText = "Error fetching network test report.";
		});
}

function updateCountdown() {
	const mins = String(Math.floor(remainingTime / 60)).padStart(2, '0');
	const secs = String(remainingTime % 60).padStart(2, '0');
	document.getElementById('countdown-timer').textContent = `${mins}:${secs}`;
}

async function fetchDevices() {
	try {
		const res = await fetch('deviceList.json');
		const devices = await res.json();
		const devicesDiv = document.getElementById("devices");
		devicesDiv.innerHTML = '';

		// Loop through the device list and create the device cards
		devices.forEach(device => {
			if (device.ip === rpi_ip) { // Only show the device matching the IP from the URL
				devicesDiv.appendChild(createDeviceCard(device));
			}
		});

	} catch (err) {
		document.getElementById("devices").innerHTML = "❌ Failed to load devices: " + err;
	}
}

// Create a card for each device
function createDeviceCard(device) {
	const div = document.createElement("div");
	div.className = "device";
	div.innerHTML = `
		<h3>${device.name} (${device.ip})</h3>
		<p><strong>Location:</strong> ${device.location}</p>
		<input type="number" id="size-${device.ip}" placeholder="Enter RAM size in MB" min="1" style="width:150px;">
		<button class="btn" onclick="runRamTest('${device.ip}')">Run RAM Test</button>
		<div class="result network-report" id="ramResult-${device.ip}">Waiting...</div>
	`;
	return div;
}

// Run RAM test for the selected device
async function runRamTest(ip) {
	const sizeInput = document.getElementById(`size-${ip}`);
	const sizeMB = parseInt(sizeInput.value);
	const resultDiv = document.getElementById(`ramResult-${ip}`);

	if (isNaN(sizeMB) || sizeMB <= 0) {
		resultDiv.innerHTML = "⚠️ Please enter a valid RAM size in MB.";
		return;
	}

	resultDiv.innerHTML = `Testing ${sizeMB} MB...`;

	try {
		// Fetch RAM test result from the backend
		const res = await fetch(`http://${ip}:5000/test_ram?size=${sizeMB}`);
		const data = await res.json();

		if (data.status === 'success') {
			resultDiv.innerHTML = `
				<strong>Requested:</strong> ${data.requested_mb} MB<br>
				<strong>Used:</strong> ${(data.used / 1e6).toFixed(2)} MB<br>
				<strong>Total:</strong> ${(data.total / 1e6).toFixed(2)} MB<br>
				<strong>Usage:</strong> ${data.percent}%<br>
				<strong>Alloc Speed:</strong> ${data.alloc_speed_sec}s<br>
				<strong>Message:</strong> ${data.message}
			`;
		} else {
			resultDiv.innerHTML = "⚠️ " + data.message;
		}
	} catch (err) {
		resultDiv.innerHTML = "❌ Request failed: " + err;
	}
}

// Call the fetchDevices function to load the specific device
fetchDevices();

async function fetchDevicess() {
	try {
		const res = await fetch('deviceList.json');
		const devices = await res.json();
		const devicesDiv = document.getElementById("diskDevices"); // Updated ID here
		devicesDiv.innerHTML = '';

		// Loop through the device list and create the device cards
		devices.forEach(device => {
			if (device.ip === rpi_ip) { // Only show the device matching the IP from the URL
				devicesDiv.appendChild(createDeviceCards(device));
			}
		});

	} catch (err) {
		document.getElementById("diskDevices").innerHTML = "❌ Failed to load devices: " + err; // Updated ID here
	}
}

// Create a card for each device
function createDeviceCards(device) {
	const div = document.createElement("div");
	div.className = "device";
	div.innerHTML = `
		<h3>${device.name} (${device.ip})</h3>
		<p><strong>Location:</strong> ${device.location}</p>
		<input type="number" id="disk-size-${device.ip}" placeholder="Enter disk size in MB" min="1" style="width:150px;">
		<button class="btn" onclick="runDiskTest('${device.ip}')">Run Disk Test</button>
		<div class="result network-report" id="diskResult-${device.ip}">Waiting...</div>
	`;
	return div;
}

// Run disk test for the selected device
async function runDiskTest(ip) {
	const sizeInput = document.getElementById(`disk-size-${ip}`);
	const sizeMB = parseInt(sizeInput.value);
	const resultDiv = document.getElementById(`diskResult-${ip}`);

	if (isNaN(sizeMB) || sizeMB <= 0) {
		resultDiv.innerHTML = "⚠️ Please enter a valid disk size in MB.";
		return;
	}

	resultDiv.innerHTML = `Testing disk speed for ${sizeMB} MB...`;

	try {
		// Fetch disk test result from the backend
		const res = await fetch(`http://${ip}:5000/test_disk?size=${sizeMB}`);
		const data = await res.json();

		if (data.status === 'success') {
			resultDiv.innerHTML = `
				<strong>Write Speed:</strong> ${data.write_speed.toFixed(2)} MB/s<br>
				<strong>Read Speed:</strong> ${data.read_speed.toFixed(2)} MB/s<br>
				<strong>Message:</strong> ${data.message}
			`;
		} else {
			resultDiv.innerHTML = "⚠️ " + data.message;
		}
	} catch (err) {
		resultDiv.innerHTML = "❌ Request failed: " + err;
	}
}

// Call the fetchDevices function to load the specific device
fetchDevicess();


