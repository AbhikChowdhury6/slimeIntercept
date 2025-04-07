from scapy.all import sniff, UDP, IP
import datetime
import struct

TARGET_IP = "192.168.1.96"
TARGET_PORT = 6969
LOG_FILE = "imu_raw_sniffed.txt"



bp = {
    'always_000000?': ('check_bytes',0,3, '000000'),
    'packet_type': ('check_uint8',3,4, 100),
    'always_all_0?': ('check_bytes',4,8, '00000000'),
    'potential_counter': ('check_uint32',8,12, None),
    'always_0_23_0_0_0?': ('check_bytes',12,17,'0017000000'),
    'quat_packet_sig': ('check_uint8',17,18,17),
    'unknown3_always_0001?': ('check_bytes',18,20, '0001'),
    'quat_w': ('check_f32',20,24, None),
    'quat_x': ('check_f32',24,28, None),
    'quat_y': ('check_f32',28,32, None),
    'quat_z': ('check_f32',32,36, None),
    'always_3_0_17_0_0_0?': ('check_bytes',36,42,'030011000000'),
    'accel_packet_sig': ('check_uint8',42,43,4),
    'accel_x': ('check_f32',43,47, None),
    'accel_y': ('check_f32',47,51, None),
    'accel_z': ('check_f32',51,55, None),
}


def check_bytes(bytes, expected_val):
    hex_val = bytes
    isExp = hex_val == expected_val
    if isExp:
        return str(isExp)
    else:
        return str(isExp) + ": " + hex_val


def check_uint8(byte, expected_val):
    val = struct.unpack('>I',b'\x00\x00\x00' + byte)[0]
    isExp = val == expected_val
    if isExp:
        return str(isExp)
    else:
        return str(isExp) + ": " + f"{val:03d}"

def check_uint32(bytes, expected_val):
    val = struct.unpack('>I',bytes)[0]
    isExp = val == expected_val
    if isExp:
        return str(isExp)
    else:
        return str(isExp) + ": " + f"{val:08d}"

def check_f32(bytes, expected_val):
    val = struct.unpack('>f',bytes)[0]
    isExp = val == expected_val
    if isExp:
        return str(isExp)
    else:
        return str(isExp) + ": " + f"{val:08.3f}"

def parse_packet(payload):
    if len(payload) < 4:
        return "Payload too short"

    # Unpack first 4 bytes as little-endian unsigned int
    packet_id = struct.unpack(">I", payload[:4])[0]
    if packet_id == 100:
        fstrings = []

        for k in bp:
            fstrings.append(k + ":")
            func = globals()[bp[k][0]]
            fstrings.append(func(t[bp[k][1]:bp[k][2]], bp[k][3]))
        
    return " ".join(fstrings)

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
            #print(f"{timestamp} - {hex_data}")
            print(parse_packet(payload))
            print()

print(f"Sniffing UDP packets from {TARGET_IP}:{TARGET_PORT}...")
sniff(filter=f"udp and port {TARGET_PORT}", prn=handle_packet, store=0)
