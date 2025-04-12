from datetime import datetime
from zoneinfo import ZoneInfo
import struct

from scapy.all import sniff, UDP, IP

TARGET_PORT = 6969

def get_f32(bytes):
    return struct.unpack('>f',bytes)[0]

def get_uint8(byte):
    return struct.unpack('>I',b'\x00\x00\x00' + byte)[0]

def make_packet_handler(TARGET_IPs, ts_buffer, accel_buffer, quat_buffer):
    def handle_packet(packet):
        if IP not in packet or UDP not in packet:
            return
        
        src_ip = packet[IP].src
        dst_port = packet[UDP].dport
        if src_ip not in TARGET_IPs or dst_port != TARGET_PORT:
            return
        
        payload = bytes(packet[UDP].payload)
        packet_type = get_uint8(payload[3:4])
        if packet_type != 100:
            return
        
        buff_idx = TARGET_IPs[src_ip][0]
        

        ts = datetime.now().astimezone(ZoneInfo("UTC"))
        ts_buffer[buff_idx] = int(ts.timestamp() * 1e9)

        quatw = get_f32(payload[20:24])
        quatx = get_f32(payload[24:28])
        quaty = get_f32(payload[28:32])
        quatz = get_f32(payload[32:36])
        quat_buffer[buff_idx] = [quatw, quatx, quaty, quatz]

        accelx = get_f32(payload[43:47])
        accely = get_f32(payload[47:51])
        accelz = get_f32(payload[51:55])
        accel_buffer[buff_idx] = [accelx, accely, accelz]
    
    return handle_packet


def SNIFFER(IPS, ts_buffer, accel_buffer, quat_buffer, debug_lvl, exit_signal):
    handle_packet = make_packet_handler(IPS, ts_buffer, accel_buffer, quat_buffer)

    sniff(filter=f"udp and port {TARGET_PORT}", 
      prn=handle_packet, 
      store=0,
      stop_filter=lambda pkt: exit_signal[0] == 1)




