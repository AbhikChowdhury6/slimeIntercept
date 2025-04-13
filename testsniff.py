from datetime import datetime
from zoneinfo import ZoneInfo
import struct
import csv

from scapy.all import sniff, UDP, IP

TARGET_PORT = 6969


instance_name = 'testpi'

bno085_sd = {
    "abno085": {
        'class_name':'aBNO085',
        'responsiblePartyName': 'abhik',
        'instanceName': instance_name,
        'manufacturer': 'slimevr-CEVA',
        'deviceName': "slime-bno085",
        'sensors': {
            'linaccel-ms2': {
                'hz': 2**8,
                'col_names': ['sampleDT!int64!datetime64[ns]!audelayhz8',
                              'linaccelx-ms2!float32!float32!afloat10',
                              'linaccely-ms2!float32!float32!afloat10',
                              'linaccelz-ms2!float32!float32!afloat10']
            },
            'quat': {
                'hz': 2**8,
                'col_names': ['sampleDT!int64!datetime64[ns]!audelayhz8', 
                              'quatw!float32!float32!aboundedfloat11',
                              'quatx!float32!float32!aboundedfloat11',
                              'quaty!float32!float32!aboundedfloat11',
                              'quatz!float32!float32!aboundedfloat11']
            }
        }
    }
}

IPS = {'192.168.1.10': (0,'right-upper-arm'), '192.168.1.19': (1,'left-upper-arm')}

sensor_descriptors = {}
base_sds = bno085_sd['sensors']
for ip in IPS:
    for sd in base_sds:
        #change the name
        new_data_type = IPS[ip][1] + '-' + sd
        #also change the col_names
        new_col_names = []
        for cn in base_sds[sd]['col_names']:
            if cn.split('!')[0] == 'sampleDT':
                new_col_names.append(cn)
            new_col_names.append(IPS[ip][1] + '-' + cn)
        
        sensor_descriptors[new_data_type] = base_sds[sd]
        sensor_descriptors[new_data_type]['col_names'] = new_col_names
        #add a new field for this sensor
        sensor_descriptors[new_data_type]['buff_idx'] = IPS[ip][0]




def get_f32(bytes):
    return struct.unpack('>f',bytes)[0]

def get_uint8(byte):
    return struct.unpack('>I',b'\x00\x00\x00' + byte)[0]

sec_buffs = [[],[]]

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
    print(f"got packet at: {ts} from {src_ip}")

    quatw = get_f32(payload[20:24])
    quatx = get_f32(payload[24:28])
    quaty = get_f32(payload[28:32])
    quatz = get_f32(payload[32:36])
    quat_buffer[buff_idx] = [quatw, quatx, quaty, quatz]

    accelx = get_f32(payload[43:47])
    accely = get_f32(payload[47:51])
    accelz = get_f32(payload[51:55])
    accel_buffer[buff_idx] = [accelx, accely, accelz]

    # write it to a csv
    day_folder = repoPath + 'dayData/'
    if not os.path.exists(day_folder):
        os.mkdir(day_folder)

    hour_file_name = day_folder + "_".join(deviceDescriptor) + "_" +\
                    newTimestamps[0].strftime('%Y-%m-%dT%H%z') + '.csv'

    is_new_file = not os.path.exists(hour_file_name)
    
    # other popular types float64, int64, float32, int32
    with open(hour_file_name, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new_file:  # Write headers only if file is new
            # print('writing cols!')
            print('new file! ' + hour_file_name)
            sys.stdout.flush()
            writer.writerow(colNames)
        
        for i, data in enumerate(ctsb.data_buffers[lastBuffNum][:ctsb.lengths[lastBuffNum][0]]):
            writer.writerow([newTimestamps[i].strftime('%Y-%m-%dT%H:%M:%S.%f%z')] + data.tolist())



sniff(filter=f"udp and port {TARGET_PORT}", prn=handle_packet, store=0)




