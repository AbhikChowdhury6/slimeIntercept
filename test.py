import socket
import datetime

# Config
TARGET_IP = "192.168.1.96"
UDP_PORT = 6969
LOG_FILE = "imu_raw_log.txt"

# Setup UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', UDP_PORT))  # Listen on all interfaces

print(f"Listening for IMU data from {TARGET_IP}:{UDP_PORT}...")

with open(LOG_FILE, "a") as f:
    while True:
        data, addr = sock.recvfrom(1024)
        if addr[0] == TARGET_IP:
            timestamp = datetime.datetime.utcnow().isoformat()
            hex_data = data.hex()
            f.write(f"{timestamp} - {hex_data}\n")
            print(f"{timestamp} - {hex_data}")
