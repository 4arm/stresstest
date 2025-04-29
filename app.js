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
<<<<<<< HEAD
=======

			fetchAndUpdateChart();
>>>>>>> parent of d7ce620 (update 18/4 tambah logging system untuk alerts dan history)

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





function getStatusClass(value, warningThreshold, criticalThreshold) {
	if (value >= criticalThreshold) return "critical";
	if (value >= warningThreshold) return "warning";
	return "good";
}

setInterval(updateGauge, 2000);

let chart;


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

  let networkTest = null;

  let countdownTimer;
  let testDuration;
  
  async function runNetworkTest() {
	  const duration = document.getElementById('network-duration').value || 20;
	  const targetIp = document.getElementById('target-ip').value || '172.18.18.50';
	
	  // Set test duration
	  testDuration = parseInt(duration);
  
	  document.getElementById('network-status').innerText = 'Running...';
	  document.getElementById('network-btn').disabled = true;
	  document.getElementById('stop-network-btn').disabled = false;
	
	  // Start the countdown
	  startCountdown(testDuration);
  
	  try {
		  const response = await fetch(`http://${rpi_ip}:5000/start_network_test`, {
			  method: 'POST',
			  headers: {
				  'Content-Type': 'application/json'
			  },
			  body: JSON.stringify({ target_ip: targetIp, duration: testDuration })
		  });
  
		  const data = await response.json();
		  if (data.status === 'started') {
			  document.getElementById('networkNotification').innerText = data.message;
			  document.getElementById('network-status').innerText = 'In Progress';
		  } else {
			  document.getElementById('networkNotification').innerText = 'Failed to start test.';
			  document.getElementById('network-status').innerText = 'Idle';
			  document.getElementById('network-btn').disabled = false;
			  document.getElementById('stop-network-btn').disabled = true;
		  }
	  } catch (error) {
		  console.error('Error:', error);
		  document.getElementById('networkNotification').innerText = 'Error starting test.';
		  document.getElementById('network-status').innerText = 'Idle';
		  document.getElementById('network-btn').disabled = false;
		  document.getElementById('stop-network-btn').disabled = true;
	  }
  }
  
  async function stopTest() {
	  try {
		  const response = await fetch(`http://${rpi_ip}:5000/stop_network_test`, {
			  method: 'POST',
		  });
		  const data = await response.json();
		  if (data.status === 'stopped') {
			  document.getElementById('networkNotification').innerText = 'Test stopped.';
			  clearInterval(countdownTimer); // Stop the countdown if the test is stopped
			  document.getElementById('network-status').innerText = 'Stopped';
		  } else {
			  document.getElementById('networkNotification').innerText = data.message;
		  }
	  } catch (error) {
		  console.error('Error:', error);
	  } finally {
		  document.getElementById('network-status').innerText = 'Idle';
		  document.getElementById('network-btn').disabled = false;
		  document.getElementById('stop-network-btn').disabled = true;
	  }
  }
  
  async function fetchNetworkReport() {
	  try {
		  const response = await fetch(`http://${rpi_ip}:5000/network_test_report`);
		  const data = await response.json();
  
		  if (data.status === 'ok') {
			  const report = JSON.parse(data.result);
			  const summary = summarizeReport(report);
			  document.getElementById('network-report').innerHTML = `
				  <h3>Network Test Summary</h3>
				  <pre>${summary}</pre>
			  `;
			  document.getElementById('network-status').innerText = 'Finished';
		  } else {
			  document.getElementById('networkNotification').innerText = data.message;
		  }
	  } catch (error) {
		  console.error('Error:', error);
		  document.getElementById('networkNotification').innerText = 'Error fetching report.';
	  }
  }
  
  // Function to start the countdown
  function startCountdown(duration) {
	  let timeLeft = duration;
	  const countdownDisplay = document.getElementById('countdown-timer');
	  
	  countdownTimer = setInterval(() => {
		  const minutes = Math.floor(timeLeft / 60);
		  const seconds = timeLeft % 60;
		  countdownDisplay.innerText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
		  
		  if (timeLeft <= 0) {
			  clearInterval(countdownTimer); // Stop the countdown when the time is up
			  fetchNetworkReport(); // Automatically fetch the report when the test finishes
			  document.getElementById('network-status').innerText = 'Finished';
		  } else {
			  timeLeft--;
		  }
	  }, 1000);
  }
  
  function summarizeReport(report) {
	  const summary = [];

	  console.log('Full report:', report);

  
	  // Ensure 'end' and 'sum' exist before accessing them
	  if (report.end && report.end.sum) {
		  // Summary of bandwidth
		  if (report.end.sum.received_bps) {
			  const bandwidth = report.end.sum.received_bps / 1e6; // Convert to Mbps
			  summary.push(`Total Bandwidth: ${bandwidth.toFixed(2)} Mbps`);
		  }
  
		  // Summary of latency (if available)
		  if (report.end.sum.hasOwnProperty('jitter_ms')) {
			  const jitter = report.end.sum.jitter_ms;
			  summary.push(`Average Jitter: ${jitter.toFixed(2)} ms`);
		  }
  
		  // Summary of retransmissions
		  if (report.end.sum.hasOwnProperty('retransmits')) {
			  const retransmits = report.end.sum.retransmits;
			  summary.push(`Retransmissions: ${retransmits}`);
		  }
  
		  // TCP connection stats (if available)
		  if (report.end.sum.hasOwnProperty('tcp_congestion')) {
			  const congestion = report.end.sum.tcp_congestion;
			  summary.push(`TCP Congestion: ${congestion}`);
		  }
	  }
  
	  // If there are multiple streams, summarize their results
	  if (report.streams) {
		  report.streams.forEach((stream, index) => {
			  if (stream.sender) {
				  const sender = stream.sender;
				  const bandwidth = sender.bits_per_second / 1e6; // Convert to Mbps
				  summary.push(`Stream ${index + 1}: Bandwidth: ${bandwidth.toFixed(2)} Mbps`);
			  }
		  });
	  }
  
	  // Check if we have any other interesting data
	  if (report.start && report.start.timestamp) {
		const timestamp = report.start.timestamp;
		if (timestamp.timesecs) {  // iperf3 JSON usually has 'timesecs'
			const testStartTime = new Date(timestamp.timesecs * 1000).toLocaleString();
			summary.push(`Test Start Time: ${testStartTime}`);
		} else {
			summary.push(`Test Start Time: Unknown`);
		}

	  if (report.start) {
		const local_host = report.start.connected.local_host;
		const remote_host = report.start.connectec.remote_host;
		summary.push(`Tested host: ${local_host}`);
		summary.push(`Server host: ${remote_host}`);
	  }
	}
  
	  return summary.join("\n");
  }
  