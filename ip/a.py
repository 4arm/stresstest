import requests
from scapy.all import sniff, IP, ARP, TCP, UDP, ICMP
from datetime import datetime

API_KEY = "ca54b980f7f6483f8e88a3f35e8ff752"
ip_cache = {}

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

        info = {
            "location": f"{city}, {country}",
            "asn": asn,
            "isp": isp
        }
        ip_cache[ip] = info
        return info
    except Exception as e:
        return {"location": "Unknown", "asn": "Unknown", "isp": "Unknown"}

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
            if sport == 5000 or dport == 5000:
                proto = "HTTP (Flask)"
            elif sport == 443 or dport == 443:
                proto = "HTTPS"
            elif sport == 80 or dport == 80:
                proto = "HTTP"
            else:
                proto = "TCP"

        elif packet.haslayer(UDP):
            sport = packet[UDP].sport
            dport = packet[UDP].dport
            proto = "UDP"

        elif packet.haslayer(ICMP):
            proto = "ICMP"
        else:
            proto = packet.lastlayer().name

        print(f"[{timestamp}] {src} ({src_info['location']}) [ASN: {src_info['asn']}, ISP: {src_info['isp']}]"
              f" :{sport} -> {dst} ({dst_info['location']}) [ASN: {dst_info['asn']}, ISP: {dst_info['isp']}]"
              f" :{dport} | Protocol: {proto}")

    elif packet.haslayer(ARP):
        src = packet[ARP].psrc
        dst = packet[ARP].pdst
        proto = "ARP"
        print(f"[{timestamp}] {src} -> {dst} | Protocol: {proto}")

# Start sniffing
print("Sniffing packets on eth0... Press Ctrl+C to stop.\n")
sniff(prn=packet_callback, store=False, iface="eth0")