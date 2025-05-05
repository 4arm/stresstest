fetch('deviceList.json')
  .then(response => response.json())
  .then(deviceList => {
    const container = document.getElementById('device-container');

    deviceList.forEach(device => {
      const card = document.createElement('div');
      card.className = 'device-card';

      card.innerHTML = `
        <h3>${device.name}</h3>
        <p><strong>IP:</strong> ${device.ip}</p>
        <p><strong>Status:</strong> <span class="status-${device.status}">${device.status}</span></p>
      `;

      card.addEventListener('click', () => {
        // Pass IP or unique identifier in the URL
        window.location.href = `device.html?ip=${encodeURIComponent(device.ip)}`;
      });

      container.appendChild(card);
    });
  })
  .catch(error => {
    console.error("Error loading device list:", error);
  });
