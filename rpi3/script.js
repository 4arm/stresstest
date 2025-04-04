// Define threshold values for alerts
const bandwidthThreshold = 950; // Mbps
const rttThreshold = 2; // ms
const cpuUsageThreshold = 90; // %

let previousResults = [];

// Function to update gauges
function updateGauge(gaugeType, value) {
    let gaugeData = {
        bandwidth: {
            max: 1000, // Mbps
            current: value,
            color: value > bandwidthThreshold ? 'red' : 'green'
        },
        rtt: {
            max: 5, // ms
            current: value,
            color: value > rttThreshold ? 'red' : 'green'
        },
        cpuUsage: {
            max: 100, // %
            current: value,
            color: value > cpuUsageThreshold ? 'red' : 'green'
        }
    };

    const gauge = gaugeData[gaugeType];
    const canvas = document.getElementById(`${gaugeType}Canvas`);
    const ctx = canvas.getContext('2d');
    const radius = canvas.width / 2;
    const startAngle = Math.PI * 1;
    const endAngle = Math.PI * (1 + 2 * (gauge.current / gauge.max));

    // Draw the gauge background
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.arc(radius, radius, radius - 10, 0, Math.PI * 2);
    ctx.fillStyle = '#e0e0e0';
    ctx.fill();

    // Draw the gauge fill
    ctx.beginPath();
    ctx.arc(radius, radius, radius - 10, startAngle, endAngle);
    ctx.lineWidth = 20;
    ctx.strokeStyle = gauge.color;
    ctx.stroke();
}

// Function to display the test summary
function displaySummary(testData) {
    const summaryText = `
        Protocol: TCP<br>
        Duration: ${testData.duration}s<br>
        Average Bandwidth: ${testData.bandwidth} Mbps<br>
        Total Data Sent: ${testData.totalData} GB<br>
        RTT: Min = ${testData.rttMin} ms, Max = ${testData.rttMax} ms, Avg = ${testData.rttAvg} ms<br>
        Retransmissions: ${testData.retransmissions}<br>
        CPU Usage: ${testData.cpuUsage}%
    `;
    document.getElementById('summaryText').innerHTML = summaryText;
}

// Function to compare the current test results with previous ones
function compareTestResults() {
    if (previousResults.length === 0) {
        document.getElementById('comparisonResult').innerText = "No previous test results to compare.";
        return;
    }

    const currentResult = {
        bandwidth: 941.59, // Mbps
        rttAvg: 2.1, // ms
        cpuUsage: 7, // %
    };

    const comparison = previousResults.map(result => {
        return `
            Previous Result - Bandwidth: ${result.bandwidth} Mbps, RTT: ${result.rttAvg} ms, CPU: ${result.cpuUsage} %
        `;
    }).join('<br>');

    document.getElementById('comparisonResult').innerHTML = `
        Current Result - Bandwidth: ${currentResult.bandwidth} Mbps, RTT: ${currentResult.rttAvg} ms, CPU: ${currentResult.cpuUsage} %<br>
        <br>
        Comparison:<br>${comparison}
    `;
    
    // Save current result for future comparison
    previousResults.push(currentResult);
}

// Simulating incoming test data
function simulateTestData() {
    const testData = {
        duration: 10,
        bandwidth: Math.random() * 1000,
        totalData: 1.17,
        rttMin: Math.random() * 2,
        rttMax: Math.random() * 3,
        rttAvg: Math.random() * 2.4 + 1,
        retransmissions: Math.floor(Math.random() * 5),
        cpuUsage: Math.random() * 100
    };

    updateGauge('bandwidth', testData.bandwidth);
    updateGauge('rtt', testData.rttAvg);
    updateGauge('cpuUsage', testData.cpuUsage);

    displaySummary({
        duration: testData.duration,
        bandwidth: testData.bandwidth.toFixed(2),
        totalData: testData.totalData.toFixed(2),
        rttMin: testData.rttMin.toFixed(2),
        rttMax: testData.rttMax.toFixed(2),
        rttAvg: testData.rttAvg.toFixed(2),
        retransmissions: testData.retransmissions,
        cpuUsage: testData.cpuUsage.toFixed(2)
    });
}

async function runTest() {
    document.getElementById("output").innerText = "Running test...";
    try {
        const response = await fetch('http://172.18.18.20:5000/run-test');
        const data = await response.json();
        const parsed = JSON.parse(data.result);
        document.getElementById("output").innerText = JSON.stringify(parsed, null, 2);
    } catch (error) {
        document.getElementById("output").innerText = "Error: " + error;
    }
    }

// Run a simulated test every 10 seconds
setInterval(simulateTestData, 1000);
