import requests
from scapy.all import sniff, IP, ARP, TCP, UDP, ICMP
from datetime import datetime
import socket
import json
import os
import pandas as pd

API_KEY = "ca54b980f7f6483f8e88a3f35e8ff752"
ip_cache = {}
json_file = "packets.json"

# Initialize log file if it doesn't exist
if not os.path.exists(json_file):
    with open(json_file, "w") as f:
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
    try:
        if not os.path.exists(json_file):
            with open(json_file, "w") as f:
                json.dump([packet_data], f, indent=2)
        else:
            with open(json_file, "r+") as f:
                data = json.load(f)
                data.append(packet_data)
                f.seek(0)
                json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving to JSON:", e)


def packet_callback(packet):
    proto = "UNKNOWN"
    src = dst = sport = dport = "-"
    timestamp = datetime.fromtimestamp(packet.time).strftime('%Y-%m-%d %H:%M:%S')

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
            "timestamp": timestamp,
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

        print(f"[{timestamp}] {src} ({src_info['hostname']}) [{src_info['location']}] ASN:{src_info['asn']} ISP:{src_info['isp']} :{sport} "
              f"-> {dst} ({dst_info['hostname']}) [{dst_info['location']}] ASN:{dst_info['asn']} ISP:{dst_info['isp']} :{dport} | Protocol: {proto}")

        save_packet_to_json(log)

    elif packet.haslayer(ARP):
        src = packet[ARP].psrc
        dst = packet[ARP].pdst
        proto = "ARP"
        log = {
            "timestamp": timestamp,
            "src_ip": src,
            "dst_ip": dst,
            "protocol": proto
        }
        print(f"[{timestamp}] {src} -> {dst} | Protocol: {proto}")
        save_packet_to_json(log)


def update_excel_database():
    record = {
        "Timestamp": timestamp_now,
        "JSON Filename": os.path.basename(json_file),
        "File Path": os.path.abspath(json_file)
    }

    if os.path.exists(excel_db_file):
        df = pd.read_excel(excel_db_file)
        df = df.append(record, ignore_index=True)
    else:
        df = pd.DataFrame([record])

    df.to_excel(excel_db_file, index=False)


timestamp_now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
json_file = f"{timestamp_now}_packets.json"
excel_db_file = "packet_database.xlsx"


# Start sniffing
print("Sniffing packets on eth0... Press Ctrl+C to stop.\n")
sniff(prn=packet_callback, store=False, iface="eth0")
print("\nSniffing completed. Updating Excel database...")
update_excel_database()
print("Excel database updated successfully.")
