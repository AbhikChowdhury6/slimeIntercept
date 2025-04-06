from scapy.all import sniff, UDP, IP
import datetime

TARGET_IP = "192.168.1.96"
TARGET_PORT = 6969
LOG_FILE = "imu_raw_sniffed.txt"

def handle_packet(packet):
    if IP in packet and UDP in packet:
        src_ip = packet[IP].src
        dst_port = packet[UDP].dport
        if src_ip == TARGET_IP and dst_port == TARGET_PORT:
            timestamp = datetime.datetime.utcnow().isoformat()
            payload = bytes(packet[UDP].payload)
            hex_data = payload.hex()
            with open(LOG_FILE, "a") as f:
                f.write(f"{timestamp} - {hex_data}\n")
            print(f"{timestamp} - {hex_data}")

print(f"Sniffing UDP packets from {TARGET_IP}:{TARGET_PORT}...")
sniff(filter=f"udp and port {TARGET_PORT}", prn=handle_packet, store=0)
