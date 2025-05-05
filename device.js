// Helper to parse query params
function getQueryParam(key) {
    const params = new URLSearchParams(window.location.search);
    return params.get(key);
}
  
const targetIp = getQueryParam('ip');
  
fetch('deviceList.json')
    .then(response => response.json())
    .then(devices => {
      const device = devices.find(d => d.ip === targetIp);
      if (!device) {
        document.getElementById('device-detail').innerHTML = `<p>Device not found.</p>`;
        return;
      }
  
      document.getElementById('detail-name').textContent = device.name;
      document.getElementById('detail-ip').textContent = device.ip;
  
      const statusEl = document.getElementById('detail-status');
      statusEl.textContent = device.status;
      statusEl.className = device.status === 'online' ? 'status-online' : 'status-offline';
  
      // You can add more monitoring logic here
    })
    .catch(err => {
      console.error('Failed to load device data:', err);
    });
  