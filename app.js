const temperatureGauge = document.getElementById('temperature');
const cpu_usageGuage = document.getElementById('cpu_usage');


function updateGauge() {
    fetch("http://172.18.18.20:5000/data")
      .then(res => res.json())
      .then(data => {
        const temperature = data.temperature; // Adjust this key if needed
        const cpu_usage = data.cpu_usage; // Adjust this key if needed

        const maxTemp = 100; // Max expected temp
        const angle = Math.min(180, (temperature / maxTemp) * 180);

        document.querySelector(".semi-circle--mask").style.transform = `rotate(${angle}deg)`;
        temperatureGauge.innerText = `Temp ${temperature}°C`; // Update the gauge text
        
        document.querySelector(".semi-circle--mask").style.transform = `rotate(${angle}deg)`;
        cpu_usageGuage.innerText = `CPU Usage ${cpu_usage}%`; // Update the gauge text
        // Optional: display value in the center or console
        console.log("Temperature:", temperature + "°C");
      })
      .catch(err => {
        console.error("Failed to fetch temperature:", err);
      });
  }

  // Update every 2 seconds
  setInterval(updateGauge, 2000);