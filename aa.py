import json
import matplotlib.pyplot as plt
from datetime import datetime

# Load your JSON data (assuming it's stored in `data.json`)
with open("data.json") as f:
    json_data = json.load(f)

timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in json_data["data"]["timestamp"]]
cpu_usage = json_data["data"]["cpu_usage"]

plt.figure(figsize=(10, 5))
plt.plot(timestamps, cpu_usage, marker='o', color='red')
plt.title("CPU Usage Over Time")
plt.xlabel("Timestamp")
plt.ylabel("CPU Usage (%)")
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
