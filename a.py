import requests
from scapy.all import sniff, IP, ARP, TCP, UDP, ICMP
from datetime import datetime
import socket
import json
import os
import pandas as pd

API_KEY = "ca54b980f7f6483f8e88a3f35e8ff752"
ip_cache = {}
packets_folder = "packets"
excel_file = "packet_database.xlsx"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
json_file = os.path.join(packets_folder, f"{timestamp}_packets.json")
packets_file = "packets.json"

# Ensure packets directory exists
os.makedirs(packets_folder, exist_ok=True)

with open(packets_file, "w") as f:
    json.dump([], f)

def get_ip_location(ip):
    if ip in ip_cache:
        return ip_cache[ip]
    try:
        response = requests.get(f"https://ipgeolocation.abstractapi.com/v1/?api_key={API_KEY}&ip_address={ip}", timeout=2)
        data = response.json()
        city = data.get('timezone', {}).get('name', 'Unknown')
        country = data.get('country', 'Unknown')
        asn = data.get('connection', {}).get('autonomous_system_number', 'Unknown')
        isp = data.get('connection', {}).get('autonomous_system_organization', 'Unknown')
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except Exception:
            hostname = "No PTR"
        info = {
            "location": f"{city}, {country}",
            "asn": asn,
            "isp": isp,
            "hostname": hostname
        }
        ip_cache[ip] = info
        return info
    except Exception:
        return {"location": "Unknown", "asn": "Unknown", "isp": "Unknown", "hostname": "Unknown"}

def identify_protocol(port, layer_name):
    common_ports = {
        5001: "iperf3",
        5000: "HTTP (Flask)",
        80: "HTTP",
        443: "HTTPS",
        53: "DNS",
        123: "NTP"
    }
    return common_ports.get(port, layer_name)

def save_packet_to_json(packet_data):
    new_file = not os.path.exists(json_file)
    if new_file:
        with open(json_file, "w") as f:
            json.dump([packet_data], f, indent=2)
        print(f"[✔] Created new JSON log: {json_file}")
    else:
        with open(json_file, "r+") as f:
            data = json.load(f)
            data.append(packet_data)
            f.seek(0)
            json.dump(data, f, indent=2)
        print(f"[+] Appended packet to existing file: {json_file}")

    # Apply chmod 666
    chmod_packets_folder()

    # Update Excel only on first creation
    if new_file:
        update_excel_database()

def chmod_packets_folder():
    for file in os.listdir(packets_folder):
        filepath = os.path.join(packets_folder, file)
        if os.path.isfile(filepath) and file.endswith(".json"):
            try:
                os.chmod(filepath, 0o666)
                print(f"[~] Applied chmod 666 to: {filepath}")
            except Exception as e:
                print(f"[!] Could not chmod {filepath}: {e}")


def update_excel_database():
    try:
        new_entry = {
            "Timestamp": timestamp,
            "JSON Filename": os.path.basename(json_file),
            "Full Path": os.path.abspath(json_file)
        }

        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            df = df.append(new_entry, ignore_index=True)
        else:
            df = pd.DataFrame([new_entry])

        df.to_excel(excel_file, index=False)
        print(f"[✔] Excel database updated: {new_entry['JSON Filename']}")
    except Exception as e:
        print("Error updating Excel:", e)


def packet_callback(packet):
    proto = "UNKNOWN"
    src = dst = sport = dport = "-"
    pkt_time = datetime.fromtimestamp(packet.time)
    timestamp_str = pkt_time.strftime('%Y-%m-%d %H:%M:%S')

    if packet.haslayer(IP):
        src = packet[IP].src
        dst = packet[IP].dst
        src_info = get_ip_location(src)
        dst_info = get_ip_location(dst)

        if packet.haslayer(TCP):
            sport = packet[TCP].sport
            dport = packet[TCP].dport
            proto = identify_protocol(dport, "TCP")
        elif packet.haslayer(UDP):
            sport = packet[UDP].sport
            dport = packet[UDP].dport
            proto = identify_protocol(dport, "UDP")
        elif packet.haslayer(ICMP):
            proto = "ICMP"
        else:
            proto = packet.lastlayer().name

        log = {
            "timestamp": timestamp_str,
            "src_ip": src,
            "src_hostname": src_info['hostname'],
            "src_location": src_info['location'],
            "src_asn": src_info['asn'],
            "src_isp": src_info['isp'],
            "src_port": sport,
            "dst_ip": dst,
            "dst_hostname": dst_info['hostname'],
            "dst_location": dst_info['location'],
            "dst_asn": dst_info['asn'],
            "dst_isp": dst_info['isp'],
            "dst_port": dport,
            "protocol": proto
        }

        print(f"[{timestamp_str}] {src}:{sport} -> {dst}:{dport} | {proto}")
        # Load existing packets, append, then save
        try:
            with open(packets_file, "r") as f:
                packets = json.load(f)
        except Exception:
            packets = []

        packets.append(log)

        with open(packets_file, "w") as f:
            json.dump(packets, f, indent=4)

        save_packet_to_json(log)

    elif packet.haslayer(ARP):
        src = packet[ARP].psrc
        dst = packet[ARP].pdst
        proto = "ARP"
        log = {
            "timestamp": timestamp_str,
            "src_ip": src,
            "dst_ip": dst,
            "protocol": proto
        }
        print(f"[{timestamp_str}] {src} -> {dst} | Protocol: {proto}")
        save_packet_to_json(log)

# Start sniffing
print("Sniffing packets on eth0... Press Ctrl+C to stop.\n")
sniff(prn=packet_callback, store=False, iface="eth0")

