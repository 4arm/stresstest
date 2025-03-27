import tkinter as tk
from tkinter import ttk
import subprocess
import os
import signal
import threading
import time
import psutil
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Global variables
stress_process = None
running = False
metrics_running = True
remaining_time = 0
data_log = []
canvas = None

def run_stress_ng():
    """Runs the stress-ng command and logs data."""
    global stress_process, running, remaining_time, data_log

    timeout = timeout_entry.get()
    if not timeout.isdigit() or int(timeout) <= 0:
        status_label.config(text="Invalid timeout! Enter a number.", fg="red")
        return

    timeout = int(timeout)
    if stress_process is None:
        command = ["stress-ng", "--cpu", "4", "--timeout", f"{timeout}s", "--metrics-brief"]
        stress_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        remaining_time = timeout
        running = True
        data_log = []
        status_label.config(text=f"Stress Test Running ({timeout}s)...", fg="green")

        threading.Thread(target=countdown_timer, daemon=True).start()
        threading.Thread(target=monitor_test_completion, args=(stress_process,), daemon=True).start()
        threading.Thread(target=log_metrics, daemon=True).start()

def stop_stress_ng():
    """Stops the running stress-ng process."""
    global stress_process, running, remaining_time
    if stress_process:
        os.kill(stress_process.pid, signal.SIGTERM)
        stress_process = None
        status_label.config(text="Stress Test Stopped", fg="red")
    running = False
    remaining_time = 0
    timer_label.config(text="Timer: --")

def monitor_test_completion(process):
    """Waits for the test to complete, updates status, and saves data."""
    process.wait()
    global stress_process, running, remaining_time
    stress_process = None
    running = False
    remaining_time = 0
    status_label.config(text="Test Finished!", fg="blue")
    timer_label.config(text="Timer: 0s")

    # Save Data and Show Graph
    save_to_excel()
    plot_graph_in_gui()

def exit_app():
    """Stops monitoring and exits."""
    global metrics_running
    stop_stress_ng()
    metrics_running = False
    root.destroy()

def countdown_timer():
    """Handles test countdown."""
    global remaining_time
    while running and remaining_time > 0:
        timer_label.config(text=f"Timer: {remaining_time}s")
        time.sleep(1)
        remaining_time -= 1
    if remaining_time == 0 and running:
        stop_stress_ng()

def get_temperature():
    """Fetches temperature."""
    try:
        output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
        return float(output.replace("temp=", "").replace("'C", "").strip())
    except:
        return None

def get_voltage():
    """Fetches core voltage."""
    try:
        output = subprocess.check_output(["vcgencmd", "measure_volts"]).decode("utf-8")
        return float(output.replace("volt=", "").replace("V", "").strip())
    except:
        return None

def get_memory():
    """Fetches ARM and GPU memory."""
    try:
        gpu_mem = subprocess.check_output(["vcgencmd", "get_mem", "gpu"]).decode("utf-8").strip().replace("gpu=", "")
        arm_mem = subprocess.check_output(["vcgencmd", "get_mem", "arm"]).decode("utf-8").strip().replace("arm=", "")
        return int(arm_mem.replace("M", "")), int(gpu_mem.replace("M", ""))
    except:
        return None, None

def get_cpu_usage():
    """Fetches CPU usage."""
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    """Fetches RAM usage in percentage."""
    return psutil.virtual_memory().percent

def update_metrics():
    """Continuously updates system metrics labels."""
    while metrics_running:
        temp_label.config(text=f"Temperature: {get_temperature()}°C")
        volts_label.config(text=f"Voltage: {get_voltage()}V")
        arm_mem, gpu_mem = get_memory()
        mem_label.config(text=f"Memory: ARM {arm_mem}MB | GPU {gpu_mem}MB")
        cpu_label.config(text=f"CPU Usage: {get_cpu_usage()}%")
        ram_label.config(text=f"RAM Usage: {get_ram_usage()}%")

