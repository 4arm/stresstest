const hostnameClass = document.getElementById('hostname');
const ipClass = document.getElementById('ip');

const temperatureGauge = document.getElementById('temperature');
const cpuUsageGauge = document.getElementById('cpu_usage');
const ramUsageGauge = document.getElementById('ram_usage');
const networkSpeedGauge = document.getElementById('network_speed');
const diskUsagePercentageGauge = document.getElementById('disk_usage');
const rpi_ip = ipClass.dataset.ip;

const stressStatus = document.getElementById("stress-status");
const networkStatus = document.getElementById("network-status");

const CPUtest = {
	rpi_ip: rpi_ip,
	notificationId: "notification",
	stressBtnId: "stress-btn",
	stopBtnId: "stop-btn"
};

const networkTest = {
	rpi_ip: rpi_ip,
	notificationId: "networkNotification",
	stressBtnId: "network-btn",
	stopBtnId: "stop-network-btn"
};

function updateGauge() {

	fetch(`http://${rpi_ip}:5000/data`)
		.then(res => res.json())
		.then(data => {
			// Log the data for debugging
			const temperature = data.temperature; // Make sure this matches your API
			const cpu_usage = data.cpu_usage;     // Make sure this matches your API
			const ram_used = data.ram_used;     // Make sure this matches your API
			const network_speed = data.network_speed; // Make sure this matches your API
			const hostname = data.hostname; // Make sure this matches your API
			const totalDiskUsage = data.disk_usage.total;
			const usedDiskUsage = data.disk_usage.used;
			const diskUsagePercentage = ((usedDiskUsage / totalDiskUsage) * 100).toFixed(2);

			console.log("ip: ", rpi_ip);

			stressStatus.innerText = data.stress_running ? "Stress Test Running" : "No Stress Test Running";
			stressStatus.className = `status ${data.stress_running ? "good" : "not-running"}`;
			
			networkStatus.innerText = data.network_running ? "Network Test Running" : "No Network Test Running";
			networkStatus.className = `status ${data.network_running ? "good" : "not-running"}`;

			const maxTemp = 100;
			const maxCPU = 100;
			const maxRAM = 4000;
			const maxNetworkSpeed = 1000; // Example max speed in Mbps
			const maxDiskUsage = 100; // Example max disk usage in percentage

			// Calculate angles
			const tempAngle = Math.min(180, (temperature / maxTemp) * 180);
			const cpuAngle = Math.min(180, (cpu_usage / maxCPU) * 180);
			const ramAngle = Math.min(180, (ram_used / maxRAM) * 180);
			const networkAngle = Math.min(180, (network_speed / maxNetworkSpeed) * 180);
			const diskAngle = Math.min(180, (diskUsagePercentage / maxDiskUsage) * 180);

			// Update gauge rotations
			document.getElementById('temp-gauge').style.transform = `rotate(${tempAngle}deg)`;
			document.getElementById('cpu-gauge').style.transform = `rotate(${cpuAngle}deg)`;
			document.getElementById('ram-gauge').style.transform = `rotate(${ramAngle}deg)`;
			document.getElementById('network-gauge').style.transform = `rotate(${networkAngle}deg)`;
			document.getElementById('disk-gauge').style.transform = `rotate(${diskAngle}deg)`;
			
			// Update text
			temperatureGauge.innerText = `Temp ${temperature}°C`;
			cpuUsageGauge.innerText = `CPU ${cpu_usage}%`;
			ramUsageGauge.innerText = `RAM ${ram_used}MB`;
			networkSpeedGauge.innerText = `Net Speed ${network_speed}Mbps`;
			hostnameClass.innerText = `${hostname}`;
			ipClass.innerText = rpi_ip;
			diskUsagePercentageGauge.innerText = `Disk Usage ${diskUsagePercentage}%`;

			fetchAndUpdateChart();

			// if(temperature >= 60){
			// 	alert("Temperature is too high!" + temperature + "°C");
			// }
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

function fetchStressReport() {
	const reportElement = document.getElementById("stress-report");

	fetch(`http://${rpi_ip}:5000/stress_result`)
		.then(response => response.json())
		.then(data => {
			if (data.error) {
				reportElement.innerText = `Error: ${data.error}`;
			} else {
				reportElement.innerHTML = `
					<h3>Stress Test Report for ${rpi_ip}</h3>
					<p>Duration: ${data.report.duration}s</p>
					<p>CPU Usage: ${data.report.end.cpu_usage}%</p>
					<p>Temperature: ${data.report.end.temperature}°C</p>
				`;
			}
		})
		.catch(err => {
			console.log(err);
			reportElement.innerText = "Error fetching stress test report.";
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

function runNetworkTest() {
	const networkNotification = document.getElementById("networkNotification");
	const networkButton = document.getElementById("network-btn");
	const stopNetworkButton = document.getElementById("stop-network-btn");
	const networkDuration = document.getElementById("network-duration").value || 10; // Default to 20 seconds
	const duration = parseInt(networkDuration.value) || 20; // Default to 20 seconds

	networkButton.disabled = true;
	stopNetworkButton.disabled = false;
	networkNotification.innerText = `Network test starting for ${networkDuration.value} seconds...`;

	startCountdown(duration, rpi_ip, "networkNotification", "network-btn", "stop-network-btn");

	fetch(`http://${rpi_ip}:5000/test_network`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ networkDuration: duration })
		})
		.then(response => response.json())
		.then(data => {
			networkNotification.innerText = data.message;
		})
		.catch(err => console.log(err));
}

function getStatusClass(value, warningThreshold, criticalThreshold) {
	if (value >= criticalThreshold) return "critical";
	if (value >= warningThreshold) return "warning";
	return "good";
}

setInterval(updateGauge, 2000);

let chart;

async function fetchAndUpdateChart() {
  try {
    const response = await fetch(`http://${rpi_ip}:5000/stress_result`); // your API endpoint
    const json = await response.json();
    const data = json.data;

    const labels = data.timestamp.map(t => new Date(t).toLocaleTimeString());

    const datasets = [
      {
        label: 'CPU Usage (%)',
        data: data.cpu_usage,
        borderColor: 'rgba(75, 192, 192, 1)',
        fill: false
      },
      {
        label: 'Temperature (°C)',
        data: data.temperature,
        borderColor: 'rgba(255, 99, 132, 1)',
        fill: false
      }
    ];

    if (!chart) {
      const ctx = document.getElementById('summaryChart').getContext('2d');
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: datasets
        },
        options: {
          responsive: true,
          animation: false,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Time'
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Value'
              }
            }
          },
          plugins: {
            legend: {
              display: true,
              position: 'bottom'
            }
          }
        }
      });
    } else {
      chart.data.labels = labels;
      chart.data.datasets.forEach((dataset, index) => {
        dataset.data = datasets[index].data;
      });
      chart.update();
    }

  } catch (error) {
    console.error("Error fetching or updating chart data:", error);
  }
}

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