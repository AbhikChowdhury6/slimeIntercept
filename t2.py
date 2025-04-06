from scapy.all import sniff, UDP, IP
import datetime
import struct

TARGET_IP = "192.168.1.96"
TARGET_PORT = 6969
LOG_FILE = "imu_raw_sniffed.txt"

from collections import namedtuple

Accel = namedtuple("Accel", "sensor_id x y z")

def parse_packet4(data: bytes):
    if len(data) < 13:
        raise ValueError("Accel packet too short")
    x, y, z = struct.unpack(">fff", data[0:12])  # Big endian floats
    sensor_id = data[12]
    return Accel(sensor_id, x, y, z)

Rotation = namedtuple("Rotation", "sensor_id data_type x y z w accuracy")

def parse_packet17(data: bytes):
    if len(data) < 18:
        raise ValueError("RotationDataPacket too short")
    sensor_id = data[0]
    data_type = data[1]
    x, y, z, w = struct.unpack(">ffff", data[2:18 - 1])  # 4 big-endian floats
    accuracy = data[17]
    return Rotation(sensor_id, data_type, x, y, z, w, accuracy)

packet_parsers = {
    4: parse_packet4,
    17: parse_packet17,
    # Add more here...
}

def parse_packet(payload):
    if len(payload) == 0:
        return "Empty packet"
    
    packet_id = payload[0]
    return f"Packet ID: 0x{packet_id:02X} ({packet_id}) | Length: {len(payload)}"

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
            print(f"Packet type: {payload[0]} (int), 0x{payload[0]:02X} (hex)")
            print(parse_packet(payload))
            print()

print(f"Sniffing UDP packets from {TARGET_IP}:{TARGET_PORT}...")
sniff(filter=f"udp and port {TARGET_PORT}", prn=handle_packet, store=0)