def log_metrics():
    """Logs system metrics every second during test."""
    global data_log
    while running:
        temp = get_temperature()
        volts = get_voltage()
        arm_mem, gpu_mem = get_memory()
        cpu = get_cpu_usage()
        ram = get_ram_usage()

        if temp is not None and volts is not None and cpu is not None:
            timestamp = time.strftime("%H:%M:%S")
            data_log.append([timestamp, temp, volts, arm_mem, gpu_mem, cpu, ram])

        time.sleep(1)

def save_to_excel():
    """Saves recorded data to an Excel file."""
    if data_log:
        df = pd.DataFrame(data_log, columns=["Time", "Temperature (°C)", "Voltage (V)", "ARM Memory (MB)", "GPU Memory (MB)", "CPU Usage (%)", "RAM Usage (%)"])
        df.to_excel("stress_test_data.xlsx", index=False)
        status_label.config(text="Data saved to stress_test_data.xlsx", fg="green")

def plot_graph_in_gui():
    """Plots and embeds the graph inside Tkinter."""
    global canvas
    if data_log:
        df = pd.DataFrame(data_log, columns=["Time", "Temperature (°C)", "Voltage (V)", "ARM Memory (MB)", "GPU Memory (MB)", "CPU Usage (%)", "RAM Usage (%)"])

        fig, ax1 = plt.subplots(figsize=(6, 3))

        ax1.plot(df["Time"], df["Temperature (°C)"], label="Temperature (°C)", color="red")
        ax1.plot(df["Time"], df["Voltage (V)"], label="Voltage (V)", color="blue")
        ax1.plot(df["Time"], df["CPU Usage (%)"], label="CPU Usage (%)", color="green")
        ax1.plot(df["Time"], df["RAM Usage (%)"], label="RAM Usage (%)", color="purple")

        ax1.set_xlabel("Time")
        ax1.set_ylabel("Value")
        ax1.legend()
        ax1.set_xticks(df["Time"][::max(1, len(df) // 10)])  # Reduce tick labels for readability
        ax1.set_xticklabels(df["Time"][::max(1, len(df) // 10)], rotation=45)

        if canvas:
            canvas.get_tk_widget().destroy()  # Clear previous graph

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack()
        canvas.draw()

# Create GUI
root = tk.Tk()
root.title("Stress Test on Raspberry Pi")
root.geometry("600x650")

# Status Label
status_label = tk.Label(root, text="Idle", font=("Arial", 12))
status_label.pack(pady=10)

# Timeout Entry
timeout_frame = tk.Frame(root)
timeout_frame.pack(pady=5)

tk.Label(timeout_frame, text="Timeout (seconds):", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
timeout_entry = tk.Entry(timeout_frame, font=("Arial", 12), width=5)
timeout_entry.pack(side=tk.LEFT)
timeout_entry.insert(0, "300")

# Timer Label
timer_label = tk.Label(root, text="Timer: --", font=("Arial", 12))
timer_label.pack(pady=5)

# System Metrics Labels
temp_label = tk.Label(root, text="Temperature: --", font=("Arial", 12))
temp_label.pack()

volts_label = tk.Label(root, text="Voltage: --", font=("Arial", 12))
volts_label.pack()

mem_label = tk.Label(root, text="Memory: --", font=("Arial", 12))
mem_label.pack()

cpu_label = tk.Label(root, text="CPU Usage: --", font=("Arial", 12))
cpu_label.pack()

ram_label = tk.Label(root, text="RAM Usage: --", font=("Arial", 12))
ram_label.pack()

# Buttons
tk.Button(root, text="Start Test", command=run_stress_ng, font=("Arial", 12), fg="white", bg="green").pack(pady=5)
tk.Button(root, text="Stop Test", command=stop_stress_ng, font=("Arial", 12), fg="white", bg="red").pack(pady=5)
tk.Button(root, text="Exit", command=exit_app, font=("Arial", 12), fg="white", bg="black").pack(pady=5)

# Graph Frame
graph_frame = ttk.LabelFrame(root, text="Graph")
graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Start system monitoring
threading.Thread(target=update_metrics, daemon=True).start()

root.mainloop()
