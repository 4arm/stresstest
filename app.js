const rpi1 = "172.18.18.20"
const rpi2 = "172.18.18.50"
const rpi3 = "192.168.120.49"

const hostnameClass = document.getElementById('hostname');
const ipClass = document.getElementById('ip');

const temperatureGauge = document.getElementById('temperature');
const cpuUsageGauge = document.getElementById('cpu_usage');
const ramUsageGauge = document.getElementById('ram_usage');
const networkSpeedGauge = document.getElementById('network_speed');
const rpi_ip = ipClass.dataset.ip;

const stressStatus = document.getElementById("stress-status");

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
        
        console.log("ip: ", rpi_ip);

        stressStatus.innerText = data.stress_running ? "Stress Test Running" : "No Stress Test Running";
        stressStatus.className = `status ${data.stress_running ? "good" : "not-running"}`;
        
        const maxTemp = 100;
        const maxCPU = 100;
        const maxRAM = 4000;
        const maxNetworkSpeed = 1000; // Example max speed in Mbps

        // Calculate angles
        const tempAngle = Math.min(180, (temperature / maxTemp) * 180);
        const cpuAngle = Math.min(180, (cpu_usage / maxCPU) * 180);
        const ramAngle = Math.min(180, (ram_used / maxRAM) * 180);
        const networkAngle = Math.min(180, (network_speed / maxNetworkSpeed) * 180);

        // Update gauge rotations
        document.getElementById('temp-gauge').style.transform = `rotate(${tempAngle}deg)`;
        document.getElementById('cpu-gauge').style.transform = `rotate(${cpuAngle}deg)`;
        document.getElementById('ram-gauge').style.transform = `rotate(${ramAngle}deg)`;
        document.getElementById('network-gauge').style.transform = `rotate(${networkAngle}deg)`;
        
        // Update text
        temperatureGauge.innerText = `Temp ${temperature}°C`;
        cpuUsageGauge.innerText = `CPU ${cpu_usage}%`;
        ramUsageGauge.innerText = `RAM ${ram_used}MB`;
        networkSpeedGauge.innerText = `Net Speed ${network_speed}Mbps`;
        hostnameClass.innerText = `${hostname}`;
        ipClass.innerText = rpi_ip;
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

  startCountdown(duration);

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

function stopStressTest() {
  const notification = document.getElementById("notification");
  const stressButton = document.getElementById("stress-btn");
  const stopButton = document.getElementById("stop-btn");

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
      .catch(err => console.log(err));
}

let countdownTimers = {};

function startCountdown(duration) {
  const notification = document.getElementById("notification");
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
          document.getElementById("stress-btn").disabled = false;
          document.getElementById("stop-btn").disabled = true;
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
                  <p>Duration: ${data.duration}s</p>
                  <p>CPU Usage: ${data.end.cpu_usage}%</p>
                  <p>Temperature: ${data.end.temperature}°C</p>
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

const options = {
  cpu: ['Stress CPU', 'Monitor CPU Temp'],
  network: ['Test Latency', 'Check Bandwidth']
};

function showOptions(type) {
  const testOptionsDiv = document.getElementById('test-options');
  const testCardDiv = document.getElementById('test-card');
  testOptionsDiv.innerHTML = '<h3>Select Test</h3>';
  testCardDiv.innerHTML = '';

  options[type].forEach(test => {
    const btn = document.createElement('button');
    btn.textContent = test;
    btn.className = 'btn';
    btn.onclick = () => showCard(test);
    testOptionsDiv.appendChild(btn);
  });
}

function showCard(testName) {
  const testCardDiv = document.getElementById('test-card');
  testCardDiv.innerHTML = `
    <div class="card">
      <h4>${testName}</h4>
      <p>This is where test info or live results will appear for "${testName}".</p>
    </div>
  `;
}

setInterval(updateGauge, 2000);
