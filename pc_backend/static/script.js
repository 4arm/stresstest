document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('test-form');
    const result = document.getElementById('result');
  
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
  
      const source = document.getElementById('source-device').value;
      const target = document.getElementById('target-device').value;
      const duration = document.getElementById('duration').value;
  
      if (source === target) {
        result.textContent = "Source and Target must be different!";
        return;
      }
  
      result.textContent = "Running test...";
  
      try {
        const response = await fetch('/start-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_device: source,
            target_device: target,
            duration: parseInt(duration)
          })
        });
  
        const data = await response.json();
        if (data.status === "success") {
          result.textContent = JSON.stringify(data.result, null, 2);
          console.log(data.result);
        } else {
          result.textContent = "Error: " + (data.message || data.error);
        }
      } catch (error) {
        result.textContent = "Failed to start test: " + error;
      }
    });
  });
  